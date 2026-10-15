"""Fetch a small set of official agronomy documents and extract reviewable facts."""

import json
import logging
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_TEXT_CHARS = 45_000
ALLOWED_HOSTS = ("isra.sn", "dapsa.gouv.sn", "fao.org", "africarice.org")

EXTRACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "culture": {"type": "STRING"},
        "titre_document": {"type": "STRING"},
        "source_organisme": {"type": "STRING"},
        "variete": {"type": "STRING"},
        "zone_agroecologique": {"type": "STRING"},
        "systeme_culture": {"type": "STRING", "enum": ["", "pluvial", "irrigue", "mixte"]},
        "type_cycle": {"type": "STRING", "enum": ["", "annuelle", "perenne"]},
        "cycle_min": {"type": ["INTEGER", "NULL"]},
        "cycle_max": {"type": ["INTEGER", "NULL"]},
        "cycle_unite": {"type": "STRING", "enum": ["", "jours", "mois", "annees"]},
        "rendement_min": {"type": ["NUMBER", "NULL"]},
        "rendement_moyen": {"type": ["NUMBER", "NULL"]},
        "rendement_max": {"type": ["NUMBER", "NULL"]},
        "rendement_unite": {"type": "STRING", "enum": ["", "kg_ha", "tonne_ha", "kg_arbre", "tonne_arbre"]},
        "besoin_eau_min_mm": {"type": ["NUMBER", "NULL"]},
        "besoin_eau_max_mm": {"type": ["NUMBER", "NULL"]},
        "sensibilite_secheresse": {"type": "STRING", "enum": ["", "faible", "faible_moyenne", "moyenne", "moyenne_forte", "forte"]},
        "source_annee": {"type": ["INTEGER", "NULL"]},
        "source_page": {"type": "STRING"},
        "preuves": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "champ": {"type": "STRING"},
                    "extrait": {"type": "STRING"},
                    "page": {"type": "STRING"},
                },
                "required": ["champ", "extrait", "page"],
            },
        },
    },
    "required": [
        "culture", "titre_document", "source_organisme", "variete", "zone_agroecologique", "systeme_culture", "type_cycle",
        "cycle_min", "cycle_max", "cycle_unite", "rendement_min",
        "rendement_moyen", "rendement_max", "rendement_unite",
        "besoin_eau_min_mm", "besoin_eau_max_mm", "sensibilite_secheresse",
        "source_annee", "source_page", "preuves",
    ],
}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())


def is_allowed_source_url(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    return (
        parsed.scheme == "https"
        and any(host == domain or host.endswith("." + domain) for domain in ALLOWED_HOSTS)
        and not parsed.username
        and not parsed.password
    )


def _download(url):
    current_url = url
    for _ in range(4):
        if not is_allowed_source_url(current_url):
            raise ValueError("URL hors des domaines documentaires autorisés")
        response = requests.get(
            current_url,
            headers={"User-Agent": "Agri-Conseil/1.0 (document review)"},
            timeout=(5, 20),
            stream=True,
            allow_redirects=False,
        )
        if response.is_redirect:
            current_url = requests.compat.urljoin(current_url, response.headers.get("Location", ""))
            response.close()
            continue
        try:
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > MAX_DOCUMENT_BYTES:
                    raise ValueError("Document supérieur à la limite de 8 Mo")
                chunks.append(chunk)
            return b"".join(chunks), response.headers.get("Content-Type", "").lower(), current_url
        finally:
            response.close()
    raise ValueError("Trop de redirections")


def _extract_with_gemini(title, url, content, content_type):
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            timeout=30_000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    prompt = (
        "Extrais seulement les faits explicitement présents dans ce document agricole. "
        "La culture doit être le nom écrit dans le document, ou une chaîne vide si absente. "
        "Conserve exactement les unités; si un fait manque, renvoie null pour nombre ou "
        "une chaîne vide pour texte. Ne convertis pas les unités et n'infère rien. "
        "Pour chaque valeur non vide/non nulle, ajoute dans preuves un court extrait exact "
        "et la page si visible, sinon chaîne vide. Le titre et l'URL sont des métadonnées, "
        "pas une preuve. Les systèmes sont pluvial, irrigue ou mixte. La sensibilité à la "
        "sécheresse ne doit être renseignée que si le document la qualifie explicitement.\n"
        f"Culture documentaire: {title}\nURL: {url}"
    )
    if "pdf" in content_type or content.lstrip().startswith(b"%PDF"):
        document = types.Part.from_bytes(data=content, mime_type="application/pdf")
        contents = [prompt, document]
    elif (
        "html" in content_type
        or "text/plain" in content_type
        or content.lstrip().lower().startswith((b"<!doctype html", b"<html"))
    ):
        parser = _TextExtractor()
        parser.feed(content.decode("utf-8", errors="replace"))
        text = " ".join(parser.parts)[:MAX_TEXT_CHARS]
        if len(text) < 100:
            raise ValueError("Page HTML sans texte exploitable")
        contents = prompt + "\nContenu du document:\n" + text
    else:
        raise ValueError("Le lien ne renvoie ni PDF ni page HTML lisible")
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EXTRACTION_SCHEMA,
            temperature=0,
        ),
    )
    data = json.loads(response.text or "")
    if not isinstance(data, dict) or set(data) != set(EXTRACTION_SCHEMA["required"]):
        raise ValueError("Structure Gemini inattendue")
    for key in ("cycle_min", "cycle_max", "rendement_min", "rendement_moyen", "rendement_max", "besoin_eau_min_mm", "besoin_eau_max_mm", "source_annee"):
        value = data[key]
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
            raise ValueError(f"Valeur numérique invalide: {key}")
    return _keep_only_evidenced_values(data)


def _keep_only_evidenced_values(data):
    """Drop extracted values Gemini did not tie to a document excerpt."""
    if not isinstance(data["preuves"], list) or len(data["preuves"]) > 80:
        raise ValueError("Preuves invalides")
    evidence_fields = set()
    valid_proofs = []
    for proof in data["preuves"]:
        if not isinstance(proof, dict) or set(proof) != {"champ", "extrait", "page"}:
            continue
        if not all(isinstance(proof[key], str) for key in ("champ", "extrait", "page")):
            continue
        if proof["champ"] and proof["extrait"].strip():
            evidence_fields.add(proof["champ"])
            valid_proofs.append(proof)
    data["preuves"] = valid_proofs
    # Reject any extracted value Gemini did not associate with a document excerpt.
    for field in ("culture", "titre_document", "source_organisme", "variete", "zone_agroecologique", "systeme_culture", "type_cycle", "cycle_unite", "rendement_unite", "sensibilite_secheresse"):
        if field not in evidence_fields:
            data[field] = ""
    for field in ("cycle_min", "cycle_max", "rendement_min", "rendement_moyen", "rendement_max", "besoin_eau_min_mm", "besoin_eau_max_mm", "source_annee"):
        if field not in evidence_fields:
            data[field] = None
    return data


def extract_document(reference):
    """Populate a pending candidate; never validates or writes unsupported values."""
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY absent")
    if reference.document_fichier:
        uploaded = reference.document_fichier.file
        uploaded.seek(0)
        content = uploaded.read(MAX_DOCUMENT_BYTES + 1)
        uploaded.seek(0)
        if len(content) > MAX_DOCUMENT_BYTES:
            raise ValueError("Document supérieur à la limite de 8 Mo")
        if not content.startswith(b"%PDF-"):
            raise ValueError("Le fichier importé n'est pas un PDF valide")
        content_type = "application/pdf"
        source_label = reference.document_fichier.name
        final_url = reference.source_url
    elif reference.source_url:
        content, content_type, final_url = _download(reference.source_url)
        source_label = final_url
    else:
        raise ValueError("Ajoutez un PDF ou une URL publique avant l'extraction")
    data = _extract_with_gemini(
        reference.source_titre,
        source_label,
        content,
        content_type,
    )
    reference.variete = data["variete"][:120]
    if data["titre_document"] and not reference.source_titre:
        reference.source_titre = data["titre_document"][:255]
    if data["source_organisme"]:
        reference.source_organisme = data["source_organisme"][:160]
    reference.zone_agroecologique = data["zone_agroecologique"][:160]
    reference.systeme_culture = data["systeme_culture"]
    reference.type_cycle = data["type_cycle"]
    reference.cycle_min = data["cycle_min"]
    reference.cycle_max = data["cycle_max"]
    reference.cycle_unite = data["cycle_unite"]
    for field in (
        "rendement_min", "rendement_moyen", "rendement_max",
        "besoin_eau_min_mm", "besoin_eau_max_mm",
    ):
        setattr(reference, field, data[field])
    reference.rendement_unite = data["rendement_unite"]
    reference.sensibilite_secheresse = data["sensibilite_secheresse"]
    reference.source_annee = data["source_annee"]
    reference.source_page = data["source_page"][:80]
    reference.extraction_preuves = list(data["preuves"])
    if data["culture"]:
        reference.extraction_preuves.append({
            "champ": "culture",
            "extrait": data["culture"][:255],
            "page": data["source_page"],
        })
    if final_url:
        reference.source_url = final_url
    # A machine extraction is evidence for a human review, never an approval.
    reference.statut_validation = "A_VERIFIER"
    reference.valide = False
    reference.save()
    return reference

