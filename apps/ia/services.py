import base64
from django.conf import settings
import requests
from .models import AnalyseIA


def analyze_photo(photo):
    """Connecteur vision optionnel.

    Un vrai modèle de vision doit être configuré via AI_API_URL/AI_API_KEY.
    Le backend ne fabrique jamais un diagnostic à partir du nom de fichier.
    """
    if not settings.AI_API_URL:
        raise RuntimeError(
            "Le service IA n'est pas configuré. Définissez AI_API_URL (et AI_API_KEY si nécessaire) dans .env."
        )

    with photo.image.open("rb") as handle:
        image_b64 = base64.b64encode(handle.read()).decode("ascii")

    headers = {"Content-Type": "application/json"}
    if settings.AI_API_KEY:
        headers["Authorization"] = f"Bearer {settings.AI_API_KEY}"
    payload = {
        "image_base64": image_b64,
        "filename": photo.image.name,
        "task": "Analyse agricole d'une photo de feuille ou de plante. Retourner probleme, confiance, resultat, conseil.",
    }
    response = requests.post(settings.AI_API_URL, json=payload, headers=headers, timeout=45)
    response.raise_for_status()
    data = response.json()
    analysis, _ = AnalyseIA.objects.update_or_create(
        photo=photo,
        defaults={
            "probleme": str(data.get("probleme", "Problème non déterminé")),
            "confiance": data.get("confiance"),
            "resultat": str(data.get("resultat", "Analyse reçue du service IA.")),
            "conseil": str(data.get("conseil", "Consultez un professionnel si les symptômes persistent.")),
        },
    )
    return analysis
