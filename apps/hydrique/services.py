
from decimal import Decimal
import requests
def estimate_eto(meteo):
    """
    Prototype V1.

    Cette fonction reste disponible pour le futur module hydrique.
    Elle ne dépend pas du service météo.
    """

    temp = Decimal(str(meteo["temperature"]))
    rh = Decimal(str(meteo["humidite"]))
    wind = Decimal(str(meteo["vent_kmh"]))

    proxy = (
        (temp * Decimal("0.10"))
        + ((Decimal("100") - rh) * Decimal("0.025"))
        + (wind * Decimal("0.02"))
    )

    return max(
        Decimal("1.00"),
        proxy.quantize(Decimal("0.01"))
    )


def build_hydric_advice(culture_suivie):
    """
    Module hydrique séparé.

    IMPORTANT :
    - aucun appel au service météo ;
    - aucun calcul de stade ;
    - aucune dépendance au calendrier ;
    - aucune dépendance à Kc pour le moment.

    Le calcul hydrique complet sera branché séparément
    lorsque les données hydriques seront définitivement définies.
    """

    return {
        "meteo": None,
        "stage": None,
        "eto": None,
        "etc": None,
        "deficit": None,
        "conseil": (
            "Le calcul hydrique détaillé sera disponible "
            "lorsque les données hydriques seront configurées."
        ),
    }

