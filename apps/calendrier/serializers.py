from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
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
    prochaine_operation = serializers.SerializerMethodField()
    fin_prevue = serializers.SerializerMethodField()
    fin_prevue_indicative = serializers.SerializerMethodField()

    def get_stade_actuel(self, obj):
        from .services import current_stage
        stage = current_stage(obj.culture_suivie)
        return StadeSerializer(stage).data if stage else None

    def get_prochaine_operation(self, obj):
        from django.utils import timezone
        operation = obj.operations.filter(
            date_fin__gte=timezone.localdate()
        ).order_by("date_debut", "id").first()
        return OperationSerializer(operation).data if operation else None

    def get_fin_prevue(self, obj):
        try:
            reference = obj.culture_suivie.culture.referentiel_agronomique
        except ObjectDoesNotExist:
            return None
        if not reference.cycle_max_jours:
            return None
        from datetime import timedelta
        return obj.culture_suivie.date_semis + timedelta(
            days=reference.cycle_max_jours - 1
        )

    def get_fin_prevue_indicative(self, obj):
        try:
            return not obj.culture_suivie.culture.referentiel_agronomique.valide
        except ObjectDoesNotExist:
            return False

    class Meta:
        model = CalendrierAgricole
        fields = [
            "id", "culture", "date_generation", "operations",
            "stade_actuel", "prochaine_operation", "fin_prevue",
            "fin_prevue_indicative",
        ]
