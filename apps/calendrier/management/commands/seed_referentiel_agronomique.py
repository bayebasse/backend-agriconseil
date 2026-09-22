from django.core.management.base import BaseCommand

from apps.cultures.models import CultureRef, ReferentielAgronomique
from apps.calendrier.models import StadeReference, RegleOperationAgricole


CULTURES = {
    "Riz": {
        "code": "riz",
        "type_cycle": "annuelle",
        "cycle_min": 90,
        "cycle_max": 150,
        "eau_min": 450,
        "eau_max": 700,
        "sensibilite": "forte",
        "source": "FAO",
        "source_reference": "FAO Crop Water Needs / données riz Sénégal",
        "source_url": "https://www.fao.org/",
        "notes": (
            "La durée varie selon le système de culture, la variété "
            "et la zone agroécologique."
        ),
        "stades": [
            ("Installation", 1, 20, 0.50),
            ("Développement végétatif", 2, 40, 0.80),
            ("Reproduction", 3, 50, 1.10),
            ("Maturation", 4, 40, 0.90),
        ],
    },

    "Mil": {
        "code": "mil",
        "type_cycle": "annuelle",
        "cycle_min": 105,
        "cycle_max": 140,
        "eau_min": 450,
        "eau_max": 650,
        "sensibilite": "faible",
        "source": "FAO",
        "source_reference": "FAO Crop Water Needs",
        "source_url": "https://www.fao.org/",
        "notes": "Durée indicative à ajuster selon variété et zone.",
        "stades": [
            ("Installation", 1, 18, 0.35),
            ("Développement végétatif", 2, 28, 0.70),
            ("Floraison et remplissage", 3, 45, 1.10),
            ("Maturation", 4, 25, 0.65),
        ],
    },

    "Maïs": {
        "code": "mais",
        "type_cycle": "annuelle",
        "cycle_min": 125,
        "cycle_max": 180,
        "eau_min": 500,
        "eau_max": 800,
        "sensibilite": "moyenne_forte",
        "source": "FAO",
        "source_reference": "FAO Crop Water Needs",
        "source_url": "https://www.fao.org/",
        "notes": "Référence maïs grain. La variété modifie fortement le cycle.",
        "stades": [
            ("Installation", 1, 25, 0.40),
            ("Développement végétatif", 2, 42, 0.80),
            ("Floraison et remplissage", 3, 50, 1.15),
            ("Maturation", 4, 30, 0.70),
        ],
    },

    "Sorgho": {
        "code": "sorgho",
        "type_cycle": "annuelle",
        "cycle_min": 120,
        "cycle_max": 130,
        "eau_min": 450,
        "eau_max": 650,
        "sensibilite": "faible",
        "source": "FAO",
        "source_reference": "FAO Crop Water Needs",
        "source_url": "https://www.fao.org/",
        "notes": "Référence générique à ajuster selon variété.",
        "stades": [
            ("Installation", 1, 20, 0.35),
            ("Développement végétatif", 2, 30, 0.75),
            ("Floraison et remplissage", 3, 40, 1.10),
            ("Maturation", 4, 30, 0.65),
        ],
    },

    "Arachide": {
        "code": "arachide",
        "type_cycle": "annuelle",
        "cycle_min": 130,
        "cycle_max": 140,
        "eau_min": 500,
        "eau_max": 700,
        "sensibilite": "faible_moyenne",
        "source": "FAO",
        "source_reference": "FAO Crop Water Needs",
        "source_url": "https://www.fao.org/",
        "notes": "Les variétés sénégalaises ont des cycles variables.",
        "stades": [
            ("Installation", 1, 25, 0.45),
            ("Développement végétatif", 2, 35, 0.75),
            ("Floraison et formation des gousses", 3, 45, 1.05),
            ("Maturation", 4, 25, 0.70),
        ],
    },

    "Niébé": {
        "code": "niebe",
        "type_cycle": "annuelle",
        "cycle_min": 70,
        "cycle_max": 100,
        "eau_min": 300,
        "eau_max": 500,
        "sensibilite": "moyenne",
        "source": "ISRA",
        "source_reference": "Variétés et itinéraires techniques adaptés au Sénégal",
        "source_url": "https://isra.sn/",
        "notes": (
            "Le cycle dépend fortement de la variété. "
            "La plage V1 est volontairement large."
        ),
        "stades": [
            ("Installation", 1, 15, 0.45),
            ("Développement végétatif", 2, 20, 0.75),
            ("Floraison et formation des gousses", 3, 30, 1.00),
            ("Maturation", 4, 20, 0.50),
        ],
    },

    "Manioc": {
        "code": "manioc",
        "type_cycle": "annuelle",
        "cycle_min": 180,
        "cycle_max": 270,
        "eau_min": None,
        "eau_max": None,
        "sensibilite": "faible",
        "source": "FAO",
        "source_reference": "FAO - Cassava / pratiques de production",
        "source_url": "https://www.fao.org/",
        "notes": (
            "La date de récolte varie fortement selon la variété et "
            "l'objectif de production."
        ),
        "stades": [
            ("Installation", 1, 30, 0.40),
            ("Développement végétatif", 2, 70, 0.70),
            ("Développement des racines", 3, 90, 0.90),
            ("Maturation", 4, 60, 0.70),
        ],
    },

    "Oignon": {
        "code": "oignon",
        "type_cycle": "annuelle",
        "cycle_min": 150,
        "cycle_max": 210,
        "eau_min": 350,
        "eau_max": 550,
        "sensibilite": "moyenne_forte",
        "source": "FAO",
        "source_reference": "FAO Crop Water Needs",
        "source_url": "https://www.fao.org/",
        "notes": (
            "Référence oignon sec. Le cycle dépend notamment de la variété "
            "et du système de production."
        ),
        "stades": [
            ("Installation", 1, 25, 0.50),
            ("Développement végétatif", 2, 35, 0.75),
            ("Bulbaison", 3, 90, 1.05),
            ("Maturation", 4, 40, 0.85),
        ],
    },

    "Mangue": {
        "code": "mangue",
        "type_cycle": "perenne",
        "cycle_min": None,
        "cycle_max": None,
        "eau_min": None,
        "eau_max": None,
        "sensibilite": "moyenne",
        "source": "ISRA",
        "source_reference": "Références horticoles sénégalaises à compléter",
        "source_url": "https://isra.sn/",
        "notes": (
            "Culture pérenne. Agri-Conseil ne doit pas lui appliquer "
            "artificiellement un cycle annuel. Les règles spécifiques "
            "d'entretien et de production seront ajoutées après validation "
            "des références locales."
        ),
        "stades": [
            ("Installation", 1, 90, None),
            ("Développement végétatif", 2, 180, None),
        ],
    },

    "Pastèque": {
        "code": "pasteque",
        "type_cycle": "annuelle",
        "cycle_min": 75,
        "cycle_max": 100,
        "eau_min": 400,
        "eau_max": 600,
        "sensibilite": "moyenne",
        "source": "FAO",
        "source_reference": "FAO - Melon / Watermelon comme référence de type",
        "source_url": "https://www.fao.org/",
        "notes": (
            "La durée dépend de la variété et des conditions de culture. "
            "Une validation locale est nécessaire pour une version finale."
        ),
        "stades": [
            ("Installation", 1, 20, 0.45),
            ("Développement végétatif", 2, 25, 0.75),
            ("Floraison et fructification", 3, 35, 1.00),
            ("Maturation", 4, 20, 0.75),
        ],
    },
}

REGLES = {
    "Riz": [
        {
            "nom": "Semis",
            "description": "Mise en place de la culture.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Repiquage",
            "description": (
                "Repiquage lorsque le système de production utilise "
                "des plants issus d'une pépinière."
            ),
            "declencheur": "semis",
            "decalage": 21,
            "duree": 1,
        },
        {
            "nom": "Fertilisation",
            "description": "Apport à adapter au stade et aux recommandations locales.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices selon l'état de la parcelle.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 14,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveiller l'état sanitaire et hydrique de la culture.",
            "declencheur": "debut_stade",
            "stade": "Floraison et remplissage",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Irrigation / gestion de l'eau",
            "description": "Adapter l'irrigation aux besoins réels et aux précipitations.",
            "declencheur": "debut_stade",
            "stade": "Floraison et remplissage",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Début de la période indicative de récolte.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Mil": [
        {
            "nom": "Semis",
            "description": "Mise en place de la culture.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices selon le développement de la parcelle.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Fertilisation",
            "description": "Apport selon les recommandations techniques locales.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveillance sanitaire et hydrique.",
            "declencheur": "debut_stade",
            "stade": "Floraison et remplissage",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte lorsque la maturité est atteinte.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Maïs": [
        {
            "nom": "Semis",
            "description": "Mise en place de la culture.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle précoce des adventices.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Fertilisation",
            "description": "Apports fractionnés selon les recommandations techniques.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveiller la culture et son état hydrique.",
            "declencheur": "debut_stade",
            "stade": "Floraison et remplissage",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte à maturité.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Sorgho": [
        {
            "nom": "Semis",
            "description": "Mise en place de la culture.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Fertilisation",
            "description": "Apport selon les recommandations locales.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveillance sanitaire et hydrique.",
            "declencheur": "debut_stade",
            "stade": "Floraison et remplissage",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte à maturité.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Arachide": [
        {
            "nom": "Semis",
            "description": "Mise en place de la culture.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveiller la floraison, les gousses et l'état hydrique.",
            "declencheur": "debut_stade",
            "stade": "Floraison et formation des gousses",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte lorsque la maturité est atteinte.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Niébé": [
        {
            "nom": "Semis",
            "description": "Mise en place de la culture.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveillance des ravageurs et du développement.",
            "declencheur": "debut_stade",
            "stade": "Floraison et formation des gousses",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte à maturité.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Manioc": [
        {
            "nom": "Plantation",
            "description": "Mise en place des boutures.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices pendant l'installation.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveiller le développement végétatif et l'état hydrique.",
            "declencheur": "debut_stade",
            "stade": "Développement des racines",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte selon la variété et l'objectif de production.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Oignon": [
        {
            "nom": "Semis",
            "description": "Mise en place de la pépinière ou semis.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Repiquage",
            "description": "Transplantation selon le système de production.",
            "declencheur": "fin_stade",
            "stade": "Installation",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Fertilisation",
            "description": "Apport selon le stade et les recommandations locales.",
            "declencheur": "debut_stade",
            "stade": "Bulbaison",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveiller la bulbaison et l'état sanitaire.",
            "declencheur": "debut_stade",
            "stade": "Bulbaison",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte à maturité.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Pastèque": [
        {
            "nom": "Semis",
            "description": "Mise en place de la culture.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Désherbage",
            "description": "Contrôle des adventices.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Surveiller floraison, fructification et état hydrique.",
            "declencheur": "debut_stade",
            "stade": "Floraison et fructification",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Récolte",
            "description": "Récolte lorsque les fruits atteignent la maturité.",
            "declencheur": "fin_cycle",
            "decalage": 0,
            "duree": 1,
        },
    ],

    "Mangue": [
        {
            "nom": "Plantation / installation",
            "description": "Suivi de l'installation du verger.",
            "declencheur": "semis",
            "decalage": 0,
            "duree": 1,
        },
        {
            "nom": "Surveillance",
            "description": "Suivi de l'état sanitaire et du développement végétatif.",
            "declencheur": "debut_stade",
            "stade": "Développement végétatif",
            "decalage": 0,
            "duree": 1,
        },
    ],
}

def create_rules(culture, referentiel):
    RegleOperationAgricole.objects.filter(
        culture=culture
    ).delete()

    stages = {
        stage.nom: stage
        for stage in referentiel.stades.all()
    }

    for index, rule in enumerate(
        REGLES.get(culture.nom, [])
    ):
        stade = None

        if rule.get("stade"):
            stade = stages.get(rule["stade"])

        RegleOperationAgricole.objects.create(
            culture=culture,
            stade_reference=stade,
            nom=rule["nom"],
            description=rule["description"],
            declencheur=rule["declencheur"],
            decalage_jours=rule.get("decalage", 0),
            duree_jours=rule.get("duree", 1),
            ordre=index,
        )
        
class Command(BaseCommand):
    help = "Initialise le référentiel agronomique V1 d'Agri-Conseil."

    def handle(self, *args, **options):

        for nom, data in CULTURES.items():

            culture, _ = CultureRef.objects.update_or_create(
                nom=nom,
                defaults={
                    "code": data["code"],
                    "actif": True,
                },
            )

            referentiel, _ = (
                ReferentielAgronomique.objects.update_or_create(
                    culture=culture,
                    defaults={
                        "type_cycle": data["type_cycle"],
                        "cycle_min_jours": data["cycle_min"],
                        "cycle_max_jours": data["cycle_max"],
                        "besoin_eau_min_mm": data["eau_min"],
                        "besoin_eau_max_mm": data["eau_max"],
                        "sensibilite_secheresse": data["sensibilite"],
                        "source": data["source"],
                        "source_reference": data["source_reference"],
                        "source_url": data["source_url"],
                        "notes": data["notes"],
                        "zone_agroecologique": "Sénégal - V1",
                        "valide": False,
                    },
                )
            )

            StadeReference.objects.filter(
                referentiel=referentiel
            ).delete()

            for nom_stade, ordre, duree, kc in data["stades"]:
                StadeReference.objects.create(
                    referentiel=referentiel,
                    nom=nom_stade,
                    ordre=ordre,
                    duree_jours=duree,
                    kc=kc,
                )

            create_rules(culture, referentiel)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Référentiel chargé : {culture.nom}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Référentiel agronomique V1 chargé avec succès."
            )
        )