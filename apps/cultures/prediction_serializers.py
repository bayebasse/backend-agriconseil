from rest_framework import serializers

from .models import RecolteReelle


class PredictionSerializer(serializers.Serializer):
    culture_suivie_id = serializers.IntegerField()
    culture = serializers.CharField()
    statut = serializers.CharField()
    methode = serializers.CharField()
    superficie = serializers.DecimalField(max_digits=12, decimal_places=2)
    unite_superficie = serializers.CharField(allow_null=True)
    date_semis = serializers.DateField()
    type_cycle = serializers.CharField(allow_null=True)
    caracteristiques_agronomiques = serializers.DictField(allow_null=True)
    rendement_reference = serializers.DictField(allow_null=True)
    stade_actuel = serializers.DictField(allow_null=True)
    recolte_prevue = serializers.DictField()
    rendement_estime_kg_ha = serializers.DecimalField(
        max_digits=12, decimal_places=3, allow_null=True
    )
    quantite_totale_estimee_kg = serializers.DecimalField(
        max_digits=14, decimal_places=3, allow_null=True
    )
    explication_prevision = serializers.CharField(allow_null=True)
    avancement_cycle = serializers.DictField(allow_null=True)
    rendement_reference_kg_ha = serializers.DecimalField(
        max_digits=15, decimal_places=3, allow_null=True
    )
    production_reference_kg = serializers.DecimalField(
        max_digits=24, decimal_places=3, allow_null=True
    )
    meteo = serializers.DictField(allow_null=True)
    risques = serializers.DictField()
    facteurs_favorables = serializers.ListField(child=serializers.DictField())
    facteurs_defavorables = serializers.ListField(child=serializers.DictField())
    recommandations = serializers.ListField(child=serializers.DictField())
    references = serializers.ListField(child=serializers.DictField())
    calcule_le = serializers.DateTimeField()
    limites = serializers.ListField(child=serializers.CharField())
    donnees_manquantes = serializers.ListField(child=serializers.CharField())
    analyse_ia = serializers.DictField()


class RecolteReelleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecolteReelle
        fields = [
            "id",
            "date_recolte",
            "quantite",
            "unite",
            "observations",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_date_recolte(self, value):
        from django.utils import timezone

        if value > timezone.localdate():
            raise serializers.ValidationError(
                "La date de récolte réelle ne peut pas être dans le futur."
            )
        return value

    def validate(self, attrs):
        culture_suivie = self.context.get("culture_suivie")
        date_recolte = attrs.get("date_recolte")
        if culture_suivie and date_recolte and date_recolte < culture_suivie.date_semis:
            raise serializers.ValidationError({
                "date_recolte": "La date de récolte ne peut pas précéder le semis enregistré."
            })
        return attrs

    def create(self, validated_data):
        return RecolteReelle.objects.create(
            culture_suivie=self.context["culture_suivie"],
            **validated_data,
        )
