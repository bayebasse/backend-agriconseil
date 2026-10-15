from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CultureSuivie, RecolteReelle
from .prediction_serializers import (
    PredictionSerializer,
    RecolteReelleSerializer,
)
from .prediction_service import build_yield_prediction


class YieldPredictionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, culture_id):
        culture = get_object_or_404(
            CultureSuivie.objects.select_related("culture", "region"),
            pk=culture_id,
            agriculteur=request.user,
        )
        data = build_yield_prediction(culture)
        return Response(PredictionSerializer(data).data)


class RecolteReelleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_culture(self, request, culture_id):
        return get_object_or_404(
            CultureSuivie,
            pk=culture_id,
            agriculteur=request.user,
        )

    def get(self, request, culture_id):
        culture = self.get_culture(request, culture_id)
        recoltes = RecolteReelle.objects.filter(culture_suivie=culture)
        return Response(RecolteReelleSerializer(recoltes, many=True).data)

    def post(self, request, culture_id):
        culture = self.get_culture(request, culture_id)
        serializer = RecolteReelleSerializer(
            data=request.data,
            context={"culture_suivie": culture},
        )
        serializer.is_valid(raise_exception=True)
        recolte = serializer.save()
        return Response(
            RecolteReelleSerializer(recolte).data,
            status=status.HTTP_201_CREATED,
        )
