from django.utils import timezone
from rest_framework import serializers

from apps.cultures.prediction_service import _get_reference, _harvest_period
from .models import Commande, Reservation


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = ["quantite_kg", "date_souhaitee", "message"]

    def validate_quantite_kg(self, value):
        crop = self.context["crop"]
        if crop.unite_disponible_vente == "tonne" and value != value.to_integral_value():
            raise serializers.ValidationError("Pour un stock en tonnes, indiquez une quantité entière de kilogrammes.")
        return value

    def validate_date_souhaitee(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("La date souhaitée ne peut pas être passée.")
        return value


class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["quantite_kg", "date_disponibilite_souhaitee", "type_reservation", "message"]

    def validate_date_disponibilite_souhaitee(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("La date souhaitée ne peut pas être passée.")
        return value


class TransactionActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["confirm", "refuse", "cancel", "deliver"])


class OrderSerializer(serializers.ModelSerializer):
    culture_id = serializers.IntegerField(source="culture_suivie_id", read_only=True)
    culture_nom = serializers.CharField(source="culture_suivie.culture.nom", read_only=True)
    buyer_name = serializers.SerializerMethodField()
    farmer_name = serializers.SerializerMethodField()
    farmer_id = serializers.IntegerField(source="culture_suivie.agriculteur_id", read_only=True)

    class Meta:
        model = Commande
        fields = ["id", "culture_id", "culture_nom", "farmer_id", "farmer_name", "acheteur_id", "buyer_name", "quantite_kg", "date_souhaitee", "message", "prix_kg_fcfa", "statut", "created_at", "updated_at"]

    def get_buyer_name(self, item):
        return " ".join(part for part in (item.acheteur.first_name, item.acheteur.last_name) if part).strip() or item.acheteur.username

    def get_farmer_name(self, item):
        user = item.culture_suivie.agriculteur
        return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.username


class ReservationSerializer(serializers.ModelSerializer):
    culture_id = serializers.IntegerField(source="culture_suivie_id", read_only=True)
    culture_nom = serializers.CharField(source="culture_suivie.culture.nom", read_only=True)
    buyer_name = serializers.SerializerMethodField()
    farmer_name = serializers.SerializerMethodField()
    farmer_id = serializers.IntegerField(source="culture_suivie.agriculteur_id", read_only=True)
    recolte_prevue = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = ["id", "culture_id", "culture_nom", "farmer_id", "farmer_name", "acheteur_id", "buyer_name", "quantite_kg", "date_disponibilite_souhaitee", "recolte_prevue", "type_reservation", "message", "statut", "created_at", "updated_at"]

    def get_buyer_name(self, item):
        return " ".join(part for part in (item.acheteur.first_name, item.acheteur.last_name) if part).strip() or item.acheteur.username

    def get_farmer_name(self, item):
        user = item.culture_suivie.agriculteur
        return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.username

    def get_recolte_prevue(self, item):
        crop = item.culture_suivie
        start, end, _reason = _harvest_period(crop, _get_reference(crop))
        return {
            "date_debut": start.isoformat() if start else None,
            "date_fin": end.isoformat() if end else None,
        }
