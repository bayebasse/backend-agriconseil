from decimal import Decimal
import requests
from django.conf import settings
from apps.calendrier.services import current_stage
from apps.meteo.services import get_local_weather

def estimate_eto(meteo):
    """Prototype V1: proxy climatique explicite, à remplacer par une ETo FAO-56 complète si nécessaire."""
    temp = Decimal(str(meteo.temperature))
    rh = Decimal(str(meteo.humidite))
    wind = Decimal(str(meteo.vent_kmh))
    proxy = (temp * Decimal("0.10")) + ((Decimal("100") - rh) * Decimal("0.025")) + (wind * Decimal("0.02"))
    return max(Decimal("1.00"), proxy.quantize(Decimal("0.01")))

def build_hydric_advice(culture_suivie):
    meteo = get_local_weather(culture_suivie.commune)
    stage = current_stage(culture_suivie)
    if not stage:
        return {"meteo": meteo, "stage": None, "eto": None, "etc": None, "deficit": None, "conseil": "Le stade ne peut pas encore être déterminé."}
    eto = estimate_eto(meteo)
    etc = (Decimal(str(stage.kc)) * eto).quantize(Decimal("0.01"))
    pluie = Decimal(str(meteo.precipitation_mm))
    deficit = (etc - pluie).quantize(Decimal("0.01"))
    if deficit <= 0:
        conseil = "Les précipitations mesurées couvrent l'estimation du besoin de la période ; surveillez l'évolution avant d'irriguer."
    elif deficit < Decimal("3"):
        conseil = "Le déficit estimé est faible ; surveillez la parcelle et ajustez l'irrigation selon son état réel."
    else:
        conseil = "Un déficit hydrique est estimé ; une irrigation peut être envisagée selon l'état réel de la parcelle."
    return {"meteo": meteo, "stage": stage, "eto": eto, "etc": etc, "deficit": deficit, "conseil": conseil}
