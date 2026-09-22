from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from apps.cultures.models import (
    CommuneLocalite,
    CultureRef,
    CultureSuivie,
    Departement,
    Region,
)


User = get_user_model()


OFFICIAL_CULTURE_CODES = {
    "riz",
    "mil",
    "mais",
    "sorgho",
    "arachide",
    "niebe",
    "manioc",
    "oignon",
    "mangue",
    "pasteque",
}


class AdminCultureSummarySerializer(serializers.ModelSerializer):
    culture_nom = serializers.CharField(
        source="culture.nom",
        read_only=True,
    )

    region_nom = serializers.CharField(
        source="region.nom",
        read_only=True,
    )

    departement_nom = serializers.CharField(
        source="departement.nom",
        read_only=True,
    )

    commune_nom = serializers.CharField(
        source="commune.nom",
        read_only=True,
    )

    class Meta:
        model = CultureSuivie
        fields = [
            "id",
            "culture_nom",
            "region_nom",
            "departement_nom",
            "commune_nom",
            "superficie",
            "date_semis",
            "type_sol",
        ]


class AdminFarmerSerializer(serializers.ModelSerializer):
    cultures_count = serializers.SerializerMethodField(
        read_only=True
    )

    cultures = AdminCultureSummarySerializer(
        source="cultures_suivies",
        many=True,
        read_only=True,
    )

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
    )

    role = serializers.CharField(
        read_only=True
    )

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "telephone",
            "role",
            "is_active",
            "cultures_count",
            "cultures",
            "password",
        ]

    def get_cultures_count(self, obj):
        return obj.cultures_suivies.count()

    def validate_password(self, value):
        validate_password(value, self.instance)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(
            **validated_data,
            role="farmer",
        )

        user.set_password(password)
        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop(
            "password",
            None,
        )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Impossible de transformer l'agriculteur en administrateur
        instance.role = "farmer"

        if password:
            instance.set_password(password)

        instance.save()

        return instance


class AdminAddCultureSerializer(serializers.Serializer):
    culture = serializers.PrimaryKeyRelatedField(
        queryset=CultureRef.objects.filter(
            actif=True,
            code__in=OFFICIAL_CULTURE_CODES,
        )
    )

    superficie = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
    )

    date_semis = serializers.DateField()

    type_sol = serializers.ChoiceField(
        choices=CultureSuivie.SOIL_CHOICES
    )

    region = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        required=False,
        allow_null=True,
    )

    departement = serializers.PrimaryKeyRelatedField(
        queryset=Departement.objects.all(),
        required=False,
        allow_null=True,
    )

    commune = serializers.PrimaryKeyRelatedField(
        queryset=CommuneLocalite.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        farmer = self.context["farmer"]

        region = attrs.get("region")
        departement = attrs.get("departement")
        commune = attrs.get("commune")

        # ---------------------------------------------------------
        # Si l'admin ne donne pas la localisation,
        # on reprend celle d'une culture précédente.
        # ---------------------------------------------------------
        if not region or not departement or not commune:
            previous_culture = (
                farmer.cultures_suivies
                .select_related(
                    "region",
                    "departement",
                    "commune",
                )
                .order_by("-id")
                .first()
            )

            if previous_culture:
                region = region or previous_culture.region
                departement = (
                    departement
                    or previous_culture.departement
                )
                commune = commune or previous_culture.commune

        # ---------------------------------------------------------
        # Dernier recours : localisation temporaire.
        # ---------------------------------------------------------
        if not region:
            region = Region.objects.order_by("id").first()

        if not region:
            raise serializers.ValidationError(
                "Aucune région disponible."
            )

        if not departement:
            departement = (
                Departement.objects
                .filter(region=region)
                .order_by("id")
                .first()
            )

        if not departement:
            raise serializers.ValidationError(
                "Aucun département disponible pour cette région."
            )

        if not commune:
            commune = (
                CommuneLocalite.objects
                .filter(departement=departement)
                .order_by("id")
                .first()
            )

        if not commune:
            commune = CommuneLocalite.objects.create(
                departement=departement,
                nom="Localité temporaire",
                latitude=None,
                longitude=None,
            )

        # ---------------------------------------------------------
        # Vérifications hiérarchiques.
        # ---------------------------------------------------------
        if departement.region_id != region.id:
            raise serializers.ValidationError({
                "departement": (
                    "Le département sélectionné "
                    "n'appartient pas à la région."
                )
            })

        if commune.departement_id != departement.id:
            raise serializers.ValidationError({
                "commune": (
                    "La commune/localité sélectionnée "
                    "n'appartient pas au département."
                )
            })

        attrs["region"] = region
        attrs["departement"] = departement
        attrs["commune"] = commune

        return attrs

    def create(self, validated_data):
        farmer = self.context["farmer"]

        return CultureSuivie.objects.create(
            agriculteur=farmer,
            culture=validated_data["culture"],
            region=validated_data["region"],
            departement=validated_data["departement"],
            commune=validated_data["commune"],
            superficie=validated_data["superficie"],
            date_semis=validated_data["date_semis"],
            type_sol=validated_data["type_sol"],
        )