from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Photo
from .serializers import PhotoSerializer
from .services import analyze_photo

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
