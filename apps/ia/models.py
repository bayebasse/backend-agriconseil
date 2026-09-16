from django.conf import settings
from django.db import models
from apps.cultures.models import CultureSuivie
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
