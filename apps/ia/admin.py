from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import AgronomyDocument, Photo, AnalyseIA
admin.site.register([Photo, AnalyseIA])


@admin.register(AgronomyDocument)
class AgronomyDocumentAdmin(admin.ModelAdmin):
    list_display = ("titre", "organisme", "culture", "theme", "zone_geographique", "statut_validation", "date_document")
    list_filter = ("statut_validation", "theme", "culture", "organisme")
    search_fields = ("titre", "organisme", "contenu", "zone_geographique")
    readonly_fields = ("valide_par", "valide_le", "created_at", "updated_at")
    actions = ("mark_pending", "approve_documents", "reject_documents")

    def save_model(self, request, obj, form, change):
        if change:
            old = AgronomyDocument.objects.get(pk=obj.pk)
            checked_fields = ("titre", "organisme", "url_source", "date_document", "culture_id", "theme", "zone_geographique", "langue", "contenu")
            if any(getattr(old, field) != getattr(obj, field) for field in checked_fields):
                obj.statut_validation = "pending"
                obj.valide_par = None
                obj.valide_le = None
        obj.full_clean()
        super().save_model(request, obj, form, change)

    @admin.action(description="Marquer les documents à vérifier")
    def mark_pending(self, request, queryset):
        queryset.update(statut_validation="pending", valide_par=None, valide_le=None)

    @admin.action(description="Valider et indexer les documents sélectionnés")
    def approve_documents(self, request, queryset):
        approved, rejected = 0, 0
        for document in queryset:
            document.statut_validation = "approved"
            document.valide_par = request.user
            document.valide_le = timezone.now()
            try:
                document.full_clean()
                document.save()
                approved += 1
            except ValidationError as exc:
                rejected += 1
                self.message_user(request, f"{document.titre}: validation impossible ({exc.messages[0]}).", messages.ERROR)
        if approved:
            self.message_user(request, f"{approved} document(s) validé(s) et indexable(s).", messages.SUCCESS)
        if rejected and not approved:
            self.message_user(request, "Aucun document n'a été validé.", messages.WARNING)

    @admin.action(description="Rejeter les documents sélectionnés")
    def reject_documents(self, request, queryset):
        queryset.update(statut_validation="rejected", valide_par=None, valide_le=None)
