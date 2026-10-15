from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.cultures.models import (
    CommuneLocalite,
    CultureRef,
    CultureSuivie,
    Departement,
    RecolteReelle,
    Region,
)
from apps.transactions.models import Commande, Reservation


class MarketplaceTransactionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.farmer = user_model.objects.create_user(
            username="farmer-market", password="test-password", role="farmer",
        )
        self.buyer = user_model.objects.create_user(
            username="buyer-market", password="test-password", role="buyer",
        )
        self.other_buyer = user_model.objects.create_user(
            username="other-buyer-market", password="test-password", role="buyer",
        )
        self.region = Region.objects.create(nom="Market region")
        self.department = Departement.objects.create(region=self.region, nom="Market department")
        self.commune = CommuneLocalite.objects.create(
            departement=self.department, nom="Market commune", type_localite="commune",
        )
        self.reference = CultureRef.objects.create(nom="Mil market", code="mil-market")
        self.crop = CultureSuivie.objects.create(
            agriculteur=self.farmer,
            culture=self.reference,
            region=self.region,
            departement=self.department,
            commune=self.commune,
            superficie=Decimal("1.00"),
            date_semis=timezone.localdate() - timedelta(days=30),
            type_sol="limoneux",
            statut_recolte="available",
            quantite_disponible_vente=Decimal("10.000"),
            unite_disponible_vente="kg",
            prix_kg_fcfa=Decimal("250.00"),
        )
        self.client = APIClient()
        self.order_url = f"/api/transactions/crops/{self.crop.pk}/orders/"
        self.reservation_url = f"/api/transactions/crops/{self.crop.pk}/reservations/"

    def _date(self):
        return (timezone.localdate() + timedelta(days=5)).isoformat()

    def _create_order(self, quantity="4"):
        self.client.force_authenticate(self.buyer)
        return self.client.post(self.order_url, {
            "quantite_kg": quantity,
            "date_souhaitee": self._date(),
            "message": "Livraison souhaitée",
        }, format="json")

    def test_order_reserves_no_stock_until_farmer_confirms_then_cancel_restores_once(self):
        response = self._create_order()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.crop.quantite_disponible_vente, Decimal("10.000"))
        order_id = response.data["id"]

        self.client.force_authenticate(self.farmer)
        confirmed = self.client.post(
            f"/api/transactions/orders/{order_id}/action/", {"action": "confirm"}, format="json",
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.data)
        self.crop.refresh_from_db()
        self.assertEqual(self.crop.quantite_disponible_vente, Decimal("6.000"))
        self.assertEqual(self.crop.statut_recolte, "available")

        self.client.force_authenticate(self.buyer)
        cancelled = self.client.post(
            f"/api/transactions/orders/{order_id}/action/", {"action": "cancel"}, format="json",
        )
        duplicate_cancel = self.client.post(
            f"/api/transactions/orders/{order_id}/action/", {"action": "cancel"}, format="json",
        )
        self.assertEqual(cancelled.status_code, 200, cancelled.data)
        self.assertEqual(duplicate_cancel.status_code, 400)
        self.crop.refresh_from_db()
        self.assertEqual(self.crop.quantite_disponible_vente, Decimal("10.000"))
        self.assertEqual(Commande.objects.get(pk=order_id).statut, "cancelled")

    def test_buyer_cannot_order_more_than_real_available_stock(self):
        response = self._create_order("10.001")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Commande.objects.count(), 0)

    def test_two_pending_orders_cannot_commit_more_than_stock(self):
        first = self._create_order("7")
        second = self._create_order("7")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.client.force_authenticate(self.farmer)
        confirmed = self.client.post(
            f"/api/transactions/orders/{first.data['id']}/action/", {"action": "confirm"}, format="json",
        )
        rejected = self.client.post(
            f"/api/transactions/orders/{second.data['id']}/action/", {"action": "confirm"}, format="json",
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.data)
        self.assertEqual(rejected.status_code, 400)
        self.crop.refresh_from_db()
        self.assertEqual(self.crop.quantite_disponible_vente, Decimal("3.000"))

    def test_delivered_order_is_not_restored_or_cancelled(self):
        response = self._create_order("4")
        order_id = response.data["id"]
        self.client.force_authenticate(self.farmer)
        self.client.post(f"/api/transactions/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        delivered = self.client.post(
            f"/api/transactions/orders/{order_id}/action/", {"action": "deliver"}, format="json",
        )
        self.assertEqual(delivered.status_code, 200, delivered.data)
        self.client.force_authenticate(self.buyer)
        cancelled = self.client.post(
            f"/api/transactions/orders/{order_id}/action/", {"action": "cancel"}, format="json",
        )
        self.assertEqual(cancelled.status_code, 400)
        self.crop.refresh_from_db()
        self.assertEqual(self.crop.quantite_disponible_vente, Decimal("6.000"))

    def test_unavailable_crop_and_non_buyer_cannot_create_orders(self):
        self.crop.statut_recolte = "in_progress"
        self.crop.save(update_fields=["statut_recolte"])
        self.assertEqual(self._create_order().status_code, 400)

        self.crop.statut_recolte = "available"
        self.crop.save(update_fields=["statut_recolte"])
        self.client.force_authenticate(self.farmer)
        response = self.client.post(self.order_url, {
            "quantite_kg": "1", "date_souhaitee": self._date(),
        }, format="json")
        self.assertEqual(response.status_code, 403)

    def test_indicative_reservation_does_not_deduct_sellable_stock(self):
        self.crop.statut_recolte = "in_progress"
        self.crop.save(update_fields=["statut_recolte"])
        self.client.force_authenticate(self.buyer)
        response = self.client.post(self.reservation_url, {
            "quantite_kg": "5",
            "date_disponibilite_souhaitee": self._date(),
            "type_reservation": "indicative",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        reservation_id = response.data["id"]

        self.client.force_authenticate(self.farmer)
        confirmed = self.client.post(
            f"/api/transactions/reservations/{reservation_id}/action/", {"action": "confirm"}, format="json",
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.data)
        self.crop.refresh_from_db()
        self.assertEqual(self.crop.quantite_disponible_vente, Decimal("10.000"))
        self.assertEqual(Reservation.objects.get(pk=reservation_id).statut, "confirmed")

    @patch("apps.transactions.services.estimated_production_kg", return_value=Decimal("10"))
    def test_firm_reservations_cannot_exceed_forecast_and_are_not_sales(self, _estimate):
        self.crop.statut_recolte = "in_progress"
        self.crop.save(update_fields=["statut_recolte"])
        RecolteReelle.objects.create(
            culture_suivie=self.crop,
            date_recolte=timezone.localdate(),
            quantite=Decimal("3"),
            unite="kg",
        )
        self.client.force_authenticate(self.buyer)
        payload = {
            "quantite_kg": "4",
            "date_disponibilite_souhaitee": self._date(),
            "type_reservation": "firm",
        }
        first = self.client.post(self.reservation_url, payload, format="json")
        second = self.client.post(self.reservation_url, payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)

        self.client.force_authenticate(self.farmer)
        confirm_one = self.client.post(
            f"/api/transactions/reservations/{first.data['id']}/action/", {"action": "confirm"}, format="json",
        )
        confirm_two = self.client.post(
            f"/api/transactions/reservations/{second.data['id']}/action/", {"action": "confirm"}, format="json",
        )
        self.assertEqual(confirm_one.status_code, 200, confirm_one.data)
        self.assertEqual(confirm_two.status_code, 400)
        self.crop.refresh_from_db()
        self.assertEqual(self.crop.quantite_disponible_vente, Decimal("10.000"))

    def test_only_transaction_participants_can_list_or_change_it(self):
        response = self._create_order("2")
        order_id = response.data["id"]
        self.client.force_authenticate(self.other_buyer)
        self.assertEqual(self.client.get("/api/transactions/orders/").status_code, 200)
        denied = self.client.post(
            f"/api/transactions/orders/{order_id}/action/", {"action": "cancel"}, format="json",
        )
        self.assertEqual(denied.status_code, 404)

    def test_farmer_lists_requests_through_owned_crop_and_other_farmer_sees_none(self):
        order = self._create_order("2")
        self.crop.statut_recolte = "in_progress"
        self.crop.save(update_fields=["statut_recolte"])
        self.client.force_authenticate(self.buyer)
        reservation = self.client.post(self.reservation_url, {
            "quantite_kg": "3",
            "date_disponibilite_souhaitee": self._date(),
            "type_reservation": "indicative",
        }, format="json")
        self.assertEqual(reservation.status_code, 201, reservation.data)

        self.client.force_authenticate(self.farmer)
        farmer_orders = self.client.get("/api/transactions/orders/")
        farmer_reservations = self.client.get("/api/transactions/reservations/")
        self.assertEqual([item["id"] for item in farmer_orders.data], [order.data["id"]])
        self.assertEqual([item["id"] for item in farmer_reservations.data], [reservation.data["id"]])
        self.assertIn("recolte_prevue", farmer_reservations.data[0])

        other_farmer = get_user_model().objects.create_user(
            username="different-farmer", password="test-password", role="farmer",
        )
        self.client.force_authenticate(other_farmer)
        self.assertEqual(self.client.get("/api/transactions/orders/").data, [])
        self.assertEqual(self.client.get("/api/transactions/reservations/").data, [])
