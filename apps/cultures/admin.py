from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import (
    Region, Departement, CommuneLocalite, CultureRef, CultureSuivie,
    ReferenceRendement, RecolteReelle,
)
from .document_extraction import extract_document

@admin.register(ReferenceRendement)
class ReferenceRendementAdmin(admin.ModelAdmin):
    list_display = ("culture", "variete", "zone_agroecologique", "source_titre", "source_organisme", "statut_validation", "valide")
    list_filter = ("statut_validation", "culture", "systeme_culture")
    search_fields = ("culture__nom", "variete", "source_titre", "source_organisme", "source_url")
    readonly_fields = ("valide", "collectee_le", "document_link", "extraction_preuves", "created_at", "updated_at")
    actions = ("extraire_avec_gemini", "valider_references", "rejeter_references")

    @admin.display(description="Ouvrir le document source")
    def document_link(self, obj):
        if obj.document_fichier:
            return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">Ouvrir le PDF importé</a>', obj.document_fichier.url)
        if obj.source_url:
            return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>', obj.source_url, obj.source_url)
        return "Aucun document enregistré"

    @admin.action(description="Extraire les champs avec Gemini (la référence reste à vérifier)")
    def extraire_avec_gemini(self, request, queryset):
        success = 0
        failed = 0
        for reference in queryset:
            try:
                extract_document(reference)
                success += 1
            except Exception as exc:
                failed += 1
                self.message_user(
                    request,
                    f"{reference}: extraction indisponible ({type(exc).__name__}). Le document reste enregistré.",
                    messages.WARNING,
                )
        if success:
            self.message_user(request, f"{success} document(s) extrait(s), à vérifier avant validation.", messages.SUCCESS)
        if failed and not success:
            self.message_user(request, "Aucun document n'a été extrait. Vérifiez la clé Gemini, le PDF ou le lien ; les références restent enregistrées.", messages.WARNING)

    @admin.action(description="Valider les références sélectionnées")
    def valider_references(self, request, queryset):
        valides = 0
        rejetees = 0
        for reference in queryset:
            reference.statut_validation = "VALIDE"
            reference.valide = True
            try:
                reference.full_clean()
                reference.save()
                valides += 1
            except ValidationError:
                reference.statut_validation = "A_VERIFIER"
                reference.valide = False
                reference.save(update_fields=["statut_validation", "valide", "updated_at"])
                rejetees += 1
        self.message_user(request, f"{valides} référence(s) validée(s); {rejetees} conservée(s) à vérifier (source ou valeurs incomplètes).", messages.WARNING if rejetees else messages.SUCCESS)

    @admin.action(description="Rejeter les références sélectionnées")
    def rejeter_references(self, request, queryset):
        count = queryset.update(statut_validation="REJETE", valide=False)
        self.message_user(request, f"{count} référence(s) rejetée(s).", messages.SUCCESS)


admin.site.register([Region, Departement, CommuneLocalite, CultureRef, CultureSuivie, RecolteReelle])
