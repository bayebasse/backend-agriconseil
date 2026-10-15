from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cultures.models import CultureSuivie
from apps.users.permissions import IsBuyerRole
from .models import Commande, Reservation
from .serializers import (
    OrderCreateSerializer, OrderSerializer, ReservationCreateSerializer,
    ReservationSerializer, TransactionActionSerializer,
)
from .services import apply_transaction_action, available_quantity_kg


def _participants_only(user):
    if user.role not in {"buyer", "farmer"}:
        raise PermissionDenied("Ce service est réservé aux acheteurs et aux agriculteurs.")


def _crop_for_action(culture_id, user):
    return get_object_or_404(
        CultureSuivie.objects.select_related("agriculteur"),
        pk=culture_id,
        agriculteur__role="farmer",
    )


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _participants_only(request.user)
        query = Q(acheteur=request.user) if request.user.role == "buyer" else Q(culture_suivie__agriculteur=request.user)
        items = Commande.objects.filter(query).select_related("acheteur", "culture_suivie__culture", "culture_suivie__agriculteur")
        return Response(OrderSerializer(items, many=True).data)

    def post(self, request, culture_id):
        if not IsBuyerRole().has_permission(request, self):
            raise PermissionDenied(IsBuyerRole.message)
        crop = _crop_for_action(culture_id, request.user)
        with transaction.atomic():
            crop = CultureSuivie.objects.select_for_update().get(pk=crop.pk)
            if crop.statut_recolte != "available" or crop.quantite_disponible_vente is None or crop.quantite_disponible_vente <= 0:
                raise ValidationError("Cette récolte n'est pas disponible à la vente.")
            serializer = OrderCreateSerializer(data=request.data, context={"crop": crop})
            serializer.is_valid(raise_exception=True)
            if serializer.validated_data["quantite_kg"] > available_quantity_kg(crop):
                raise ValidationError({"quantite_kg": "La quantité demandée dépasse le stock réellement disponible."})
            item = serializer.save(
                acheteur=request.user,
                culture_suivie=crop,
                prix_kg_fcfa=crop.prix_kg_fcfa,
            )
        return Response(OrderSerializer(item).data, status=status.HTTP_201_CREATED)


class ReservationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _participants_only(request.user)
        query = Q(acheteur=request.user) if request.user.role == "buyer" else Q(culture_suivie__agriculteur=request.user)
        items = Reservation.objects.filter(query).select_related("acheteur", "culture_suivie__culture", "culture_suivie__agriculteur")
        return Response(ReservationSerializer(items, many=True).data)

    def post(self, request, culture_id):
        if not IsBuyerRole().has_permission(request, self):
            raise PermissionDenied(IsBuyerRole.message)
        crop = _crop_for_action(culture_id, request.user)
        with transaction.atomic():
            crop = CultureSuivie.objects.select_for_update().get(pk=crop.pk)
            if crop.statut_recolte != "in_progress":
                raise ValidationError("Cette culture n'est pas déclarée en cours de récolte.")
            serializer = ReservationCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            item = serializer.save(acheteur=request.user, culture_suivie=crop)
        return Response(ReservationSerializer(item).data, status=status.HTTP_201_CREATED)


class TransactionActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, kind, pk):
        _participants_only(request.user)
        if kind == "order":
            qs = Commande.objects.select_related("culture_suivie")
            serializer_class = OrderSerializer
        else:
            qs = Reservation.objects.select_related("culture_suivie")
            serializer_class = ReservationSerializer
        item = get_object_or_404(qs.filter(Q(acheteur=request.user) | Q(culture_suivie__agriculteur=request.user)), pk=pk)
        action_serializer = TransactionActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        try:
            item = apply_transaction_action(item, action_serializer.validated_data["action"], request.user, kind)
        except PermissionError as exc:
            raise PermissionDenied("Vous ne pouvez pas effectuer cette action.") from exc
        item = (Commande.objects if kind == "order" else Reservation.objects).select_related(
            "acheteur", "culture_suivie__culture", "culture_suivie__agriculteur"
        ).get(pk=item.pk)
        return Response(serializer_class(item).data)
