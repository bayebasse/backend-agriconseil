#Ancien code de import_donnees_senegal.py
# from django.core.management.base import BaseCommand
# from django.db import transaction

# from apps.cultures.models import Region, Departement, CommuneLocalite, CultureRef


# REGIONS = {
#     "Dakar": [
#         "Dakar",
#         "Pikine",
#         "Guédiawaye",
#         "Rufisque",
#         "Keur Massar",
#     ],
#     "Diourbel": [
#         "Bambey",
#         "Diourbel",
#         "Mbacké",
#     ],
#     "Fatick": [
#         "Fatick",
#         "Foundiougne",
#         "Gossas",
#     ],
#     "Kaffrine": [
#         "Birkelane",
#         "Kaffrine",
#         "Koungheul",
#         "Malem Hodar",
#     ],
#     "Kaolack": [
#         "Guinguinéo",
#         "Kaolack",
#         "Nioro du Rip",
#     ],
#     "Kédougou": [
#         "Kédougou",
#         "Salémata",
#         "Saraya",
#     ],
#     "Kolda": [
#         "Kolda",
#         "Médina Yoro Foulah",
#         "Vélingara",
#     ],
#     "Louga": [
#         "Kébémer",
#         "Linguère",
#         "Louga",
#     ],
#     "Matam": [
#         "Kanel",
#         "Matam",
#         "Ranérou-Ferlo",
#     ],
#     "Saint-Louis": [
#         "Dagana",
#         "Podor",
#         "Saint-Louis",
#     ],
#     "Sédhiou": [
#         "Bounkiling",
#         "Goudomp",
#         "Sédhiou",
#     ],
#     "Tambacounda": [
#         "Bakel",
#         "Goudiry",
#         "Koumpentoum",
#         "Tambacounda",
#     ],
#     "Thiès": [
#         "Mbour",
#         "Thiès",
#         "Tivaouane",
#     ],
#     "Ziguinchor": [
#         "Bignona",
#         "Oussouye",
#         "Ziguinchor",
#     ],
# }


# CULTURES = [
#     {
#         "nom": "Riz",
#         "code": "riz",
#         "description": "Culture du riz.",
#         "cycle_jours": 120,
#         "besoin_min_mm": 450,
#         "besoin_max_mm": 700,
#         "sensibilite_secheresse": "forte",
#     },
#     {
#         "nom": "Mil",
#         "code": "mil",
#         "description": "Culture du mil.",
#         "cycle_jours": 100,
#         "besoin_min_mm": 350,
#         "besoin_max_mm": 550,
#         "sensibilite_secheresse": "moyenne",
#     },
#     {
#         "nom": "Maïs",
#         "code": "mais",
#         "description": "Culture du maïs.",
#         "cycle_jours": 100,
#         "besoin_min_mm": 400,
#         "besoin_max_mm": 650,
#         "sensibilite_secheresse": "forte",
#     },
#     {
#         "nom": "Sorgho",
#         "code": "sorgho",
#         "description": "Culture du sorgho.",
#         "cycle_jours": 110,
#         "besoin_min_mm": 400,
#         "besoin_max_mm": 650,
#         "sensibilite_secheresse": "moyenne",
#     },
#     {
#         "nom": "Arachide",
#         "code": "arachide",
#         "description": "Culture de l'arachide.",
#         "cycle_jours": 100,
#         "besoin_min_mm": 400,
#         "besoin_max_mm": 600,
#         "sensibilite_secheresse": "moyenne",
#     },
#     {
#         "nom": "Niébé",
#         "code": "niebe",
#         "description": "Culture du niébé.",
#         "cycle_jours": 80,
#         "besoin_min_mm": 300,
#         "besoin_max_mm": 500,
#         "sensibilite_secheresse": "moyenne",
#     },
#     {
#         "nom": "Manioc",
#         "code": "manioc",
#         "description": "Culture du manioc.",
#         "cycle_jours": 270,
#         "besoin_min_mm": 500,
#         "besoin_max_mm": 1000,
#         "sensibilite_secheresse": "faible",
#     },
#     {
#         "nom": "Oignon",
#         "code": "oignon",
#         "description": "Culture de l'oignon.",
#         "cycle_jours": 120,
#         "besoin_min_mm": 350,
#         "besoin_max_mm": 550,
#         "sensibilite_secheresse": "forte",
#     },
#     {
#         "nom": "Mangue",
#         "code": "mangue",
#         "description": "Culture de la mangue.",
#         "cycle_jours": 180,
#         "besoin_min_mm": 750,
#         "besoin_max_mm": 1200,
#         "sensibilite_secheresse": "moyenne",
#     },
#     {
#         "nom": "Pastèque",
#         "code": "pasteque",
#         "description": "Culture de la pastèque.",
#         "cycle_jours": 90,
#         "besoin_min_mm": 400,
#         "besoin_max_mm": 600,
#         "sensibilite_secheresse": "forte",
#     },
# ]


# class Command(BaseCommand):
#     help = "Importe les régions, départements et cultures de base du Sénégal."

#     @transaction.atomic
#     def handle(self, *args, **options):
#         self.stdout.write(
#             self.style.WARNING(
#                 "Début de l'importation des données Agri-Conseil..."
#             )
#         )

#         total_regions = 0
#         total_departements = 0
#         total_cultures = 0

#         # ---------------------------------------------------------
#         # 1. RÉGIONS + DÉPARTEMENTS
#         # ---------------------------------------------------------
#         for region_name, departements in REGIONS.items():
#             region, created = Region.objects.get_or_create(
#                 nom=region_name
#             )

#             if created:
#                 total_regions += 1
#                 self.stdout.write(
#                     self.style.SUCCESS(
#                         f"Région créée : {region_name}"
#                     )
#                 )

#             for departement_name in departements:
#                 departement, created = Departement.objects.get_or_create(
#                     region=region,
#                     nom=departement_name,
#                 )

#                 if created:
#                     total_departements += 1
#                     self.stdout.write(
#                         self.style.SUCCESS(
#                             f"  Département créé : {departement_name}"
#                         )
#                     )

#         # ---------------------------------------------------------
#         # 2. CULTURES
#         # ---------------------------------------------------------
#         for culture_data in CULTURES:
#             culture, created = CultureRef.objects.update_or_create(
#                 code=culture_data["code"],
#                 defaults=culture_data,
#             )

#             if created:
#                 total_cultures += 1
#                 self.stdout.write(
#                     self.style.SUCCESS(
#                         f"Culture créée : {culture.nom}"
#                     )
#                 )
#             else:
#                 self.stdout.write(
#                     f"Culture déjà existante / mise à jour : {culture.nom}"
#                 )

#         # ---------------------------------------------------------
#         # 3. RÉSUMÉ
#         # ---------------------------------------------------------
#         self.stdout.write("")
#         self.stdout.write(
#             self.style.SUCCESS("Importation terminée.")
#         )

#         self.stdout.write(
#             f"Régions créées : {total_regions}"
#         )

#         self.stdout.write(
#             f"Départements créés : {total_departements}"
#         )

#         self.stdout.write(
#             f"Cultures créées : {total_cultures}"
#         )

#         self.stdout.write(
#             f"Total régions en base : {Region.objects.count()}"
#         )

#         self.stdout.write(
#             f"Total départements en base : {Departement.objects.count()}"
#         )

#         self.stdout.write(
#             f"Total cultures en base : {CultureRef.objects.count()}"
#         )

#         self.stdout.write("")
#         self.stdout.write(
#             self.style.WARNING(
#                 "Les communes/localités seront importées à partir du répertoire ANSD."
#             )
#         )



import csv
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cultures.models import (
    Region,
    Departement,
    CommuneLocalite,
    CultureRef,
)


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


def normaliser_texte(value):
    """
    Normalise un texte pour faciliter les comparaisons.

    Exemple :
        "Kédougou" -> "kedougou"
        "KÉDOUGOU" -> "kedougou"
        "  Thiès  " -> "thies"
    """

    if value is None:
        return ""

    value = str(value).strip()

    value = " ".join(value.split())

    value = unicodedata.normalize("NFD", value)

    value = "".join(
        char
        for char in value
        if unicodedata.category(char) != "Mn"
    )

    return value.casefold()


def nettoyer_nom(value):
    """
    Nettoie les espaces sans modifier le nom fourni
    par le fichier ANSD.
    """

    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def trouver_colonne(fieldnames, *possibles):
    """
    Trouve une colonne CSV même si son écriture varie.

    Exemple :
        COMMUNE
        Commune
        commune

    seront reconnus comme la même colonne.
    """

    if not fieldnames:
        return None

    normalisees = {
        normaliser_texte(field): field
        for field in fieldnames
        if field
    }

    for nom in possibles:
        cle = normaliser_texte(nom)

        if cle in normalisees:
            return normalisees[cle]

    return None


class Command(BaseCommand):

    help = (
        "Importe les régions, départements, "
        "communes, villes/arrondissements, "
        "quartiers/villages/hameaux et cultures du Sénégal."
    )

    def _chemin_fichier_localites(self):
        """
        Localisation du fichier CSV ANSD.

        backend-agriconseil/
        ├── data/
        │   └── repertoire_localites_ansd.csv
        └── apps/
        """

        return (
            Path(settings.BASE_DIR)
            / "data"
            / "repertoire_localites_ansd.csv"
        )

    def importer_regions_et_departements(self):
        """
        Initialise le référentiel de base :
        14 régions + 46 départements.
        """

        total_regions = 0
        total_departements = 0

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

                departement, created = (
                    Departement.objects.get_or_create(
                        region=region,
                        nom=departement_name,
                    )
                )

                if created:
                    total_departements += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Département créé : "
                            f"{departement_name}"
                        )
                    )

        return total_regions, total_departements

    def creer_localite(
        self,
        departement,
        nom,
        type_localite,
    ):
        """
        Crée une localité si elle n'existe pas.

        Les coordonnées restent nulles pour le moment.
        """

        if not nom:
            return False

        _, created = CommuneLocalite.objects.get_or_create(
            departement=departement,
            nom=nom,
            type_localite=type_localite,
            defaults={
                "latitude": None,
                "longitude": None,
            },
        )

        return created

    def importer_localites(self):
        """
        Importe les trois niveaux du fichier ANSD :

        1. COM_ARRT_VILLE
        2. COMMUNE
        3. QUARTIER_VILLAGE_HAMEAU

        Toutes les valeurs sont conservées dans la même table
        CommuneLocalite, avec leur type_localite.
        """

        csv_path = self._chemin_fichier_localites()

        if not csv_path.exists():

            self.stdout.write(
                self.style.ERROR(
                    "\nFichier géographique introuvable :\n"
                    f"{csv_path}\n\n"
                    "Placez le fichier ANSD dans :\n"
                    "data/repertoire_localites_ansd.csv"
                )
            )

            return 0

        total_nouvelles = 0
        total_existantes = 0
        lignes_ignorees = 0

        region_map = {
            normaliser_texte(region.nom): region
            for region in Region.objects.all()
        }

        departement_map = {
            (
                normaliser_texte(departement.region.nom),
                normaliser_texte(departement.nom),
            ): departement
            for departement in (
                Departement.objects.select_related("region").all()
            )
        }

        with open(
            csv_path,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as fichier:

            lecteur = csv.DictReader(fichier)

            if not lecteur.fieldnames:

                self.stdout.write(
                    self.style.ERROR(
                        "Le fichier CSV ne contient pas "
                        "d'en-têtes."
                    )
                )

                return 0

            # -----------------------------------------------------
            # Détection des colonnes
            # -----------------------------------------------------

            colonne_region = trouver_colonne(
                lecteur.fieldnames,
                "Région",
                "Region",
            )

            colonne_departement = trouver_colonne(
                lecteur.fieldnames,
                "Département",
                "Departement",
            )

            colonne_com_arrt_ville = trouver_colonne(
                lecteur.fieldnames,
                "COM_ARRT_VILLE",
            )

            colonne_commune = trouver_colonne(
                lecteur.fieldnames,
                "COMMUNE",
                "Commune",
            )

            colonne_quartier = trouver_colonne(
                lecteur.fieldnames,
                "QUARTIER_VILLAGE_HAMEAU",
            )

            colonnes_obligatoires = {
                "Region": colonne_region,
                "Departement": colonne_departement,
                "COM_ARRT_VILLE": colonne_com_arrt_ville,
                "COMMUNE": colonne_commune,
                "QUARTIER_VILLAGE_HAMEAU": colonne_quartier,
            }

            colonnes_manquantes = [
                nom
                for nom, colonne in colonnes_obligatoires.items()
                if not colonne
            ]

            if colonnes_manquantes:

                self.stdout.write(
                    self.style.ERROR(
                        "Colonnes manquantes dans le CSV : "
                        + ", ".join(colonnes_manquantes)
                    )
                )

                return 0

            # -----------------------------------------------------
            # Lecture des lignes
            # -----------------------------------------------------

            for ligne in lecteur:

                region_nom = nettoyer_nom(
                    ligne.get(colonne_region)
                )

                departement_nom = nettoyer_nom(
                    ligne.get(colonne_departement)
                )

                com_arrt_ville_nom = nettoyer_nom(
                    ligne.get(colonne_com_arrt_ville)
                )

                commune_nom = nettoyer_nom(
                    ligne.get(colonne_commune)
                )

                quartier_nom = nettoyer_nom(
                    ligne.get(colonne_quartier)
                )

                if not region_nom or not departement_nom:

                    lignes_ignorees += 1
                    continue

                region_key = normaliser_texte(region_nom)

                departement_key = normaliser_texte(
                    departement_nom
                )

                # -------------------------------------------------
                # Région
                # -------------------------------------------------

                region = region_map.get(region_key)

                if region is None:

                    region, _ = Region.objects.get_or_create(
                        nom=region_nom
                    )

                    region_map[region_key] = region

                # -------------------------------------------------
                # Département
                # -------------------------------------------------

                dept_key = (
                    region_key,
                    departement_key,
                )

                departement = departement_map.get(
                    dept_key
                )

                if departement is None:

                    departement, _ = (
                        Departement.objects.get_or_create(
                            region=region,
                            nom=departement_nom,
                        )
                    )

                    departement_map[dept_key] = departement

                # -------------------------------------------------
                # 1. COM_ARRT_VILLE
                # -------------------------------------------------

                if com_arrt_ville_nom:

                    created = self.creer_localite(
                        departement=departement,
                        nom=com_arrt_ville_nom,
                        type_localite="arrondissement_ville",
                    )

                    if created:
                        total_nouvelles += 1
                    else:
                        total_existantes += 1

                # -------------------------------------------------
                # 2. COMMUNE
                # -------------------------------------------------

                if commune_nom:

                    created = self.creer_localite(
                        departement=departement,
                        nom=commune_nom,
                        type_localite="commune",
                    )

                    if created:
                        total_nouvelles += 1
                    else:
                        total_existantes += 1

                # -------------------------------------------------
                # 3. QUARTIER / VILLAGE / HAMEAU
                # -------------------------------------------------

                if quartier_nom:

                    created = self.creer_localite(
                        departement=departement,
                        nom=quartier_nom,
                        type_localite=(
                            "quartier_village_hameau"
                        ),
                    )

                    if created:
                        total_nouvelles += 1
                    else:
                        total_existantes += 1

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Importation des localités terminée."
            )
        )

        self.stdout.write(
            f"Nouvelles localités : {total_nouvelles}"
        )

        self.stdout.write(
            f"Localités déjà présentes : "
            f"{total_existantes}"
        )

        if lignes_ignorees:

            self.stdout.write(
                self.style.WARNING(
                    f"Lignes ignorées : {lignes_ignorees}"
                )
            )

        return total_nouvelles

    def importer_cultures(self):
        """
        Importe les 10 cultures officielles.
        """

        total_cultures = 0

        for culture_data in CULTURES:

            culture, created = (
                CultureRef.objects.update_or_create(
                    code=culture_data["code"],
                    defaults=culture_data,
                )
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
                    f"Culture déjà existante / mise à jour : "
                    f"{culture.nom}"
                )

        return total_cultures

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "\nDébut de l'importation des données "
                "Agri-Conseil..."
            )
        )

        # =========================================================
        # 1. RÉGIONS + DÉPARTEMENTS
        # =========================================================

        (
            total_regions,
            total_departements,
        ) = self.importer_regions_et_departements()

        # =========================================================
        # 2. LOCALITÉS ANSD
        # =========================================================

        total_localites = self.importer_localites()

        # =========================================================
        # 3. CULTURES
        # =========================================================

        total_cultures = self.importer_cultures()

        # =========================================================
        # 4. RÉSUMÉ
        # =========================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Importation terminée."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            f"Régions créées : {total_regions}"
        )

        self.stdout.write(
            f"Départements créés : {total_departements}"
        )

        self.stdout.write(
            f"Nouvelles localités : {total_localites}"
        )

        self.stdout.write(
            f"Cultures créées : {total_cultures}"
        )

        self.stdout.write("")

        self.stdout.write(
            f"Total régions en base : "
            f"{Region.objects.count()}"
        )

        self.stdout.write(
            f"Total départements en base : "
            f"{Departement.objects.count()}"
        )

        self.stdout.write(
            f"Total localités en base : "
            f"{CommuneLocalite.objects.count()}"
        )

        self.stdout.write(
            f"Total cultures en base : "
            f"{CultureRef.objects.count()}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.WARNING(
                "Les coordonnées des localités ne sont "
                "pas importées ici."
            )
        )

        self.stdout.write(
            self.style.WARNING(
                "La météo V1 sera obtenue au niveau "
                "de la région avec OpenWeather."
            )
        )