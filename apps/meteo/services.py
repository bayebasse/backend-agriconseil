from datetime import datetime, timezone as dt_timezone
from decimal import Decimal


import requests
from django.conf import settings
from django.utils import timezone
from zoneinfo import ZoneInfo



DAKAR_TZ = ZoneInfo("Africa/Dakar")


def _get_region_coordinates(region_nom):
    """
    Transforme le nom de la région sénégalaise
    en coordonnées grâce à OpenWeather Geocoding.
    """

    if not settings.OPENWEATHER_API_KEY:
        raise RuntimeError(
            "OPENWEATHER_API_KEY n'est pas configurée."
        )

    params = {
        "q": f"{region_nom},SN",
        "limit": 1,
        "appid": settings.OPENWEATHER_API_KEY,
    }

    response = requests.get(
        settings.OPENWEATHER_GEOCODING_URL,
        params=params,
        timeout=8,
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        raise ValueError(
            f"Impossible de trouver les coordonnées de la région : {region_nom}"
        )

    location = results[0]

    return {
        "nom": location.get("name") or region_nom,
        "latitude": float(location["lat"]),
        "longitude": float(location["lon"]),
    }


def _get_current_weather(latitude, longitude):
    """
    Récupère la météo actuelle à partir des coordonnées.
    """

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "fr",
    }

    response = requests.get(
        settings.OPENWEATHER_WEATHER_URL,
        params=params,
        timeout=8,
    )

    response.raise_for_status()

    return response.json()


def _get_forecast(latitude, longitude):
    """
    Récupère les prévisions sur 5 jours
    avec un pas de 3 heures.
    """

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "fr",
    }

    response = requests.get(
        settings.OPENWEATHER_FORECAST_URL,
        params=params,
        timeout=8,
    )

    response.raise_for_status()

    return response.json()


def _forecast_today(forecast_data):
    """
    Garde uniquement les prévisions correspondant
    à la date actuelle au Sénégal.
    """

    today = timezone.now().astimezone(DAKAR_TZ).date()

    result = []

    for item in forecast_data.get("list", []):
        timestamp = item.get("dt")

        if not timestamp:
            continue

        forecast_datetime = datetime.fromtimestamp(
            timestamp,
            tz=dt_timezone.utc,
        ).astimezone(DAKAR_TZ)

        if forecast_datetime.date() == today:
            result.append(item)

    return result


def _calculate_today_rain(forecasts):
    """
    Détermine si une pluie est prévue aujourd'hui.

    On utilise :
    - la probabilité de précipitation (pop)
    - le volume de pluie prévu sur 3 heures (rain.3h)

    Une pluie est considérée comme prévue si :
    - pop >= 0.50
    OU
    - rain.3h > 0
    """

    if not forecasts:
        return {
            "pluie_prevue": False,
            "probabilite_pluie": 0,
            "precipitation_prevue_mm": 0,
        }

    max_probability = 0
    total_rain = Decimal("0")

    for item in forecasts:
        pop = float(item.get("pop", 0) or 0)

        probability_percent = pop * 100

        if probability_percent > max_probability:
            max_probability = probability_percent

        rain = item.get("rain", {})
        rain_3h = rain.get("3h", 0) if rain else 0

        if rain_3h:
            total_rain += Decimal(str(rain_3h))

    pluie_prevue = (
        max_probability >= 50
        or total_rain > Decimal("0")
    )

    return {
        "pluie_prevue": pluie_prevue,
        "probabilite_pluie": round(max_probability, 2),
        "precipitation_prevue_mm": round(
            float(total_rain),
            2,
        ),
    }


def _build_advice(pluie_prevue):
    """
    Conseil météo simple pour la V1.

    Aucun stade, Kc, ETo ou besoin hydrique
    n'intervient dans cette décision.
    """

    if pluie_prevue:
        return (
            "Évitez d'irriguer aujourd'hui. "
            "Une pluie est prévue dans votre région."
        )

    return (
        "Continuez à suivre votre calendrier agricole. "
        "Aucune pluie n'est prévue aujourd'hui."
    )


def get_region_weather(region):
    """
    Fonction principale utilisée par l'API.

    IMPORTANT :
    - la météo dépend uniquement de la région ;
    - aucun stade de culture n'est utilisé ;
    - aucune donnée hydrique n'est utilisée.
    """

    if not region:
        raise ValueError(
            "La région de la culture est obligatoire."
        )

    region_nom = region.nom.strip()

    coordinates = _get_region_coordinates(region_nom)

    current_data = _get_current_weather(
        coordinates["latitude"],
        coordinates["longitude"],
    )

    forecast_data = _get_forecast(
        coordinates["latitude"],
        coordinates["longitude"],
    )

    today_forecasts = _forecast_today(
        forecast_data
    )

    rain_data = _calculate_today_rain(
        today_forecasts
    )

    current_main = current_data.get("main", {})
    current_wind = current_data.get("wind", {})
    current_rain = current_data.get("rain", {})

    current_precipitation = (
        current_rain.get("1h", 0)
        if current_rain
        else 0
    )

    wind_ms = float(
        current_wind.get("speed", 0) or 0
    )

    wind_kmh = wind_ms * 3.6

    weather_description = ""

    weather_list = current_data.get("weather", [])

    if weather_list:
        weather_description = (
            weather_list[0].get("description", "")
        )

    return {
        "region": region_nom,
        "localisation": region_nom,

        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],

        "temperature": round(
            float(current_main.get("temp", 0)),
            1,
        ),

        "humidite": round(
            float(current_main.get("humidity", 0)),
            1,
        ),

        "vent_kmh": round(
            wind_kmh,
            1,
        ),

        "precipitation_mm": round(
            float(current_precipitation),
            2,
        ),

        "probabilite_pluie": rain_data[
            "probabilite_pluie"
        ],

        "precipitation_prevue_mm": rain_data[
            "precipitation_prevue_mm"
        ],

        "pluie_prevue": rain_data[
            "pluie_prevue"
        ],

        "description": weather_description,

        "conseil": _build_advice(
            rain_data["pluie_prevue"]
        ),

        "source": "OpenWeather",

        "prevision": {
            "nombre_points": len(
                forecast_data.get("list", [])
            ),
            "aujourd_hui": len(
                today_forecasts
            ),
        },
    }