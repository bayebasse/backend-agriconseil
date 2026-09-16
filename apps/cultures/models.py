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
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name="communes")
    nom = models.CharField(max_length=160)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    class Meta: unique_together = ("departement", "nom")
    def __str__(self): return self.nom

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
