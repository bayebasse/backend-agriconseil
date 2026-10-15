"""Indicative pre-harvest information based only on recorded data."""

import logging
import calendar as month_calendar
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlparse

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from apps.calendrier.models import OperationAgricole
from apps.calendrier.services import current_stage, ensure_calendar
from apps.meteo.services import get_region_weather
from apps.ia.yield_advice import analyze_agricultural_context
from .models import ReferenceRendement, RecolteReelle


logger = logging.getLogger(__name__)


def _get_reference(culture_suivie):
    try:
        return culture_suivie.culture.referentiel_agronomique
    except ObjectDoesNotExist:
        return None


def _automatic_official_statistic(reference):
    """Trust only the imported ANSD/DAPSA 2025/26 campaign aggregates."""
    host = (urlparse(reference.source_url).hostname or "").lower()
    return (
        reference.culture.code in {
            "mil", "arachide", "niebe", "manioc", "pasteque",
            "sorgho", "mais", "riz",
        }
        and host in {"ansd.sn", "www.ansd.sn"}
        and reference.source_titre.startswith(
            "DAPSA/ANSD - Resultats definitifs campagne agricole 2025/2026"
        )
        and reference.source_annee == 2026
        and reference.rendement_unite == "kg_ha"
        and reference.rendement_moyen is not None
        and reference.rendement_moyen > 0
        and reference.statut_validation != "REJETE"
    )


def _regional_statistic_matches(reference, region_name):
    prefix = "Region administrative de "
    label = reference.zone_agroecologique
    if not label.startswith(prefix):
        return False
    reference_region = label[len(prefix):].split(" (", 1)[0].strip()
    return reference_region.casefold() == region_name.strip().casefold()


def _matching_yield_reference(culture_suivie, candidates=None):
    references = candidates if candidates is not None else ReferenceRendement.objects.filter(
        culture_id=culture_suivie.culture_id,
    ).select_related("culture")

    candidates = []
    for item in references:
        if item.variete and item.variete != culture_suivie.variete:
            continue
        if item.systeme_culture and item.systeme_culture != culture_suivie.systeme_culture:
            continue
        auto_validated = _automatic_official_statistic(item)
        if not item.valide and not auto_validated:
            continue
        if item.zone_agroecologique and not (
            auto_validated
            and _regional_statistic_matches(item, culture_suivie.region.nom)
        ):
            continue
        if item.age_arbres_min_annees is not None:
            age = culture_suivie.age_arbres_annees
            if age is None or age < item.age_arbres_min_annees:
                continue
        if item.age_arbres_max_annees is not None:
            age = culture_suivie.age_arbres_annees
            if age is None or age > item.age_arbres_max_annees:
                continue
        # Prefer an exact administrative-region statistic, then the national
        # aggregate. Neither one is treated as a parcel-level yield forecast.
        regional = int(_regional_statistic_matches(item, culture_suivie.region.nom))
        specificity = int(bool(item.variete)) + int(bool(item.systeme_culture))
        candidates.append((regional, specificity, item.pk, item))
    return max(candidates, default=(None, None, None, None))[3]


def estimated_production_kg(culture_suivie, yield_reference=None):
    """Return the official indicative production amount, if the data supports it."""
    reference = yield_reference or _matching_yield_reference(culture_suivie)
    if not (
        reference
        and _automatic_official_statistic(reference)
        and reference.rendement_moyen is not None
        and reference.rendement_unite in {"kg_ha", "tonne_ha"}
        and culture_suivie.unite_superficie in {"ha", "m2"}
    ):
        return None
    multiplier = Decimal("1000") if reference.rendement_unite == "tonne_ha" else Decimal("1")
    yield_kg_ha = Decimal(reference.rendement_moyen) * multiplier
    area_ha = Decimal(culture_suivie.superficie)
    if culture_suivie.unite_superficie == "m2":
        area_ha /= Decimal("10000")
    return (yield_kg_ha * area_ha).quantize(Decimal("0.001"))


def _reference_cycle(reference, yield_reference):
    if yield_reference:
        if yield_reference.type_cycle == "perenne":
            return "perenne", yield_reference.cycle_min, yield_reference.cycle_max, yield_reference.cycle_unite
        if yield_reference.type_cycle == "annuelle" and yield_reference.cycle_min is not None:
            return "annuelle", yield_reference.cycle_min, yield_reference.cycle_max, yield_reference.cycle_unite
    if reference:
        return "annuelle" if reference.type_cycle == "annuelle" else "perenne", reference.cycle_min_jours, reference.cycle_max_jours, "jours"
    return None, None, None, None


def _add_cycle_duration(start, duration, unit):
    if unit == "jours":
        return start + timedelta(days=duration - 1)
    months = duration if unit == "mois" else duration * 12 if unit == "annees" else None
    if months is None:
        return None
    month_index = start.year * 12 + start.month - 1 + months
    year, zero_month = divmod(month_index, 12)
    month = zero_month + 1
    day = min(start.day, month_calendar.monthrange(year, month)[1])
    from datetime import date
    return date(year, month, day) - timedelta(days=1)


def _harvest_period(culture_suivie, reference, yield_reference=None):
    cycle_type, minimum, maximum, unit = _reference_cycle(reference, yield_reference)
    source_is_yield_ref = bool(
        yield_reference
        and yield_reference.type_cycle == "annuelle"
        and yield_reference.cycle_min is not None
    )
    if yield_reference and yield_reference.type_cycle == "perenne":
        return None, None, "La référence décrit une production pérenne, sans cycle de récolte datable depuis le semis."
    indicative_fao_cycle = bool(
        reference
        and reference.source == "FAO"
        and (urlparse(reference.source_url).hostname or "").lower() in {"fao.org", "www.fao.org"}
        and reference.cycle_min_jours
        and reference.cycle_max_jours
    )
    if reference is None and not source_is_yield_ref:
        return None, None, "Aucun référentiel agronomique n'est associé à cette culture."

    if not source_is_yield_ref and not reference.valide and not indicative_fao_cycle:
        return None, None, "Le référentiel agronomique n'est pas validé."

    if source_is_yield_ref and not (yield_reference.source_titre.strip() or yield_reference.source_url.strip()):
        return None, None, "La source de la durée de cycle n'est pas identifiable."
    if not source_is_yield_ref and reference and not reference.source_reference.strip() and not reference.source_url.strip():
        return None, None, "La source de la durée de cycle n'est pas identifiable."

    if cycle_type != "annuelle":
        return None, None, (
            "Le cycle enregistré ne permet pas de dater la récolte d'une culture pérenne."
        )

    if not minimum or not maximum or minimum > maximum or not unit:
        return None, None, "La plage ou l'unité du cycle annuel est absente ou incohérente."

    start = _add_cycle_duration(culture_suivie.date_semis, minimum, unit)
    end = _add_cycle_duration(culture_suivie.date_semis, maximum, unit)
    if start is None or end is None:
        return None, None, "L'unité de durée du cycle n'est pas prise en charge."
    return start, end, None


def _yield_reference_payload(reference):
    if reference is None:
        return None
    automatic_validation = _automatic_official_statistic(reference)
    if automatic_validation and reference.zone_agroecologique.startswith(
        "Region administrative de "
    ):
        statistical_scope = "Moyenne régionale ANSD — " + reference.zone_agroecologique[
            len("Region administrative de "):].split(" (", 1)[0]
    elif automatic_validation:
        statistical_scope = "Moyenne nationale ANSD"
    else:
        statistical_scope = None
    return {
        "type_cycle": reference.type_cycle or None,
        "variete": reference.variete or None,
        "zone_agroecologique": reference.zone_agroecologique or None,
        "systeme_culture": reference.systeme_culture or None,
        "cycle": {
            "minimum": reference.cycle_min,
            "maximum": reference.cycle_max,
            "unite": reference.cycle_unite or None,
        },
        "age_arbres_annees": {
            "minimum": reference.age_arbres_min_annees,
            "maximum": reference.age_arbres_max_annees,
        },
        "rendement": {
            "minimum": str(reference.rendement_min) if reference.rendement_min is not None else None,
            "moyen": str(reference.rendement_moyen) if reference.rendement_moyen is not None else None,
            "maximum": str(reference.rendement_max) if reference.rendement_max is not None else None,
            "unite": reference.rendement_unite or None,
            "periode": reference.periode_rendement or None,
        },
        "besoin_eau_mm": {
            "minimum": str(reference.besoin_eau_min_mm) if reference.besoin_eau_min_mm is not None else None,
            "maximum": str(reference.besoin_eau_max_mm) if reference.besoin_eau_max_mm is not None else None,
        },
        "sensibilite_secheresse": reference.sensibilite_secheresse or None,
        "source": {
            "titre": reference.source_titre or None,
            "url": reference.source_url or None,
            "annee": reference.source_annee,
            "organisme": reference.source_organisme or None,
            "page": reference.source_page or None,
            "conditions_mesure": reference.conditions_mesure or None,
        },
        "valide": reference.valide or _automatic_official_statistic(reference),
        "validation_automatique": automatic_validation,
        "portee_statistique": statistical_scope,
    }


def _historical_observations(culture_suivie):
    if culture_suivie.unite_superficie not in {"ha", "m2"}:
        return []
    harvests = RecolteReelle.objects.filter(
        culture_suivie__agriculteur_id=culture_suivie.agriculteur_id,
        culture_suivie__culture_id=culture_suivie.culture_id,
        culture_suivie__region_id=culture_suivie.region_id,
        culture_suivie__type_sol=culture_suivie.type_sol,
        culture_suivie__variete=culture_suivie.variete,
        culture_suivie__systeme_culture=culture_suivie.systeme_culture,
        culture_suivie__unite_superficie=culture_suivie.unite_superficie,
    ).exclude(culture_suivie_id=culture_suivie.pk).select_related("culture_suivie")
    if culture_suivie.age_arbres_annees is not None:
        harvests = harvests.filter(
            culture_suivie__age_arbres_annees=culture_suivie.age_arbres_annees
        )
    surface_ha = Decimal(str(culture_suivie.superficie))
    if culture_suivie.unite_superficie == "m2":
        surface_ha /= Decimal("10000")
    if surface_ha <= 0:
        return []
    observations = []
    for harvest in harvests.order_by("-date_recolte", "-id")[:5]:
        quantity_kg = Decimal(harvest.quantite)
        if harvest.unite == "tonne":
            quantity_kg *= Decimal("1000")
        observations.append({
            "date": harvest.date_recolte.isoformat(),
            "rendement_observe_kg_ha": str((quantity_kg / surface_ha).quantize(Decimal("0.001"))),
            "source": "récolte réelle comparable du même agriculteur",
        })
    return observations


def _weather(culture_suivie):
    try:
        weather = get_region_weather(culture_suivie.region)
        if weather is None:
            return None, "Le service météo n'a retourné aucune donnée exploitable."
        return weather, None
    except Exception:
        logger.exception(
            "Météo indisponible pour la culture suivie %s",
            culture_suivie.pk,
        )
        return None, "Le service météo est indisponible pour le moment."


def _stage_payload(stage):
    if stage is None:
        return None
    return {
        "id": stage.pk,
        "nom": stage.nom,
        "ordre": stage.ordre,
        "duree_jours": stage.duree_jours,
        "date_debut": stage.date_debut,
        "date_fin": stage.date_fin,
        "kc": stage.reference.kc,
        "description": stage.reference.description,
    }


def _reference_payload(reference):
    if reference is None:
        return None
    return {
        "type_cycle": reference.type_cycle,
        "cycle_min_jours": reference.cycle_min_jours,
        "cycle_max_jours": reference.cycle_max_jours,
        "besoin_eau_min_mm": reference.besoin_eau_min_mm,
        "besoin_eau_max_mm": reference.besoin_eau_max_mm,
        "sensibilite_secheresse": reference.sensibilite_secheresse,
        "source": reference.source,
        "source_reference": reference.source_reference,
        "source_url": reference.source_url or None,
        "zone_agroecologique": reference.zone_agroecologique or None,
        "valide": reference.valide,
    }


def _weather_context(weather):
    """Keep only weather measurements and their time coverage for Gemini."""
    if not weather:
        return None
    return {
        key: weather.get(key)
        for key in (
            "temperature",
            "humidite",
            "vent_kmh",
            "precipitation_mm",
            "probabilite_pluie",
            "precipitation_prevue_mm",
            "pluie_prevue",
            "source",
        )
    } | {
        "periode": {
            "conditions_actuelles": timezone.now().isoformat(),
            "prevision_points_jour": (weather.get("prevision") or {}).get("aujourd_hui", 0),
        }
    }


def _calendar_and_stage(culture_suivie, reference):
    if reference is None:
        return None, None, None
    indicative_fao_cycle = bool(
        reference.source == "FAO"
        and (urlparse(reference.source_url).hostname or "").lower() in {"fao.org", "www.fao.org"}
        and reference.cycle_min_jours
        and reference.cycle_max_jours
        and reference.stades.exists()
    )
    if not reference.valide and not indicative_fao_cycle:
        return None, None, "Le référentiel n'est pas validé ; le stade et les opérations ne sont pas personnalisés."
    if reference.type_cycle != "annuelle":
        return None, None, "Le modèle ne contient pas les données de plantation et de stades adaptées aux cultures pérennes."
    try:
        calendar = ensure_calendar(culture_suivie)
        stage = current_stage(culture_suivie)
        if stage:
            stage_limit = None
        elif timezone.localdate() < culture_suivie.date_semis:
            stage_limit = "Le semis n'a pas encore eu lieu ; le stade sera affiché à partir de cette date."
        else:
            stage_limit = "Aucun stade actuel calculable à partir des références enregistrées."
        return calendar, stage, stage_limit
    except Exception:
        logger.exception(
            "Calendrier indisponible pour la culture suivie %s",
            culture_suivie.pk,
        )
        return None, None, "Le calendrier cultural n'a pas pu être calculé."


def _recommendations(calendar, weather):
    recommendations = []
    today = timezone.localdate()

    if calendar:
        operation = (
            OperationAgricole.objects
            .filter(calendrier=calendar, date_fin__gte=today)
            .order_by("date_debut", "id")
            .first()
        )
        if operation:
            recommendations.append({
                "type": "calendrier",
                "texte": f"Préparez l'opération « {operation.nom} » prévue au calendrier.",
                "date": operation.date_debut,
                "source": "règle du calendrier agricole",
            })

    # The existing weather advice treats an empty forecast as no rain. Only
    # use it when the provider actually returned forecast points for today.
    if weather and weather.get("prevision", {}).get("aujourd_hui", 0) > 0:
        recommendations.append({
            "type": "meteo",
            "texte": weather["conseil"],
            "date": today,
            "source": "règle météo existante appliquée aux prévisions régionales OpenWeather",
        })

    return recommendations


def _cycle_progress(culture_suivie, reference, yield_reference):
    cycle_type, minimum, maximum, unit = _reference_cycle(reference, yield_reference)
    if cycle_type != "annuelle" or not minimum or not maximum or unit != "jours":
        return None

    average_days = (minimum + maximum) / 2
    elapsed_days = (timezone.localdate() - culture_suivie.date_semis).days
    percentage = max(0, min(100, round(max(0, elapsed_days) / average_days * 100)))
    return {
        "pourcentage": percentage,
        "jours_ecoules": max(0, elapsed_days),
        "duree_moyenne_jours": round(average_days),
        "indicatif": bool(reference and not reference.valide),
    }


def build_yield_prediction(culture_suivie):
    """Build a transparent estimate; never infer a yield without a reference."""

    reference = _get_reference(culture_suivie)
    yield_reference = _matching_yield_reference(culture_suivie)
    harvest_start, harvest_end, cycle_limit = _harvest_period(
        culture_suivie, reference, yield_reference
    )
    weather, weather_limit = _weather(culture_suivie)
    calendar, stage, calendar_limit = _calendar_and_stage(
        culture_suivie, reference
    )
    cycle_progress = _cycle_progress(culture_suivie, reference, yield_reference)

    references = []
    if reference is not None and reference.valide:
        references = [{
            "source": reference.source,
            "reference": reference.source_reference,
            "url": reference.source_url or None,
            "zone_agroecologique": reference.zone_agroecologique or None,
            "valide": reference.valide,
        }]
    if yield_reference:
        references.append({
            "source": yield_reference.source_organisme or "Source documentaire",
            "reference": yield_reference.source_titre,
            "url": yield_reference.source_url or None,
            "annee": yield_reference.source_annee,
            "page": yield_reference.source_page or None,
            "validation_automatique": _automatic_official_statistic(yield_reference),
            "variete": yield_reference.variete or None,
            "zone_agroecologique": yield_reference.zone_agroecologique or None,
            "systeme_culture": yield_reference.systeme_culture or None,
            "valide": yield_reference.valide or _automatic_official_statistic(yield_reference),
        })

    # Report the arithmetic benchmark separately from a real harvest forecast.
    reference_yield_kg_ha = None
    reference_production_kg = None
    if yield_reference and yield_reference.rendement_moyen is not None:
        if yield_reference.rendement_unite in {"kg_ha", "tonne_ha"}:
            multiplier = Decimal("1000") if yield_reference.rendement_unite == "tonne_ha" else Decimal("1")
            reference_yield_kg_ha = Decimal(yield_reference.rendement_moyen) * multiplier
            if culture_suivie.unite_superficie in {"ha", "m2"}:
                area_ha = Decimal(culture_suivie.superficie)
                if culture_suivie.unite_superficie == "m2":
                    area_ha /= Decimal("10000")
                reference_production_kg = (reference_yield_kg_ha * area_ha).quantize(Decimal("0.001"))

    is_official_yield_estimate = bool(
        yield_reference
        and _automatic_official_statistic(yield_reference)
        and reference_yield_kg_ha is not None
    )

    missing = []
    limits = [
        "Aucune methode documentee ne permet d'ajuster le rendement aux conditions de la parcelle.",
        "Le module hydrique ne calcule actuellement ni ETo, ni ETc, ni déficit hydrique.",
    ]
    if yield_reference is None:
        limits.insert(0, "Aucune référence de rendement validée et adaptée à cette culture n'est disponible.")
        missing.append("Référence de rendement validée et adaptée absente ou non vérifiable.")
    else:
        missing.append("Méthode d'ajustement du rendement vérifiée absente.")
        if not _regional_statistic_matches(yield_reference, culture_suivie.region.nom):
            limits.append("Le repere affiche est une moyenne nationale, faute de statistique regionale correspondante.")
    if not culture_suivie.unite_superficie:
        limits.append("L'unité de superficie n'est pas renseignée ; aucune quantité totale ne peut être calculée.")
        missing.append("Unité de superficie de la parcelle.")
    if cycle_limit:
        limits.append(cycle_limit)
        missing.append(cycle_limit)
    if weather_limit:
        limits.append(weather_limit)
        missing.append(weather_limit)
    if calendar_limit:
        limits.append(calendar_limit)
        missing.append(calendar_limit)
    if reference is None:
        missing.append("Référentiel agronomique absent.")
    indicative_fao_cycle = bool(
        reference
        and reference.source == "FAO"
        and (urlparse(reference.source_url).hostname or "").lower() in {"fao.org", "www.fao.org"}
        and reference.cycle_min_jours
        and reference.cycle_max_jours
    )
    if reference and indicative_fao_cycle and not reference.valide:
        limits.append("Le calendrier FAO est indicatif et reste a confirmer selon la variete et les conditions locales.")
    if (
        not reference
        or (not reference.valide and not indicative_fao_cycle)
        or (
            not reference.source_reference.strip()
            and not reference.source_url.strip()
        )
    ):
        missing.append("Cycle de récolte vérifié et identifiable.")
    missing.append("Calcul hydrique valide (ETo, ETc et deficit hydrique).")

    recommendations = _recommendations(calendar, weather)
    weather_risk_status = "non_evalue" if weather else "indisponible"

    # Keep the external context minimal: no farmer/account/plot identifiers or
    # coordinates. Only verified references and explicitly recorded units are sent.
    ai_context = {
        "culture": culture_suivie.culture.nom,
        "date_semis": culture_suivie.date_semis,
        "cycle_agronomique": (
            _reference_payload(reference)
            if reference and reference.valide
            else None
        ),
        "stade_cultural": (
            {"nom": stage.nom, "description": stage.reference.description}
            if stage else None
        ),
        "superficie": {
            "valeur": str(culture_suivie.superficie),
            "unite": culture_suivie.unite_superficie or None,
            "variete": culture_suivie.variete or None,
            "systeme_culture": culture_suivie.systeme_culture or None,
            "age_arbres_annees": culture_suivie.age_arbres_annees,
        },
        # No validated mapping exists from the administrative region to an
        # agroecological zone; do not present a reference zone as parcel data.
        "zone_agroecologique_parcelle": None,
        "meteo": _weather_context(weather),
        "reference_rendement": _yield_reference_payload(yield_reference),
        "recoltes_reelles_comparables": _historical_observations(culture_suivie),
        "limites": list(dict.fromkeys(missing)),
    }
    ai_analysis = analyze_agricultural_context(ai_context)

    harvest_explanation = None
    if is_official_yield_estimate:
        if reference_production_kg is None:
            harvest_explanation = "La récolte totale sera calculée lorsque la superficie sera renseignée."
        else:
            total_kg = f"{int(reference_production_kg.quantize(Decimal('1'))):,}".replace(",", " ")
            harvest_explanation = (
                f"À la fin du cycle, votre récolte totale est estimée à environ {total_kg} kg."
            )

    return {
        "culture_suivie_id": culture_suivie.pk,
        "culture": culture_suivie.culture.nom,
        "statut": "prevision_indicative" if is_official_yield_estimate else "rendement_indisponible",
        "methode": (
            "Moyenne officielle de la derniere campagne appliquee a la superficie."
            if is_official_yield_estimate else
            "Aucune moyenne officielle exploitable pour estimer cette culture."
            if yield_reference else
            "Aucune estimation chiffree : les donnees de rendement verifiees sont absentes."
        ),
        "superficie": str(culture_suivie.superficie),
        "unite_superficie": culture_suivie.unite_superficie or None,
        "date_semis": culture_suivie.date_semis,
        "type_cycle": (
            (yield_reference.type_cycle or (reference.type_cycle if reference else None))
            if yield_reference else (reference.type_cycle if reference else None)
        ),
        "caracteristiques_agronomiques": _reference_payload(reference),
        "rendement_reference": _yield_reference_payload(yield_reference),
        "stade_actuel": _stage_payload(stage),
        "recolte_prevue": {
            "date_debut": harvest_start,
            "date_fin": harvest_end,
            "statut": "indicative" if harvest_start and harvest_end else "indisponible",
            "raison_indisponible": cycle_limit,
            "source": (
                (
                    yield_reference.source_titre or yield_reference.source_url
                    if yield_reference else
                    reference.source_reference or reference.source_url
                    if reference else None
                )
            ),
        },
        "rendement_estime_kg_ha": reference_yield_kg_ha if is_official_yield_estimate else None,
        "quantite_totale_estimee_kg": reference_production_kg if is_official_yield_estimate else None,
        "explication_prevision": harvest_explanation,
        "avancement_cycle": cycle_progress,
        "rendement_reference_kg_ha": reference_yield_kg_ha,
        "production_reference_kg": reference_production_kg,
        "meteo": weather,
        "risques": {
            "meteorologique": {
                "statut": weather_risk_status,
                "raison": (
                    "Les données météo sont restituées, mais aucun seuil de risque cultural validé n'est configuré."
                    if weather else weather_limit or "Aucune donnée météo disponible."
                ),
            },
            "hydrique": {
                "statut": "indisponible",
                "raison": "ETo, ETc et déficit hydrique ne sont pas calculés par le module actuel.",
            },
        },
        "facteurs_favorables": [],
        "facteurs_defavorables": [],
        "recommandations": recommendations,
        "analyse_ia": ai_analysis,
        "references": references,
        "calcule_le": timezone.now(),
        "limites": limits,
        "donnees_manquantes": list(dict.fromkeys(missing)),
    }
