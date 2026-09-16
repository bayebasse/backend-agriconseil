from rest_framework import serializers
from .models import DonneeMeteo
class MeteoSerializer(serializers.ModelSerializer):
    localisation = serializers.CharField(source="commune.nom", read_only=True)
    latitude = serializers.DecimalField(source="commune.latitude", max_digits=9, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(source="commune.longitude", max_digits=9, decimal_places=6, read_only=True)
    class Meta: model = DonneeMeteo; fields = ["id","date_heure","localisation","latitude","longitude","temperature","humidite","vent_kmh","precipitation_mm","probabilite_pluie","source"]
