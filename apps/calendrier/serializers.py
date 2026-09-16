from rest_framework import serializers
from .models import Stade, CalendrierAgricole, OperationAgricole
class StadeSerializer(serializers.ModelSerializer):
    class Meta: model = Stade; fields = "__all__"
class OperationSerializer(serializers.ModelSerializer):
    stade_nom = serializers.CharField(source="stade.nom", read_only=True)
    class Meta: model = OperationAgricole; fields = "__all__"
class CalendrierSerializer(serializers.ModelSerializer):
    operations = OperationSerializer(many=True, read_only=True)
    culture = serializers.CharField(source="culture_suivie.culture.nom", read_only=True)
    stade_actuel = serializers.SerializerMethodField()
    def get_stade_actuel(self, obj):
        from .services import current_stage
        stage = current_stage(obj.culture_suivie)
        return StadeSerializer(stage).data if stage else None
    class Meta: model = CalendrierAgricole; fields = ["id","culture","date_generation","operations","stade_actuel"]
