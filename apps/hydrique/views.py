from rest_framework.views import APIView
from rest_framework.response import Response
from apps.cultures.models import CultureSuivie
from .services import build_hydric_advice
from .serializers import HydricSerializer
class HydricView(APIView):
    def get(self, request, culture_id):
        culture = CultureSuivie.objects.filter(id=culture_id, agriculteur=request.user).select_related("culture","commune").first()
        if not culture: return Response({"detail":"Culture introuvable."}, status=404)
        return Response(HydricSerializer(build_hydric_advice(culture)).data)
