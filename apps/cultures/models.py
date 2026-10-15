from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator
from decimal import Decimal

class Region(models.Model):
    nom = models.CharField(max_length=120, unique=True)
    def __str__(self): return self.nom

class Departement(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="departements")
    nom = models.CharField(max_length=120)
    class Meta: unique_together = ("region", "nom")
    def __str__(self): return f"{self.nom} ({self.region})"


class CommuneLocalite(models.Model):
    TYPE_CHOICES = [
        ("commune", "Commune"),
        ("arrondissement_ville", "Commune / Arrondissement / Ville"),
        ("quartier_village_hameau", "Quartier / Village / Hameau"),
    ]

    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        related_name="communes"
    )

    nom = models.CharField(max_length=160)

    type_localite = models.CharField(
    max_length=40,
    choices=TYPE_CHOICES,
)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["departement", "nom", "type_localite"],
                name="unique_localite_par_departement_type"
            )
        ]

    def __str__(self):
        return f"{self.nom} ({self.get_type_localite_display()})"
class CultureRef(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    cycle_jours = models.PositiveIntegerField(default=90)
    besoin_min_mm = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    besoin_max_mm = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    sensibilite_secheresse = models.CharField(max_length=30, default="moyenne")
    actif = models.BooleanField(default=True)
    def __str__(self): return self.nom
class ReferentielAgronomique(models.Model):
    """
    Données agronomiques de référence.
    Elles proviennent de sources externes :
    FAO, ISRA, DAPSA/ANSD, AfricaRice, etc.
    """

    SOURCE_CHOICES = [
        ("FAO", "FAO"),
        ("ISRA", "ISRA"),
        ("ANSD", "ANSD"),
        ("DAPSA", "DAPSA"),
        ("AFRICARICE", "AfricaRice"),
        ("AUTRE", "Autre"),
    ]

    SENSIBILITE_CHOICES = [
        ("", "Non documentée"),
        ("faible", "Faible"),
        ("faible_moyenne", "Faible à moyenne"),
        ("moyenne", "Moyenne"),
        ("moyenne_forte", "Moyenne à forte"),
        ("forte", "Forte"),
    ]

    TYPE_CYCLE_CHOICES = [
        ("annuelle", "Annuelle"),
        ("perenne", "Pérenne"),
    ]

    culture = models.OneToOneField(
        CultureRef,
        on_delete=models.CASCADE,
        related_name="referentiel_agronomique",
    )

    type_cycle = models.CharField(
        max_length=20,
        choices=TYPE_CYCLE_CHOICES,
        default="annuelle",
    )

    cycle_min_jours = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    cycle_max_jours = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    besoin_eau_min_mm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    besoin_eau_max_mm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    sensibilite_secheresse = models.CharField(
        max_length=30,
        choices=SENSIBILITE_CHOICES,
        default="moyenne",
    )

    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
    )

    source_reference = models.CharField(
        max_length=255,
        blank=True,
    )

    source_url = models.URLField(
        blank=True,
    )

    zone_agroecologique = models.CharField(
        max_length=255,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    valide = models.BooleanField(
        default=False,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Référentiel - {self.culture.nom}"    

class CultureSuivie(models.Model):
    SOIL_CHOICES = [("sableux","Sableux"),("argileux","Argileux"),("limoneux","Limoneux"),("sablo-limoneux","Sablo-limoneux")]
    SYSTEME_CHOICES = [("", "Non renseigné"), ("pluvial", "Pluvial"), ("irrigue", "Irrigué"), ("mixte", "Mixte")]
    SUPERFICIE_UNIT_CHOICES = [("ha", "Hectare"), ("m2", "Mètre carré")]
    STATUT_RECOLTE_CHOICES = [
        ("in_progress", "Récolte en cours"),
        ("available", "Disponible"),
        ("harvested", "Récoltée"),
        ("exhausted", "Épuisée"),
        ("unavailable", "Indisponible"),
        ("cancelled", "Annulée"),
    ]
    agriculteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cultures_suivies")
    culture = models.ForeignKey(CultureRef, on_delete=models.PROTECT, related_name="suivis")
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    departement = models.ForeignKey(Departement, on_delete=models.PROTECT)
    commune = models.ForeignKey(CommuneLocalite, on_delete=models.PROTECT)
    superficie = models.DecimalField(max_digits=12, decimal_places=2)
    unite_superficie = models.CharField(max_length=5, choices=SUPERFICIE_UNIT_CHOICES, blank=True, default="")
    variete = models.CharField(max_length=120, blank=True)
    systeme_culture = models.CharField(max_length=12, choices=SYSTEME_CHOICES, blank=True, default="")
    age_arbres_annees = models.PositiveSmallIntegerField(null=True, blank=True)
    quantite_disponible_vente = models.DecimalField(
        max_digits=14, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    unite_disponible_vente = models.CharField(
        max_length=10, choices=[("kg", "Kilogramme"), ("tonne", "Tonne")],
        blank=True, default="",
    )
    statut_recolte = models.CharField(
        max_length=16, choices=STATUT_RECOLTE_CHOICES, default="in_progress",
        db_index=True,
    )
    prix_kg_fcfa = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    date_semis = models.DateField()
    type_sol = models.CharField(max_length=30, choices=SOIL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.culture} - {self.agriculteur.username}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.quantite_disponible_vente is not None and not self.unite_disponible_vente:
            raise ValidationError({"unite_disponible_vente": "Renseignez l'unité de la quantité disponible."})
        if self.quantite_disponible_vente is None and self.unite_disponible_vente:
            raise ValidationError({"quantite_disponible_vente": "Renseignez une quantité ou effacez l'unité."})


class ReferenceRendement(models.Model):
    """Sourced crop-specific reference data; imported rows require review."""

    CYCLE_CHOICES = [("annuelle", "Annuelle"), ("perenne", "Pérenne")]
    SYSTEME_CHOICES = [
        ("", "Non précisé"),
        ("pluvial", "Pluvial"),
        ("irrigue", "Irrigué"),
        ("mixte", "Mixte"),
    ]
    CYCLE_UNIT_CHOICES = [("jours", "Jours"), ("mois", "Mois"), ("annees", "Années")]
    YIELD_UNIT_CHOICES = [
        ("kg_ha", "kg/ha"),
        ("tonne_ha", "tonne/ha"),
        ("kg_arbre", "kg/arbre"),
        ("tonne_arbre", "tonne/arbre"),
    ]
    PERIOD_CHOICES = [("campagne", "Par campagne"), ("annee", "Par année")]
    SENSIBILITE_CHOICES = [
        ("faible", "Faible"),
        ("faible_moyenne", "Faible à moyenne"),
        ("moyenne", "Moyenne"),
        ("moyenne_forte", "Moyenne à forte"),
        ("forte", "Forte"),
    ]
    STATUT_CHOICES = [
        ("A_VERIFIER", "À vérifier"),
        ("VALIDE", "Validé"),
        ("REJETE", "Rejeté"),
    ]

    culture = models.ForeignKey(
        CultureRef, on_delete=models.CASCADE, related_name="references_rendement"
    )
    variete = models.CharField(max_length=120, blank=True)
    zone_agroecologique = models.CharField(max_length=160, blank=True)
    systeme_culture = models.CharField(max_length=12, choices=SYSTEME_CHOICES, blank=True, default="")
    type_cycle = models.CharField(max_length=12, choices=CYCLE_CHOICES, blank=True, default="")
    cycle_min = models.PositiveIntegerField(null=True, blank=True)
    cycle_max = models.PositiveIntegerField(null=True, blank=True)
    cycle_unite = models.CharField(max_length=10, choices=CYCLE_UNIT_CHOICES, blank=True, default="")
    age_arbres_min_annees = models.PositiveSmallIntegerField(null=True, blank=True)
    age_arbres_max_annees = models.PositiveSmallIntegerField(null=True, blank=True)
    rendement_min = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    rendement_moyen = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    rendement_max = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    rendement_unite = models.CharField(max_length=12, choices=YIELD_UNIT_CHOICES, blank=True, default="")
    periode_rendement = models.CharField(max_length=12, choices=PERIOD_CHOICES, blank=True, default="")
    besoin_eau_min_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    besoin_eau_max_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    sensibilite_secheresse = models.CharField(max_length=30, choices=SENSIBILITE_CHOICES, blank=True, default="")
    source_titre = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(blank=True)
    document_fichier = models.FileField(
        upload_to="agronomy_documents/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(["pdf"])],
    )
    source_annee = models.PositiveSmallIntegerField(null=True, blank=True)
    source_organisme = models.CharField(max_length=160, blank=True)
    source_page = models.CharField(max_length=80, blank=True)
    conditions_mesure = models.TextField(blank=True)
    extraction_preuves = models.JSONField(default=dict, blank=True)
    statut_validation = models.CharField(
        max_length=12, choices=STATUT_CHOICES, default="A_VERIFIER", db_index=True
    )
    collectee_le = models.DateTimeField(null=True, blank=True)
    valide = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["culture__nom", "variete", "zone_agroecologique", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["culture", "source_url"],
                condition=~models.Q(source_url=""),
                name="unique_reference_url_par_culture",
            ),
            models.CheckConstraint(
                condition=(models.Q(rendement_min__isnull=True) | models.Q(rendement_min__gte=0)),
                name="ref_rendement_min_nonnegatif",
            ),
            models.CheckConstraint(
                condition=(models.Q(rendement_moyen__isnull=True) | models.Q(rendement_moyen__gte=0)),
                name="ref_rendement_moyen_nonnegatif",
            ),
            models.CheckConstraint(
                condition=(models.Q(rendement_max__isnull=True) | models.Q(rendement_max__gte=0)),
                name="ref_rendement_max_nonnegatif",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}
        if self.document_fichier:
            try:
                uploaded = self.document_fichier.file
                uploaded.seek(0)
                signature = uploaded.read(5)
                uploaded.seek(0)
                if signature != b"%PDF-":
                    errors["document_fichier"] = "Le fichier sélectionné n'est pas un PDF valide."
                if getattr(uploaded, "size", 0) > 8 * 1024 * 1024:
                    errors["document_fichier"] = "Le PDF ne peut pas dépasser 8 Mo."
            except (OSError, ValueError):
                errors["document_fichier"] = "Le fichier PDF n'a pas pu être lu."
        if self.statut_validation == "VALIDE" and not self.valide:
            self.valide = True
        elif self.statut_validation != "VALIDE" and self.valide:
            self.statut_validation = "VALIDE"
        if (self.cycle_min is None) != (self.cycle_max is None):
            errors["cycle_max"] = "Les bornes minimale et maximale du cycle doivent être renseignées ensemble."
        elif self.cycle_min is not None and self.cycle_min > self.cycle_max:
            errors["cycle_max"] = "La borne maximale du cycle doit être supérieure ou égale à la borne minimale."
        if self.cycle_min is not None and not self.cycle_unite:
            errors["cycle_unite"] = "L'unité du cycle est obligatoire lorsque sa durée est renseignée."
        if (self.age_arbres_min_annees is None) != (self.age_arbres_max_annees is None):
            errors["age_arbres_max_annees"] = "Les deux bornes d'âge des arbres doivent être renseignées ensemble."
        elif self.age_arbres_min_annees is not None and self.age_arbres_min_annees > self.age_arbres_max_annees:
            errors["age_arbres_max_annees"] = "L'âge maximal doit être supérieur ou égal à l'âge minimal."
        values = [self.rendement_min, self.rendement_moyen, self.rendement_max]
        present_values = [value for value in values if value is not None]
        if present_values and not self.rendement_unite:
            errors["rendement_unite"] = "L'unité du rendement est obligatoire lorsque des valeurs sont renseignées."
        if self.rendement_moyen is not None:
            if self.rendement_min is not None and self.rendement_moyen < self.rendement_min:
                errors["rendement_moyen"] = "La moyenne ne peut pas être inférieure au minimum."
            if self.rendement_max is not None and self.rendement_moyen > self.rendement_max:
                errors["rendement_moyen"] = "La moyenne ne peut pas dépasser le maximum."
        if (self.besoin_eau_min_mm is None) != (self.besoin_eau_max_mm is None):
            errors["besoin_eau_max_mm"] = "Les bornes du besoin en eau doivent être renseignées ensemble."
        elif self.besoin_eau_min_mm is not None and self.besoin_eau_min_mm > self.besoin_eau_max_mm:
            errors["besoin_eau_max_mm"] = "Le maximum du besoin en eau doit être supérieur ou égal au minimum."
        if self.valide and not (self.source_titre.strip() or self.source_url.strip()):
            errors["source_titre"] = "Une référence validée doit avoir une source identifiable."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Keep the legacy flag in sync for existing callers and imported rows.
        if self.statut_validation == "VALIDE" or self.valide:
            self.statut_validation = "VALIDE"
            self.valide = True
        else:
            self.valide = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Référence de rendement - {self.culture.nom} - {self.source_titre or 'source non renseignée'}"


class RecolteReelle(models.Model):
    """Harvest reported by the farmer, kept separate from any estimate."""

    UNITE_CHOICES = [
        ("kg", "Kilogramme"),
        ("tonne", "Tonne"),
    ]

    culture_suivie = models.ForeignKey(
        CultureSuivie,
        on_delete=models.CASCADE,
        related_name="recoltes_reelles",
    )
    date_recolte = models.DateField()
    quantite = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unite = models.CharField(max_length=10, choices=UNITE_CHOICES)
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_recolte", "-id"]

    def __str__(self):
        return f"Récolte {self.culture_suivie} - {self.quantite} {self.unite}"
