
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.cultures.models import CultureSuivie

from .services import get_region_weather


class MeteoCultureView(APIView):

    def get(self, request, culture_id):

        culture = (
            CultureSuivie.objects
            .filter(
                id=culture_id,
                agriculteur=request.user,
            )
            .select_related("region")
            .first()
        )

        if not culture:
            return Response(
                {
                    "detail": "Culture introuvable."
                },
                status=404,
            )

        try:
            weather = get_region_weather(
                culture.region
            )

            return Response(weather)

        except Exception as exc:
            return Response(
                {
                    "detail": (
                        "Impossible de récupérer "
                        "la météo de votre région."
                    ),
                    "error": str(exc),
                },
                status=503,
            )