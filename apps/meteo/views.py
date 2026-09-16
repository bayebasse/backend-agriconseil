from rest_framework.views import APIView
from rest_framework.response import Response
from apps.cultures.models import CultureSuivie
from .services import get_local_weather
from .serializers import MeteoSerializer
class MeteoCultureView(APIView):
    def get(self, request, culture_id):
        culture = CultureSuivie.objects.filter(id=culture_id, agriculteur=request.user).select_related("commune").first()
        if not culture: return Response({"detail":"Culture introuvable."}, status=404)
        return Response(MeteoSerializer(get_local_weather(culture.commune)).data)
