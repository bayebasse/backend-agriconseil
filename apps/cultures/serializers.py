from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
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
    region_nom = serializers.CharField(source="region.nom", read_only=True)
    class Meta:
        model = CultureSuivie
        fields = "__all__"
        read_only_fields = ["agriculteur"]
    def validate(self, attrs):
        user = self.context["request"].user
        if user.role != "farmer":
            raise PermissionDenied("Seuls les agriculteurs peuvent gérer leurs cultures.")
        quantity = attrs.get("quantite_disponible_vente", getattr(self.instance, "quantite_disponible_vente", None))
        unit = attrs.get("unite_disponible_vente", getattr(self.instance, "unite_disponible_vente", ""))
        status = attrs.get("statut_recolte", getattr(self.instance, "statut_recolte", "in_progress"))
        if (quantity is None) != (not unit):
            raise serializers.ValidationError({
                "unite_disponible_vente": "Renseignez ensemble la quantité disponible et son unité, ou effacez les deux."
            })
        if status == "available" and (quantity is None or quantity <= 0):
            raise serializers.ValidationError({
                "quantite_disponible_vente": "Une récolte disponible doit avoir une quantité de vente supérieure à zéro."
            })
        return self.validate_location(attrs)

    def validate_location(self, attrs):
        if self.instance:
            region = attrs.get("region", self.instance.region)
            departement = attrs.get("departement", self.instance.departement)
            commune = attrs.get("commune", self.instance.commune)
        else:
            region, departement, commune = attrs["region"], attrs["departement"], attrs["commune"]
        if departement.region_id != region.id:
            raise serializers.ValidationError({"departement": "Le département ne correspond pas à la région."})
        if commune.departement_id != departement.id:
            raise serializers.ValidationError({"commune": "La commune/localité ne correspond pas au département."})
        return attrs

    def create(self, validated_data):
        return CultureSuivie.objects.create(agriculteur=self.context["request"].user, **validated_data)
