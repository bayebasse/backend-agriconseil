from django.conf import settings
from django.db import models
from apps.cultures.models import CultureSuivie
from apps.cultures.models import CultureRef
class Photo(models.Model):
    agriculteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="photos_ia")
    culture_suivie = models.ForeignKey(CultureSuivie, on_delete=models.SET_NULL, null=True, blank=True, related_name="photos")
    image = models.ImageField(upload_to="ia/%Y/%m/")
    date_prise = models.DateTimeField(auto_now_add=True)
class AnalyseIA(models.Model):
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE, related_name="analyse")
    date_analyse = models.DateTimeField(auto_now_add=True)
    probleme = models.CharField(max_length=160, blank=True)
    confiance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    resultat = models.TextField()
    conseil = models.TextField()


class AgronomyDocument(models.Model):
    """A reviewable source document; only approved documents feed the RAG."""

    THEMES = [
        ("general", "Agriculture générale"),
        ("soil", "Sol et préparation"),
        ("planting", "Semis et plantation"),
        ("water", "Eau et irrigation"),
        ("nutrition", "Engrais et fertilisation"),
        ("health", "Maladies et ravageurs"),
        ("harvest", "Récolte"),
        ("storage", "Conservation et stockage"),
        ("yield", "Rendement et production"),
        ("climate", "Climat et risques"),
        ("economics", "Coûts et rentabilité"),
    ]
    REVIEW_STATES = [
        ("draft", "Brouillon"),
        ("pending", "À vérifier"),
        ("approved", "Validé"),
        ("rejected", "Rejeté"),
    ]

    titre = models.CharField(max_length=255)
    organisme = models.CharField(max_length=160)
    url_source = models.URLField(max_length=1000)
    date_document = models.DateField(null=True, blank=True)
    culture = models.ForeignKey(
        CultureRef, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="documents_agronomiques",
    )
    theme = models.CharField(max_length=16, choices=THEMES, default="general", db_index=True)
    zone_geographique = models.CharField(max_length=180, blank=True)
    langue = models.CharField(max_length=12, default="fr")
    contenu = models.TextField(max_length=45_000)
    statut_validation = models.CharField(max_length=12, choices=REVIEW_STATES, default="draft", db_index=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="documents_agronomiques_valides",
    )
    valide_le = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_document", "titre"]

    def clean(self):
        from django.core.exceptions import ValidationError
        from apps.cultures.document_extraction import is_allowed_source_url

        errors = {}
        if not is_allowed_source_url(self.url_source):
            errors["url_source"] = "La source doit être une URL HTTPS officielle (ISRA, DAPSA, FAO ou AfricaRice)."
        if self.statut_validation == "approved" and not (self.valide_par_id and self.valide_le):
            errors["statut_validation"] = "Un document doit être validé par un administrateur avant l'indexation."
        if not self.contenu.strip():
            errors["contenu"] = "Ajoutez le texte source vérifié avant d'enregistrer le document."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.titre} ({self.organisme})"
