from django.db import models
from apps.cultures.models import CommuneLocalite, CultureSuivie
class DonneeMeteo(models.Model):
    commune = models.ForeignKey(CommuneLocalite, on_delete=models.CASCADE, related_name="meteo")
    date_heure = models.DateTimeField()
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidite = models.DecimalField(max_digits=5, decimal_places=2)
    vent_kmh = models.DecimalField(max_digits=6, decimal_places=2)
    precipitation_mm = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    probabilite_pluie = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    source = models.CharField(max_length=60, default="demo")
class ConsultationMeteo(models.Model):
    culture_suivie = models.ForeignKey(CultureSuivie, on_delete=models.CASCADE, related_name="consultations_meteo")
    donnee = models.ForeignKey(DonneeMeteo, on_delete=models.CASCADE)
    creee_le = models.DateTimeField(auto_now_add=True)
