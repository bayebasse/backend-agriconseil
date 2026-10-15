import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.cultures.models import CultureRef, ReferenceRendement


HEADERS = [
    "culture_code", "variete", "zone_agroecologique", "systeme_culture",
    "type_cycle", "cycle_min", "cycle_max", "cycle_unite",
    "age_arbres_min_annees", "age_arbres_max_annees",
    "rendement_min", "rendement_moyen", "rendement_max",
    "rendement_unite", "periode_rendement", "besoin_eau_min_mm",
    "besoin_eau_max_mm", "sensibilite_secheresse", "source_titre",
    "source_url", "source_annee", "conditions_mesure",
]


def _optional_int(row, field):
    value = row.get(field, "").strip()
    return int(value) if value else None


def _optional_decimal(row, field):
    value = row.get(field, "").strip()
    if not value:
        return None
    try:
        return Decimal(value.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"{field}: valeur numérique invalide") from exc


def _duplicate_key(item):
    return (
        item.culture_id,
        item.variete.strip().casefold(),
        item.zone_agroecologique.strip().casefold(),
        item.systeme_culture,
        item.type_cycle,
        item.source_titre.strip().casefold(),
        item.source_url.strip().casefold(),
        item.source_annee,
    )


class Command(BaseCommand):
    help = "Importe des références agronomiques/rendement sourcées, toujours non validées."

    def add_arguments(self, parser):
        parser.add_argument("--csv", dest="csv_path", required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["csv_path"])
        if not path.is_file():
            raise CommandError("Le fichier CSV indiqué est introuvable.")

        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None or not set(HEADERS).issubset(reader.fieldnames):
                    raise CommandError("Le CSV doit contenir toutes les colonnes du modèle de référence.")
                rows = list(reader)
        except UnicodeDecodeError as exc:
            raise CommandError("Le CSV doit être encodé en UTF-8.") from exc

        pending = []
        errors = []
        keys = set()
        existing_codes = set(CultureRef.objects.values_list("code", flat=True))

        for line_number, row in enumerate(rows, start=2):
            row = {key: (value or "").strip() for key, value in row.items() if key}
            if not any(value for key, value in row.items() if key != "culture_code"):
                continue
            try:
                code = row.get("culture_code", "")
                if code not in existing_codes:
                    raise ValueError(f"culture_code inconnu: {code or '(vide)'}")
                culture = CultureRef.objects.get(code=code)
                if not (row.get("source_titre", "").strip() or row.get("source_url", "").strip()):
                    raise ValueError("source_titre ou source_url est obligatoire")
                item = ReferenceRendement(
                    culture=culture,
                    variete=row.get("variete", ""),
                    zone_agroecologique=row.get("zone_agroecologique", ""),
                    systeme_culture=row.get("systeme_culture", ""),
                    type_cycle=row.get("type_cycle", ""),
                    cycle_min=_optional_int(row, "cycle_min"),
                    cycle_max=_optional_int(row, "cycle_max"),
                    cycle_unite=row.get("cycle_unite", ""),
                    age_arbres_min_annees=_optional_int(row, "age_arbres_min_annees"),
                    age_arbres_max_annees=_optional_int(row, "age_arbres_max_annees"),
                    rendement_min=_optional_decimal(row, "rendement_min"),
                    rendement_moyen=_optional_decimal(row, "rendement_moyen"),
                    rendement_max=_optional_decimal(row, "rendement_max"),
                    rendement_unite=row.get("rendement_unite", ""),
                    periode_rendement=row.get("periode_rendement", ""),
                    besoin_eau_min_mm=_optional_decimal(row, "besoin_eau_min_mm"),
                    besoin_eau_max_mm=_optional_decimal(row, "besoin_eau_max_mm"),
                    sensibilite_secheresse=row.get("sensibilite_secheresse", ""),
                    source_titre=row.get("source_titre", ""),
                    source_url=row.get("source_url", ""),
                    source_annee=_optional_int(row, "source_annee"),
                    conditions_mesure=row.get("conditions_mesure", ""),
                    valide=False,
                )
                item.full_clean()
                key = _duplicate_key(item)
                if key in keys or ReferenceRendement.objects.filter(
                    culture=culture,
                    variete=item.variete,
                    zone_agroecologique=item.zone_agroecologique,
                    systeme_culture=item.systeme_culture,
                    type_cycle=item.type_cycle,
                    source_titre=item.source_titre,
                    source_url=item.source_url,
                    source_annee=item.source_annee,
                ).exists():
                    raise ValueError("référence dupliquée (dans le fichier ou déjà en base)")
                keys.add(key)
                pending.append(item)
            except (ValueError, ValidationError, TypeError) as exc:
                errors.append(f"ligne {line_number}: {exc}")

        if errors:
            raise CommandError("Import annulé; aucune ligne écrite:\n" + "\n".join(errors))
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Validation OK : {len(pending)} référence(s), aucune écriture."))
            return
        with transaction.atomic():
            ReferenceRendement.objects.bulk_create(pending)
        self.stdout.write(self.style.SUCCESS(
            f"{len(pending)} référence(s) importée(s) avec valide=False."
        ))
