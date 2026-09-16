from django.core.management.base import BaseCommand
from apps.cultures.models import Region, Departement, CommuneLocalite, CultureRef
from apps.calendrier.models import Stade

class Command(BaseCommand):
    help = "Initialise les référentiels de démonstration Agri-Conseil"
    def handle(self, *args, **kwargs):
        region, _ = Region.objects.get_or_create(nom="Dakar")
        dept, _ = Departement.objects.get_or_create(region=region, nom="Rufisque")
        communes = [
            ("Tivaouane Peulh-Niaga", 14.7835, -17.2577),
            ("Niagues", 14.8363, -17.2447),
        ]
        for nom, lat, lon in communes:
            CommuneLocalite.objects.get_or_create(departement=dept, nom=nom, defaults={"latitude":lat,"longitude":lon})
        cultures = {
            "Mil": (120, 450, 650, [("Initial", 20, .35),("Développement", 35, .70),("Mi-saison", 40, 1.10),("Fin de cycle", 25, .65)]),
            "Sorgho": (120, 450, 650, [("Initial",20,.35),("Développement",35,.75),("Mi-saison",40,1.10),("Fin de cycle",25,.65)]),
            "Maïs": (120, 500, 800, [("Initial",20,.30),("Développement",35,.70),("Mi-saison",40,1.15),("Fin de cycle",25,.60)]),
            "Arachide": (120, 500, 700, [("Initial",20,.45),("Développement",35,.75),("Mi-saison",40,1.05),("Fin de cycle",25,.70)]),
            "Oignon": (120, 350, 550, [("Initial",20,.50),("Développement",35,.70),("Bulbaison",40,1.05),("Maturation",25,.75)]),
            "Riz": (120, 450, 700, [("Initial",20,1.05),("Développement",35,1.10),("Mi-saison",40,1.20),("Fin de cycle",25,.90)]),
        }
        for nom, (cycle, bmin, bmax, stages) in cultures.items():
            ref, _ = CultureRef.objects.get_or_create(nom=nom, defaults={"code":nom.lower().replace(" ","-"),"cycle_jours":cycle,"besoin_min_mm":bmin,"besoin_max_mm":bmax})
            for order, (stage, duration, kc) in enumerate(stages, 1):
                Stade.objects.update_or_create(culture=ref, ordre=order, defaults={"nom":stage,"duree_jours":duration,"kc":kc})
        self.stdout.write(self.style.SUCCESS("Référentiels Agri-Conseil initialisés."))
