from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Photo
from .serializers import AgriculturalQuestionSerializer, PhotoSerializer
from .services import analyze_photo
from .rag import answer_agricultural_question
from .chatbot import answer_chatbot_question

class AnalyzePhotoView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        serializer = PhotoSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()
        try:
            analyze_photo(photo)
        except RuntimeError as exc:
            photo.delete()
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as exc:
            photo.delete()
            return Response({"detail": f"Le service IA n'a pas pu analyser l'image : {exc}"}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(PhotoSerializer(photo).data, status=status.HTTP_201_CREATED)

class PhotoListView(APIView):
    def get(self, request):
        photos = Photo.objects.filter(agriculteur=request.user).order_by("-date_prise")
        return Response(PhotoSerializer(photos, many=True).data)


class AgriculturalChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AgriculturalQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(answer_agricultural_question(serializer.validated_data["question"]))


class ChatbotView(APIView):
    """Public endpoint for the global floating help chatbot."""

    permission_classes = []

    def post(self, request):
        question = request.data.get("question") if isinstance(request.data, dict) else None
        if not isinstance(question, str) or len(question.strip()) < 2 or len(question) > 1500:
            return Response({"detail": "Saisissez une question de 2 à 1500 caractères."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(answer_chatbot_question(question.strip()))
