from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.cultures.models import (
    CommuneLocalite, CultureRef, CultureSuivie, Departement, Region,
)
from .models import Conversation, Message


class BuyerMessagingApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.buyer = user_model.objects.create_user(
            username="buyer", password="pass-12345", role="buyer"
        )
        self.farmer = user_model.objects.create_user(
            username="farmer", password="pass-12345", role="farmer",
            first_name="Awa", last_name="Diop", telephone="+221770000000",
        )
        self.other_buyer = user_model.objects.create_user(
            username="other-buyer", password="pass-12345", role="buyer"
        )
        self.other_farmer = user_model.objects.create_user(
            username="other-farmer", password="pass-12345", role="farmer"
        )
        region = Region.objects.create(nom="Test")
        department = Departement.objects.create(region=region, nom="Test")
        commune = CommuneLocalite.objects.create(
            departement=department, nom="Test", type_localite="commune"
        )
        crop_ref = CultureRef.objects.create(nom="Mil", code="mil")
        self.crop = CultureSuivie.objects.create(
            agriculteur=self.farmer, culture=crop_ref, region=region,
            departement=department, commune=commune, superficie=Decimal("2"),
            date_semis=date(2026, 1, 1), type_sol="limoneux",
        )
        self.conversation = Conversation.objects.create(
            culture=self.crop, buyer=self.buyer, farmer=self.farmer
        )
        self.client = APIClient()

    def test_buyer_can_register_login_and_cannot_escalate_role(self):
        response = self.client.post(reverse("user-register"), {
            "username": "new-buyer", "password": "pass-12345",
            "role": "buyer",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], "buyer")

        response = self.client.post(reverse("user-login"), {
            "username": "new-buyer", "password": "pass-12345",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "buyer")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        response = self.client.patch(reverse("user-me"), {"role": "admin"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "buyer")

    def test_new_farmer_crop_is_listed_only_for_buyers_and_is_read_only(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.get(reverse("buyer-crop-catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.crop.pk)
        self.assertEqual(response.data["results"][0]["agriculteur_prenom"], "Awa")
        self.assertEqual(response.data["results"][0]["agriculteur_nom"], "Diop")
        self.assertEqual(response.data["results"][0]["agriculteur_telephone"], "+221770000000")

        response = self.client.patch(
            reverse("mes-cultures-detail", args=[self.crop.pk]),
            {"superficie": "100"}, format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_buyer_can_start_and_reuse_crop_conversation(self):
        self.client.force_authenticate(self.buyer)
        url = reverse("conversation-from-crop", args=[self.crop.pk])
        first = self.client.post(url, {}, format="json")
        second = self.client.post(url, {}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["id"], second.data["id"])

    def test_buyer_and_farmer_share_history_and_read_state(self):
        messages_url = reverse("conversation-messages", args=[self.conversation.pk])
        self.client.force_authenticate(self.buyer)
        buyer_message = self.client.post(messages_url, {
            "message_type": "text", "content": "Bonjour", "sender": self.other_buyer.pk,
        }, format="json")
        self.assertEqual(buyer_message.status_code, 201)
        self.assertEqual(buyer_message.data["sender"], self.buyer.pk)

        self.client.force_authenticate(self.farmer)
        inbox = self.client.get(reverse("conversation-list"))
        self.assertEqual(inbox.data[0]["messages_non_lus"], 1)
        farmer_history = self.client.get(messages_url)
        self.assertEqual(farmer_history.data[0]["content"], "Bonjour")
        self.assertIsNotNone(farmer_history.data[0]["read_at"])
        self.assertEqual(self.client.get(reverse("conversation-list")).data[0]["messages_non_lus"], 0)

        farmer_reply = self.client.post(messages_url, {
            "message_type": "text", "content": "Bonjour, je vous réponds.",
        }, format="json")
        self.assertEqual(farmer_reply.status_code, 201)
        self.client.force_authenticate(self.buyer)
        buyer_history = self.client.get(messages_url)
        self.assertEqual([item["content"] for item in buyer_history.data], [
            "Bonjour", "Bonjour, je vous réponds.",
        ])
        self.assertIsNotNone(buyer_history.data[-1]["read_at"])

    def test_conversation_and_audio_are_limited_to_participants(self):
        messages_url = reverse("conversation-messages", args=[self.conversation.pk])
        self.client.force_authenticate(self.other_farmer)
        self.assertEqual(self.client.get(messages_url).status_code, 404)
        self.client.force_authenticate(self.other_buyer)
        self.assertEqual(self.client.get(messages_url).status_code, 404)

        self.client.force_authenticate(self.buyer)
        upload = SimpleUploadedFile(
            "voice.ogg", b"OggS" + b"\x00" * 20, content_type="audio/ogg"
        )
        storage = Message._meta.get_field("audio_file").storage
        with patch.object(storage, "save", return_value="voice_messages/test.ogg"), \
                patch.object(storage, "open", return_value=BytesIO(b"OggS" + b"\x00" * 20)):
            response = self.client.post(messages_url, {
                "message_type": "audio", "audio_file": upload,
            }, format="multipart")
            self.assertEqual(response.status_code, 201)
            message = Message.objects.get(pk=response.data["id"])
            self.assertTrue(message.audio_file)
            self.assertNotIn("/media/", message.audio_file.url)

            audio_url = reverse("message-audio", args=[message.pk])
            self.assertEqual(self.client.get(audio_url).status_code, 200)
            self.client.force_authenticate(self.farmer)
            self.assertEqual(self.client.get(audio_url).status_code, 200)

            farmer_upload = SimpleUploadedFile(
                "reply.ogg", b"OggS" + b"\x00" * 20, content_type="audio/ogg"
            )
            farmer_reply = self.client.post(messages_url, {
                "message_type": "audio", "audio_file": farmer_upload,
            }, format="multipart")
            self.assertEqual(farmer_reply.status_code, 201)
            self.client.force_authenticate(self.buyer)
            reply_audio_url = reverse("message-audio", args=[farmer_reply.data["id"]])
            self.assertEqual(self.client.get(reply_audio_url).status_code, 200)

            self.client.force_authenticate(self.other_buyer)
            self.assertEqual(self.client.get(audio_url).status_code, 404)

    def test_invalid_or_oversized_audio_is_rejected(self):
        url = reverse("conversation-messages", args=[self.conversation.pk])
        self.client.force_authenticate(self.buyer)
        invalid = SimpleUploadedFile("fake.ogg", b"not audio", content_type="audio/ogg")
        response = self.client.post(url, {
            "message_type": "audio", "audio_file": invalid,
        }, format="multipart")
        self.assertEqual(response.status_code, 400)

        oversized = SimpleUploadedFile(
            "large.ogg", b"OggS" + b"x" * (10 * 1024 * 1024),
            content_type="audio/ogg",
        )
        response = self.client.post(url, {
            "message_type": "audio", "audio_file": oversized,
        }, format="multipart")
        self.assertEqual(response.status_code, 400)
