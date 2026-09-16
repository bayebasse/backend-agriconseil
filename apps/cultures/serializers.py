from rest_framework import serializers
from .models import Region, Departement, CommuneLocalite, CultureRef, CultureSuivie

class RegionSerializer(serializers.ModelSerializer):
    class Meta: model = Region; fields = "__all__"
class DepartementSerializer(serializers.ModelSerializer):
    class Meta: model = Departement; fields = "__all__"
class CommuneSerializer(serializers.ModelSerializer):
    class Meta: model = CommuneLocalite; fields = "__all__"
class CultureRefSerializer(serializers.ModelSerializer):
    class Meta: model = CultureRef; fields = "__all__"
class CultureSuivieSerializer(serializers.ModelSerializer):
    culture_nom = serializers.CharField(source="culture.nom", read_only=True)
    localisation = serializers.CharField(source="commune.nom", read_only=True)
    class Meta:
        model = CultureSuivie
        fields = "__all__"
        read_only_fields = ["agriculteur"]
    def validate(self, attrs):
        if attrs["departement"].region_id != attrs["region"].id:
            raise serializers.ValidationError({"departement": "Le département ne correspond pas à la région."})
        if attrs["commune"].departement_id != attrs["departement"].id:
            raise serializers.ValidationError({"commune": "La commune/localité ne correspond pas au département."})
        return attrs

    def create(self, validated_data):
        return CultureSuivie.objects.create(agriculteur=self.context["request"].user, **validated_data)
