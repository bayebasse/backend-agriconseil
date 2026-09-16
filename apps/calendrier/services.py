from datetime import timedelta
from django.utils import timezone
from .models import CalendrierAgricole, OperationAgricole, Stade

DEFAULT_OPERATIONS = {
    "Mil": [("Surveillance", "Observer régulièrement l’état de la culture."), ("Désherbage", "Maintenir la parcelle propre selon le stade."), ("Fertilisation", "Appliquer selon la recommandation agronomique locale.")],
    "Maïs": [("Désherbage", "Contrôler les adventices précocement."), ("Fertilisation", "Fractionner les apports selon le calendrier."), ("Surveillance", "Surveiller l’état foliaire et hydrique.")],
    "Arachide": [("Désherbage", "Contrôler les adventices."), ("Surveillance", "Surveiller les signes de stress hydrique."), ("Récolte", "Préparer la récolte lorsque la maturité est atteinte.")],
}

def ensure_calendar(culture_suivie):
    calendar, _ = CalendrierAgricole.objects.get_or_create(culture_suivie=culture_suivie)
    calendar.operations.all().delete()
    stages = list(Stade.objects.filter(culture=culture_suivie.culture).order_by("ordre"))
    cursor = culture_suivie.date_semis
    ops = DEFAULT_OPERATIONS.get(culture_suivie.culture.nom, [("Suivi cultural", "Observer et suivre la culture selon son stade.")])
    for idx, stage in enumerate(stages):
        start = cursor
        end = cursor + timedelta(days=max(stage.duree_jours - 1, 0))
        if idx < len(ops):
            nom, desc = ops[idx]
            OperationAgricole.objects.create(calendrier=calendar, stade=stage, nom=nom, description=desc, date_debut=start, date_fin=end)
        cursor = end + timedelta(days=1)
    return calendar

def current_stage(culture_suivie):
    days = (timezone.localdate() - culture_suivie.date_semis).days
    if days < 0:
        return None
    cursor = 0
    stages = Stade.objects.filter(culture=culture_suivie.culture).order_by("ordre")
    for stage in stages:
        if cursor <= days < cursor + stage.duree_jours:
            return stage
        cursor += stage.duree_jours
    return stages.last()
