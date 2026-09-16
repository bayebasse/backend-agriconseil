from rest_framework import serializers
from apps.meteo.serializers import MeteoSerializer
from apps.calendrier.serializers import StadeSerializer
class HydricSerializer(serializers.Serializer):
    meteo = serializers.SerializerMethodField()
    stage = serializers.SerializerMethodField()
    eto = serializers.DecimalField(max_digits=7, decimal_places=2, allow_null=True)
    etc = serializers.DecimalField(max_digits=7, decimal_places=2, allow_null=True)
    deficit = serializers.DecimalField(max_digits=7, decimal_places=2, allow_null=True)
    conseil = serializers.CharField()
    def get_meteo(self, obj): return MeteoSerializer(obj["meteo"]).data if obj.get("meteo") else None
    def get_stage(self, obj): return StadeSerializer(obj["stage"]).data if obj.get("stage") else None
