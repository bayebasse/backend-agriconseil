from pathlib import Path

from rest_framework import serializers

from .models import Conversation, Message


MAX_AUDIO_BYTES = 10 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/wav", "audio/x-wav",
    "audio/mpeg", "audio/mp4", "audio/x-m4a",
}


def _valid_audio_signature(audio_file, content_type):
    audio_file.seek(0)
    header = audio_file.read(16)
    audio_file.seek(0)
    if content_type == "audio/webm":
        return header.startswith(bytes.fromhex("1A45DFA3"))
    if content_type == "audio/ogg":
        return header.startswith(b"OggS")
    if content_type in {"audio/wav", "audio/x-wav"}:
        return header.startswith(b"RIFF") and header[8:12] == b"WAVE"
    if content_type in {"audio/mp4", "audio/x-m4a"}:
        return header[4:8] == b"ftyp"
    if content_type == "audio/mpeg":
        return header.startswith(b"ID3") or (len(header) > 1 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0)
    return False


class ConversationSerializer(serializers.ModelSerializer):
    culture_nom = serializers.CharField(source="culture.culture.nom", read_only=True)
    culture_id = serializers.IntegerField(read_only=True)
    localisation = serializers.CharField(source="culture.commune.nom", read_only=True)
    agriculteur_nom = serializers.SerializerMethodField()
    acheteur_nom = serializers.SerializerMethodField()
    dernier_message = serializers.SerializerMethodField()
    messages_non_lus = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "culture_id", "culture_nom", "localisation",
            "buyer", "acheteur_nom", "farmer", "agriculteur_nom",
            "created_at", "updated_at", "dernier_message", "messages_non_lus",
        ]

    def get_agriculteur_nom(self, conversation):
        user = conversation.farmer
        return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.username

    def get_acheteur_nom(self, conversation):
        user = conversation.buyer
        return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.username

    def get_dernier_message(self, conversation):
        message = conversation.messages.last()
        if not message:
            return None
        if message.message_type == "audio":
            content = "Message vocal"
        else:
            content = message.content[:180]
        return {"type": message.message_type, "contenu": content, "date": message.created_at}

    def get_messages_non_lus(self, conversation):
        user = self.context["request"].user
        return conversation.messages.filter(read_at__isnull=True).exclude(sender=user).count()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    has_audio = serializers.SerializerMethodField()
    audio_endpoint = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id", "sender", "sender_name", "message_type", "content",
            "has_audio", "audio_content_type", "audio_endpoint",
            "created_at", "read_at",
        ]

    def get_sender_name(self, message):
        user = message.sender
        return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.username

    def get_has_audio(self, message):
        return bool(message.audio_file)

    def get_audio_endpoint(self, message):
        if not message.audio_file:
            return None
        return f"/api/messages/{message.pk}/audio/"


class MessageCreateSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField(required=False, write_only=True)

    class Meta:
        model = Message
        fields = ["message_type", "content", "audio_file"]

    def validate(self, attrs):
        message_type = attrs.get("message_type")
        content = (attrs.get("content") or "").strip()
        audio_file = attrs.get("audio_file")
        if message_type == "text":
            if not content or audio_file:
                raise serializers.ValidationError("Un message texte doit contenir du texte uniquement.")
            attrs["content"] = content
        elif message_type == "audio":
            if content or not audio_file:
                raise serializers.ValidationError("Un message vocal doit contenir un fichier audio uniquement.")
            if audio_file.size > MAX_AUDIO_BYTES:
                raise serializers.ValidationError({"audio_file": "Le message vocal ne peut pas dépasser 10 Mo."})
            content_type = (audio_file.content_type or "").split(";", 1)[0].lower()
            if content_type not in ALLOWED_AUDIO_TYPES:
                raise serializers.ValidationError({"audio_file": "Format audio non pris en charge."})
            if not _valid_audio_signature(audio_file, content_type):
                raise serializers.ValidationError({"audio_file": "Le contenu du fichier ne correspond pas à un audio valide."})
            attrs["audio_content_type"] = content_type
        else:
            raise serializers.ValidationError({"message_type": "Type de message invalide."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("audio_file", None) if validated_data.get("message_type") == "text" else None
        return super().create(validated_data)
