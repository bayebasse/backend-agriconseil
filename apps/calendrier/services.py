#versiion 1.0
# from datetime import timedelta
# from django.utils import timezone
# from .models import CalendrierAgricole, OperationAgricole, Stade

# DEFAULT_OPERATIONS = {
#     "Mil": [("Surveillance", "Observer régulièrement l’état de la culture."), ("Désherbage", "Maintenir la parcelle propre selon le stade."), ("Fertilisation", "Appliquer selon la recommandation agronomique locale.")],
#     "Maïs": [("Désherbage", "Contrôler les adventices précocement."), ("Fertilisation", "Fractionner les apports selon le calendrier."), ("Surveillance", "Surveiller l’état foliaire et hydrique.")],
#     "Arachide": [("Désherbage", "Contrôler les adventices."), ("Surveillance", "Surveiller les signes de stress hydrique."), ("Récolte", "Préparer la récolte lorsque la maturité est atteinte.")],
# }

# def ensure_calendar(culture_suivie):
#     calendar, _ = CalendrierAgricole.objects.get_or_create(culture_suivie=culture_suivie)
#     calendar.operations.all().delete()
#     stages = list(Stade.objects.filter(culture=culture_suivie.culture).order_by("ordre"))
#     cursor = culture_suivie.date_semis
#     ops = DEFAULT_OPERATIONS.get(culture_suivie.culture.nom, [("Suivi cultural", "Observer et suivre la culture selon son stade.")])
#     for idx, stage in enumerate(stages):
#         start = cursor
#         end = cursor + timedelta(days=max(stage.duree_jours - 1, 0))
#         if idx < len(ops):
#             nom, desc = ops[idx]
#             OperationAgricole.objects.create(calendrier=calendar, stade=stage, nom=nom, description=desc, date_debut=start, date_fin=end)
#         cursor = end + timedelta(days=1)
#     return calendar

# def current_stage(culture_suivie):
#     days = (timezone.localdate() - culture_suivie.date_semis).days
#     if days < 0:
#         return None
#     cursor = 0
#     stages = Stade.objects.filter(culture=culture_suivie.culture).order_by("ordre")
#     for stage in stages:
#         if cursor <= days < cursor + stage.duree_jours:
#             return stage
#         cursor += stage.duree_jours
#     return stages.last()


#version 2.0  normal baye basse
from datetime import timedelta

from django.utils import timezone

from .models import (
    CalendrierAgricole,
    OperationAgricole,
    Stade,
    StadeReference,
    RegleOperationAgricole,
)


def get_referentiel(culture_suivie):
    return culture_suivie.culture.referentiel_agronomique


def build_stages(culture_suivie):
    """
    Transforme les stades agronomiques de référence
    en stades utilisables par le moteur de calcul.
    """

    referentiel = get_referentiel(culture_suivie)

    Stade.objects.filter(
        culture=culture_suivie.culture
    ).delete()

    stages = []

    cursor = culture_suivie.date_semis

    for reference in StadeReference.objects.filter(
        referentiel=referentiel
    ).order_by("ordre"):

        date_debut = cursor

        date_fin = (
            cursor
            + timedelta(days=reference.duree_jours - 1)
        )

        stage = Stade.objects.create(
            culture=culture_suivie.culture,
            reference=reference,
            nom=reference.nom,
            ordre=reference.ordre,
            duree_jours=reference.duree_jours,
            date_debut=date_debut,
            date_fin=date_fin,
        )

        stages.append(stage)

        cursor = date_fin + timedelta(days=1)

    return stages


def get_cycle_end_date(culture_suivie):
    referentiel = get_referentiel(culture_suivie)

    if not referentiel.cycle_max_jours:
        return None

    return (
        culture_suivie.date_semis
        + timedelta(days=referentiel.cycle_max_jours - 1)
    )


def get_trigger_date(
    rule,
    culture_suivie,
    stages,
):
    if rule.declencheur == "semis":
        return culture_suivie.date_semis

    if rule.declencheur == "fin_cycle":
        return get_cycle_end_date(culture_suivie)

    if not rule.stade_reference:
        return None

    stage = next(
        (
            item
            for item in stages
            if item.reference_id == rule.stade_reference_id
        ),
        None,
    )

    if not stage:
        return None

    if rule.declencheur == "debut_stade":
        return stage.date_debut

    if rule.declencheur == "fin_stade":
        return stage.date_fin

    return None


def ensure_calendar(culture_suivie):

    calendar, _ = CalendrierAgricole.objects.get_or_create(
        culture_suivie=culture_suivie
    )

    calendar.operations.all().delete()

    stages = build_stages(culture_suivie)

    rules = (
        RegleOperationAgricole.objects
        .filter(
            culture=culture_suivie.culture,
            actif=True,
        )
        .select_related("stade_reference")
        .order_by("ordre", "id")
    )

    for rule in rules:

        trigger_date = get_trigger_date(
            rule,
            culture_suivie,
            stages,
        )

        if not trigger_date:
            continue

        date_debut = (
            trigger_date
            + timedelta(days=rule.decalage_jours)
        )

        date_fin = (
            date_debut
            + timedelta(days=rule.duree_jours - 1)
        )

        stade = None

        if rule.stade_reference_id:
            stade = next(
                (
                    item
                    for item in stages
                    if item.reference_id
                    == rule.stade_reference_id
                ),
                None,
            )

        OperationAgricole.objects.create(
            calendrier=calendar,
            stade=stade,
            nom=rule.nom,
            description=rule.description,
            date_debut=date_debut,
            date_fin=date_fin,
        )

    return calendar


def current_stage(culture_suivie):

    stages = Stade.objects.filter(
        culture=culture_suivie.culture
    ).order_by("ordre")

    if not stages.exists():
        stages = build_stages(culture_suivie)

    today = timezone.localdate()

    for stage in stages:

        if (
            stage.date_debut
            <= today
            <= stage.date_fin
        ):
            return stage

    return stages.last()


def next_operation(culture_suivie):

    calendar = ensure_calendar(culture_suivie)

    today = timezone.localdate()

    return (
        calendar.operations
        .filter(date_fin__gte=today)
        .order_by("date_debut")
        .first()
    )