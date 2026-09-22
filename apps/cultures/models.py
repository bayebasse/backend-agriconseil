from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models

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
    agriculteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cultures_suivies")
    culture = models.ForeignKey(CultureRef, on_delete=models.PROTECT, related_name="suivis")
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    departement = models.ForeignKey(Departement, on_delete=models.PROTECT)
    commune = models.ForeignKey(CommuneLocalite, on_delete=models.PROTECT)
    superficie = models.DecimalField(max_digits=12, decimal_places=2)
    date_semis = models.DateField()
    type_sol = models.CharField(max_length=30, choices=SOIL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.culture} - {self.agriculteur.username}"
