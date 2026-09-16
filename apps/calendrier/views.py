from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.cultures.models import CultureSuivie
from .services import ensure_calendar, current_stage
from .serializers import CalendrierSerializer, StadeSerializer
class CalendrierDetailView(APIView):
    def get(self, request, culture_id):
        culture = CultureSuivie.objects.filter(id=culture_id, agriculteur=request.user).first()
        if not culture: return Response({"detail":"Culture introuvable."}, status=404)
        return Response(CalendrierSerializer(ensure_calendar(culture)).data)
class StadeView(APIView):
    def get(self, request, culture_id):
        culture = CultureSuivie.objects.filter(id=culture_id, agriculteur=request.user).first()
        if not culture: return Response({"detail":"Culture introuvable."}, status=404)
        stage = current_stage(culture)
        return Response(StadeSerializer(stage).data if stage else None)

