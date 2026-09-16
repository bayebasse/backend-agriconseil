from django.db import models
from apps.cultures.models import CultureRef, CultureSuivie

class Stade(models.Model):
    culture = models.ForeignKey(CultureRef, on_delete=models.CASCADE, related_name="stades")
    nom = models.CharField(max_length=80)
    ordre = models.PositiveIntegerField()
    duree_jours = models.PositiveIntegerField()
    kc = models.DecimalField(max_digits=5, decimal_places=2)
    def __str__(self): return f"{self.culture.nom} - {self.nom}"
    class Meta: ordering = ["culture_id", "ordre"]

class CalendrierAgricole(models.Model):
    culture_suivie = models.OneToOneField(CultureSuivie, on_delete=models.CASCADE, related_name="calendrier")
    date_generation = models.DateTimeField(auto_now=True)
    def __str__(self): return f"Calendrier {self.culture_suivie}"

class OperationAgricole(models.Model):
    calendrier = models.ForeignKey(CalendrierAgricole, on_delete=models.CASCADE, related_name="operations")
    stade = models.ForeignKey(Stade, on_delete=models.PROTECT)
    nom = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=30, default="a_faire")
    def __str__(self): return self.nom
