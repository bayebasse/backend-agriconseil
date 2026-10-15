"""Register one manually selected official document, without a search API."""

from urllib.parse import unquote, urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils import timezone

from apps.cultures.document_extraction import extract_document, is_allowed_source_url
from apps.cultures.models import CultureRef, ReferenceRendement


class Command(BaseCommand):
    help = "Enregistre une URL publique officielle comme référence à vérifier; aucune API de recherche n'est appelée."

    def add_arguments(self, parser):
        parser.add_argument("--culture", required=True, help="Code CultureRef, par exemple riz.")
        parser.add_argument("--url", required=True, help="URL exacte du document public officiel (HTTPS).")
        parser.add_argument("--title", default="", help="Titre du document; à vérifier dans l'administration.")
        parser.add_argument("--organisme", default="", help="Organisme auteur, si connu.")
        parser.add_argument("--extract", action="store_true", help="Tenter l'extraction Gemini après l'enregistrement.")

    def handle(self, *args, **options):
        culture = CultureRef.objects.filter(code=options["culture"]).first()
        if culture is None:
            raise CommandError(f"Culture inconnue: {options['culture']}. Ajoutez-la d'abord au catalogue CultureRef.")

        url = options["url"].strip()
        if not is_allowed_source_url(url):
            raise CommandError("Utilisez une URL HTTPS directe d'ISRA, DAPSA, FAO ou AfricaRice.")

        existing = ReferenceRendement.objects.filter(culture=culture, source_url=url).first()
        if existing:
            reference = existing
            created = False
        else:
            parsed = urlparse(url)
            title = options["title"].strip() or unquote(parsed.path.rsplit("/", 1)[-1]) or parsed.hostname or "Document agronomique"
            organism = options["organisme"].strip() or parsed.hostname or ""
            try:
                reference = ReferenceRendement.objects.create(
                    culture=culture,
                    source_titre=title[:255],
                    source_organisme=organism[:160],
                    source_url=url,
                    statut_validation="A_VERIFIER",
                    valide=False,
                    collectee_le=timezone.now(),
                )
                created = True
            except IntegrityError as exc:
                raise CommandError("Cette URL existe déjà pour cette culture.") from exc

        if options["extract"] and not reference.extraction_preuves and reference.statut_validation == "A_VERIFIER":
            try:
                extract_document(reference)
            except Exception as exc:
                self.stderr.write(self.style.WARNING(
                    f"Document conservé sans extraction Gemini ({type(exc).__name__}); il reste à vérifier."
                ))

        action = "ajouté" if created else "déjà présent"
        self.stdout.write(self.style.SUCCESS(
            f"Document {action} comme référence A_VERIFIER pour {culture.nom}. Ouvrez /admin/ pour le contrôler."
        ))
