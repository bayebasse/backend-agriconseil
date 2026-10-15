from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from apps.cultures.models import CultureSuivie
from apps.cultures.prediction_service import estimated_production_kg
from .models import Commande, Reservation


def quantity_to_kg(quantity, unit):
    value = Decimal(quantity)
    return value * Decimal("1000") if unit == "tonne" else value


def available_quantity_kg(crop):
    if crop.quantite_disponible_vente is None:
        return Decimal("0")
    return quantity_to_kg(crop.quantite_disponible_vente, crop.unite_disponible_vente)


def set_available_quantity_kg(crop, amount_kg):
    amount_kg = Decimal(amount_kg)
    if crop.unite_disponible_vente not in {"kg", "tonne"}:
        crop.unite_disponible_vente = "kg"
    if crop.unite_disponible_vente == "tonne":
        if amount_kg != amount_kg.to_integral_value():
            raise ValidationError("Pour un stock en tonnes, les commandes doivent être exprimées en kilogrammes entiers.")
        crop.quantite_disponible_vente = amount_kg / Decimal("1000")
    else:
        crop.quantite_disponible_vente = amount_kg
    if amount_kg == 0:
        crop.statut_recolte = "exhausted"
    elif crop.statut_recolte == "exhausted":
        crop.statut_recolte = "available"
    crop.save(update_fields=["quantite_disponible_vente", "unite_disponible_vente", "statut_recolte", "updated_at"])


def forecast_remaining_kg(crop):
    estimated = estimated_production_kg(crop)
    if estimated is None:
        return None
    harvested_kg = sum(
        (
            Decimal(harvest.quantite)
            * (Decimal("1000") if harvest.unite == "tonne" else Decimal("1"))
            for harvest in crop.recoltes_reelles.all()
        ),
        Decimal("0"),
    )
    firmly_reserved = Reservation.objects.filter(
        culture_suivie=crop,
        type_reservation="firm",
        statut="confirmed",
    ).aggregate(total=Sum("quantite_kg"))["total"] or Decimal("0")
    return max(Decimal("0"), estimated - harvested_kg - firmly_reserved)


def confirm_order(order_id, user):
    with transaction.atomic():
        order = Commande.objects.select_for_update().select_related("culture_suivie").get(pk=order_id)
        if order.culture_suivie.agriculteur_id != user.pk:
            raise PermissionError
        if order.statut != "pending":
            raise ValidationError("Seule une commande en attente peut être validée.")
        crop = CultureSuivie.objects.select_for_update().get(pk=order.culture_suivie_id)
        if crop.statut_recolte != "available":
            raise ValidationError("Cette récolte n'est plus disponible à la vente.")
        current_kg = available_quantity_kg(crop)
        if order.quantite_kg > current_kg:
            raise ValidationError({"quantite_kg": "La quantité disponible ne permet plus de valider cette commande."})
        set_available_quantity_kg(crop, current_kg - order.quantite_kg)
        order.statut = "confirmed"
        order.save(update_fields=["statut", "updated_at"])
        return order


def confirm_reservation(reservation_id, user):
    with transaction.atomic():
        reservation = Reservation.objects.select_for_update().select_related("culture_suivie").get(pk=reservation_id)
        if reservation.culture_suivie.agriculteur_id != user.pk:
            raise PermissionError
        if reservation.statut != "pending":
            raise ValidationError("Seule une réservation en attente peut être confirmée.")
        crop = CultureSuivie.objects.select_for_update().get(pk=reservation.culture_suivie_id)
        if crop.statut_recolte != "in_progress":
            raise ValidationError("Cette culture n'est plus en cours de récolte.")
        if reservation.type_reservation == "firm":
            remaining = forecast_remaining_kg(crop)
            if remaining is None:
                raise ValidationError("Aucune prévision de production vérifiée ne permet de confirmer une réservation ferme.")
            if reservation.quantite_kg > remaining:
                raise ValidationError({"quantite_kg": "La quantité prévisionnelle encore réservable est insuffisante."})
        reservation.statut = "confirmed"
        reservation.save(update_fields=["statut", "updated_at"])
        return reservation


def apply_transaction_action(instance, action, user, kind):
    try:
        if kind == "order" and action == "confirm":
            return confirm_order(instance.pk, user)
        if kind == "reservation" and action == "confirm":
            return confirm_reservation(instance.pk, user)
        with transaction.atomic():
            model = Commande if kind == "order" else Reservation
            item = model.objects.select_for_update().select_related("culture_suivie").get(pk=instance.pk)
            is_farmer = item.culture_suivie.agriculteur_id == user.pk
            is_buyer = item.acheteur_id == user.pk
            if not (is_farmer or is_buyer):
                raise PermissionError
            if action == "refuse":
                if not is_farmer or item.statut != "pending":
                    raise ValidationError("Seul l'agriculteur peut refuser une demande en attente.")
                item.statut = "refused"
            elif action == "cancel":
                if item.statut not in ({"pending", "confirmed"} if kind == "order" else {"pending", "confirmed"}):
                    raise ValidationError("Cette demande ne peut plus être annulée.")
                if kind == "order" and item.statut == "confirmed":
                    crop = CultureSuivie.objects.select_for_update().get(pk=item.culture_suivie_id)
                    set_available_quantity_kg(crop, available_quantity_kg(crop) + item.quantite_kg)
                item.statut = "cancelled"
            elif action == "deliver":
                if not is_farmer or kind != "order" or item.statut != "confirmed":
                    raise ValidationError("Seule une commande validée peut être marquée comme livrée par l'agriculteur.")
                item.statut = "delivered"
            else:
                raise ValidationError({"action": "Action inconnue."})
            item.save(update_fields=["statut", "updated_at"])
            return item
    except (Commande.DoesNotExist, Reservation.DoesNotExist) as exc:
        raise ValidationError("Demande introuvable.") from exc
