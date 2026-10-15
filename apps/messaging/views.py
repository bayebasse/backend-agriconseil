from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cultures.models import CultureSuivie
from apps.users.permissions import IsBuyerRole
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageCreateSerializer, MessageSerializer


def _conversation_for_participant(request, conversation_id):
    return get_object_or_404(
        Conversation.objects.select_related(
            "culture__culture", "culture__commune", "buyer", "farmer"
        ),
        Q(buyer=request.user) | Q(farmer=request.user),
        pk=conversation_id,
    )


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in {"buyer", "farmer"}:
            raise PermissionDenied("La messagerie est réservée aux acheteurs et agriculteurs participants.")
        conversations = Conversation.objects.filter(
            Q(buyer=request.user) | Q(farmer=request.user)
        ).select_related("culture__culture", "culture__commune", "buyer", "farmer")
        return Response(ConversationSerializer(conversations, many=True, context={"request": request}).data)


class StartConversationView(APIView):
    permission_classes = [IsAuthenticated, IsBuyerRole]

    def post(self, request, culture_id):
        crop = get_object_or_404(
            CultureSuivie.objects.select_related("agriculteur"),
            pk=culture_id,
        )
        if crop.agriculteur.role != "farmer":
            raise PermissionDenied("Cette culture n'appartient pas à un compte agriculteur.")
        conversation, _created = Conversation.objects.get_or_create(
            culture=crop,
            buyer=request.user,
            farmer=crop.agriculteur,
        )
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = _conversation_for_participant(request, conversation_id)
        conversation.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(
            read_at=timezone.now()
        )
        messages = conversation.messages.select_related("sender")
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request, conversation_id):
        conversation = _conversation_for_participant(request, conversation_id)
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(conversation=conversation, sender=request.user)
        conversation.updated_at = message.created_at
        conversation.save(update_fields=["updated_at"])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MessageAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        message = get_object_or_404(
            Message.objects.select_related("conversation"),
            pk=message_id,
        )
        _conversation_for_participant(request, message.conversation_id)
        if not message.audio_file:
            return Response({"detail": "Aucun fichier audio pour ce message."}, status=404)
        try:
            audio = message.audio_file.open("rb")
        except OSError:
            return Response({"detail": "Fichier audio indisponible."}, status=404)
        response = FileResponse(
            audio,
            content_type=message.audio_content_type or "application/octet-stream",
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Security-Policy"] = "default-src 'none'; media-src 'self'"
        return response
