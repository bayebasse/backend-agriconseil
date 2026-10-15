from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.cultures.models import CultureSuivie


class Commande(models.Model):
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("confirmed", "Validée"),
        ("refused", "Refusée"),
        ("cancelled", "Annulée"),
        ("delivered", "Livrée"),
    ]

    acheteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="commandes_acheteur",
    )
    culture_suivie = models.ForeignKey(
        CultureSuivie, on_delete=models.CASCADE, related_name="commandes",
    )
    quantite_kg = models.DecimalField(
        max_digits=14, decimal_places=3, validators=[MinValueValidator(0.001)],
    )
    date_souhaitee = models.DateField()
    message = models.TextField(blank=True, max_length=2000)
    prix_kg_fcfa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    statut = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class Reservation(models.Model):
    TYPE_CHOICES = [("firm", "Ferme"), ("indicative", "Indicative")]
    STATUS_CHOICES = [
        ("pending", "En attente de confirmation"),
        ("confirmed", "Confirmée"),
        ("refused", "Refusée"),
        ("cancelled", "Annulée"),
    ]

    acheteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="reservations_acheteur",
    )
    culture_suivie = models.ForeignKey(
        CultureSuivie, on_delete=models.CASCADE, related_name="reservations",
    )
    quantite_kg = models.DecimalField(
        max_digits=14, decimal_places=3, validators=[MinValueValidator(0.001)],
    )
    date_disponibilite_souhaitee = models.DateField()
    type_reservation = models.CharField(max_length=12, choices=TYPE_CHOICES)
    message = models.TextField(blank=True, max_length=2000)
    statut = models.CharField(max_length=24, choices=STATUS_CHOICES, default="pending", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
