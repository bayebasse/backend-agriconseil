from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cultures.models import Region, Departement, CommuneLocalite, CultureRef


REGIONS = {
    "Dakar": [
        "Dakar",
        "Pikine",
        "Guédiawaye",
        "Rufisque",
        "Keur Massar",
    ],
    "Diourbel": [
        "Bambey",
        "Diourbel",
        "Mbacké",
    ],
    "Fatick": [
        "Fatick",
        "Foundiougne",
        "Gossas",
    ],
    "Kaffrine": [
        "Birkelane",
        "Kaffrine",
        "Koungheul",
        "Malem Hodar",
    ],
    "Kaolack": [
        "Guinguinéo",
        "Kaolack",
        "Nioro du Rip",
    ],
    "Kédougou": [
        "Kédougou",
        "Salémata",
        "Saraya",
    ],
    "Kolda": [
        "Kolda",
        "Médina Yoro Foulah",
        "Vélingara",
    ],
    "Louga": [
        "Kébémer",
        "Linguère",
        "Louga",
    ],
    "Matam": [
        "Kanel",
        "Matam",
        "Ranérou-Ferlo",
    ],
    "Saint-Louis": [
        "Dagana",
        "Podor",
        "Saint-Louis",
    ],
    "Sédhiou": [
        "Bounkiling",
        "Goudomp",
        "Sédhiou",
    ],
    "Tambacounda": [
        "Bakel",
        "Goudiry",
        "Koumpentoum",
        "Tambacounda",
    ],
    "Thiès": [
        "Mbour",
        "Thiès",
        "Tivaouane",
    ],
    "Ziguinchor": [
        "Bignona",
        "Oussouye",
        "Ziguinchor",
    ],
}


CULTURES = [
    {
        "nom": "Riz",
        "code": "riz",
        "description": "Culture du riz.",
        "cycle_jours": 120,
        "besoin_min_mm": 450,
        "besoin_max_mm": 700,
        "sensibilite_secheresse": "forte",
    },
    {
        "nom": "Mil",
        "code": "mil",
        "description": "Culture du mil.",
        "cycle_jours": 100,
        "besoin_min_mm": 350,
        "besoin_max_mm": 550,
        "sensibilite_secheresse": "moyenne",
    },
    {
        "nom": "Maïs",
        "code": "mais",
        "description": "Culture du maïs.",
        "cycle_jours": 100,
        "besoin_min_mm": 400,
        "besoin_max_mm": 650,
        "sensibilite_secheresse": "forte",
    },
    {
        "nom": "Sorgho",
        "code": "sorgho",
        "description": "Culture du sorgho.",
        "cycle_jours": 110,
        "besoin_min_mm": 400,
        "besoin_max_mm": 650,
        "sensibilite_secheresse": "moyenne",
    },
    {
        "nom": "Arachide",
        "code": "arachide",
        "description": "Culture de l'arachide.",
        "cycle_jours": 100,
        "besoin_min_mm": 400,
        "besoin_max_mm": 600,
        "sensibilite_secheresse": "moyenne",
    },
    {
        "nom": "Niébé",
        "code": "niebe",
        "description": "Culture du niébé.",
        "cycle_jours": 80,
        "besoin_min_mm": 300,
        "besoin_max_mm": 500,
        "sensibilite_secheresse": "moyenne",
    },
    {
        "nom": "Manioc",
        "code": "manioc",
        "description": "Culture du manioc.",
        "cycle_jours": 270,
        "besoin_min_mm": 500,
        "besoin_max_mm": 1000,
        "sensibilite_secheresse": "faible",
    },
    {
        "nom": "Oignon",
        "code": "oignon",
        "description": "Culture de l'oignon.",
        "cycle_jours": 120,
        "besoin_min_mm": 350,
        "besoin_max_mm": 550,
        "sensibilite_secheresse": "forte",
    },
    {
        "nom": "Mangue",
        "code": "mangue",
        "description": "Culture de la mangue.",
        "cycle_jours": 180,
        "besoin_min_mm": 750,
        "besoin_max_mm": 1200,
        "sensibilite_secheresse": "moyenne",
    },
    {
        "nom": "Pastèque",
        "code": "pasteque",
        "description": "Culture de la pastèque.",
        "cycle_jours": 90,
        "besoin_min_mm": 400,
        "besoin_max_mm": 600,
        "sensibilite_secheresse": "forte",
    },
]


class Command(BaseCommand):
    help = "Importe les régions, départements et cultures de base du Sénégal."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "Début de l'importation des données Agri-Conseil..."
            )
        )

        total_regions = 0
        total_departements = 0
        total_cultures = 0

        # ---------------------------------------------------------
        # 1. RÉGIONS + DÉPARTEMENTS
        # ---------------------------------------------------------
        for region_name, departements in REGIONS.items():
            region, created = Region.objects.get_or_create(
                nom=region_name
            )

            if created:
                total_regions += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Région créée : {region_name}"
                    )
                )

            for departement_name in departements:
                departement, created = Departement.objects.get_or_create(
                    region=region,
                    nom=departement_name,
                )

                if created:
                    total_departements += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Département créé : {departement_name}"
                        )
                    )

        # ---------------------------------------------------------
        # 2. CULTURES
        # ---------------------------------------------------------
        for culture_data in CULTURES:
            culture, created = CultureRef.objects.update_or_create(
                code=culture_data["code"],
                defaults=culture_data,
            )

            if created:
                total_cultures += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Culture créée : {culture.nom}"
                    )
                )
            else:
                self.stdout.write(
                    f"Culture déjà existante / mise à jour : {culture.nom}"
                )

        # ---------------------------------------------------------
        # 3. RÉSUMÉ
        # ---------------------------------------------------------
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("Importation terminée.")
        )

        self.stdout.write(
            f"Régions créées : {total_regions}"
        )

        self.stdout.write(
            f"Départements créés : {total_departements}"
        )

        self.stdout.write(
            f"Cultures créées : {total_cultures}"
        )

        self.stdout.write(
            f"Total régions en base : {Region.objects.count()}"
        )

        self.stdout.write(
            f"Total départements en base : {Departement.objects.count()}"
        )

        self.stdout.write(
            f"Total cultures en base : {CultureRef.objects.count()}"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Les communes/localités seront importées à partir du répertoire ANSD."
            )
        )