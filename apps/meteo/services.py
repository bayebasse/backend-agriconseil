from datetime import timedelta
from decimal import Decimal
import requests
from django.conf import settings
from django.utils import timezone
from .models import DonneeMeteo

def _fallback(commune):
    now = timezone.now()
    return DonneeMeteo.objects.create(
        commune=commune, date_heure=now,
        temperature=Decimal("31.0"), humidite=Decimal("48.0"), vent_kmh=Decimal("18.0"),
        precipitation_mm=Decimal("0.0"), probabilite_pluie=Decimal("0.0"), source="fallback"
    )

def get_local_weather(commune):
    now = timezone.now()
    existing = DonneeMeteo.objects.filter(commune=commune, date_heure__gte=now-timedelta(hours=1)).order_by("-date_heure").first()
    if existing:
        return existing
    if commune.latitude is None or commune.longitude is None:
        return _fallback(commune)
    params = {
        "latitude": float(commune.latitude), "longitude": float(commune.longitude),
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        "hourly": "precipitation_probability",
        "forecast_days": 1, "timezone": "Africa/Dakar",
    }
    try:
        response = requests.get(settings.WEATHER_API_URL, params=params, timeout=8)
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current", {})
        hourly = payload.get("hourly", {})
        probs = hourly.get("precipitation_probability") or [0]
        prob = probs[0] if probs else 0
        return DonneeMeteo.objects.create(
            commune=commune, date_heure=now,
            temperature=Decimal(str(current.get("temperature_2m", 0))),
            humidite=Decimal(str(current.get("relative_humidity_2m", 0))),
            vent_kmh=Decimal(str(current.get("wind_speed_10m", 0))),
            precipitation_mm=Decimal(str(current.get("precipitation", 0))),
            probabilite_pluie=Decimal(str(prob)), source="Open-Meteo"
        )
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return _fallback(commune)
