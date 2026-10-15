from django.conf import settings
from django.db import models

from apps.cultures.models import CultureSuivie
from .storage import PrivateAudioStorage


private_audio_storage = PrivateAudioStorage()


class Conversation(models.Model):
    culture = models.ForeignKey(
        CultureSuivie, on_delete=models.CASCADE, related_name="conversations"
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="buyer_conversations",
    )
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="farmer_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["culture", "buyer", "farmer"],
                name="unique_buyer_farmer_crop_conversation",
            )
        ]

    def __str__(self):
        return f"{self.culture} — {self.buyer} / {self.farmer}"


class Message(models.Model):
    TYPE_CHOICES = [("text", "Texte"), ("audio", "Vocal")]
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="agri_messages",
    )
    message_type = models.CharField(max_length=8, choices=TYPE_CHOICES)
    content = models.TextField(blank=True, max_length=5000)
    audio_file = models.FileField(
        storage=private_audio_storage,
        upload_to="voice_messages/%Y/%m/",
        blank=True,
    )
    audio_content_type = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.message_type} — {self.sender} — {self.created_at}"
