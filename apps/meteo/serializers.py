from rest_framework import serializers


class MeteoSerializer(serializers.Serializer):

    region = serializers.CharField()

    localisation = serializers.CharField()

    latitude = serializers.FloatField()

    longitude = serializers.FloatField()

    temperature = serializers.FloatField()

    humidite = serializers.FloatField()

    vent_kmh = serializers.FloatField()

    precipitation_mm = serializers.FloatField()

    probabilite_pluie = serializers.FloatField()

    precipitation_prevue_mm = serializers.FloatField()

    pluie_prevue = serializers.BooleanField()

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    conseil = serializers.CharField()

    source = serializers.CharField()

    prevision = serializers.DictField(
        required=False,
    )