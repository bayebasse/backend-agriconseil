from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.calendrier.models import RegleOperationAgricole, StadeReference
from apps.cultures.models import (
    CommuneLocalite,
    CultureRef,
    CultureSuivie,
    Departement,
    Region,
    RecolteReelle,
    ReferentielAgronomique,
    ReferenceRendement,
)


@override_settings(GEMINI_API_KEY="")
class YieldPredictionApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.farmer = User.objects.create_user(
            username="farmer", password="test-password-123"
        )
        self.other_farmer = User.objects.create_user(
            username="other", password="test-password-123"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.farmer)

        self.region = Region.objects.create(nom="Test region")
        self.departement = Departement.objects.create(
            region=self.region, nom="Test department"
        )
        self.commune = CommuneLocalite.objects.create(
            departement=self.departement,
            nom="Test commune",
            type_localite="commune",
        )
        self.crop_ref = CultureRef.objects.create(
            nom="Riz", code="riz", cycle_jours=120
        )
        self.crop = CultureSuivie.objects.create(
            agriculteur=self.farmer,
            culture=self.crop_ref,
            region=self.region,
            departement=self.departement,
            commune=self.commune,
            superficie=Decimal("2.50"),
            date_semis=date(2026, 1, 1),
            type_sol="limoneux",
        )
        self.url = reverse("prevision-rendement", args=[self.crop.pk])

    def add_reference(self, **overrides):
        values = {
            "type_cycle": "annuelle",
            "cycle_min_jours": 10,
            "cycle_max_jours": 15,
            "source": "FAO",
            "source_reference": "Référence de test vérifiée",
            "source_url": "https://example.org/reference",
            "valide": True,
        }
        values.update(overrides)
        return ReferentielAgronomique.objects.create(
            culture=self.crop_ref, **values
        )

    def test_reference_validation_status_stays_in_sync_with_legacy_flag(self):
        reference = ReferenceRendement.objects.create(
            culture=self.crop_ref,
            source_titre="Document en revue",
            source_url="https://example.org/doc",
            statut_validation="A_VERIFIER",
        )
        self.assertFalse(reference.valide)
        self.assertEqual(reference.statut_validation, "A_VERIFIER")
        reference.statut_validation = "VALIDE"
        reference.save()
        reference.refresh_from_db()
        self.assertTrue(reference.valide)

    @patch("apps.cultures.document_extraction.requests.get")
    def test_public_url_import_needs_no_search_key_and_skips_duplicate(self, get):
        options = {
            "culture": "riz",
            "url": "https://www.fao.org/publications/rice-guide.pdf",
            "title": "Guide de culture du riz",
        }
        call_command("collect_references_agronomiques", **options)
        reference = ReferenceRendement.objects.get(culture=self.crop_ref)
        self.assertEqual(reference.statut_validation, "A_VERIFIER")
        self.assertFalse(reference.valide)
        self.assertEqual(reference.source_titre, "Guide de culture du riz")
        self.assertIsNotNone(reference.collectee_le)
        call_command("collect_references_agronomiques", **options)
        self.assertEqual(ReferenceRendement.objects.filter(culture=self.crop_ref).count(), 1)
        get.assert_not_called()

    @override_settings(GEMINI_API_KEY="")
    @patch("apps.cultures.document_extraction.requests.get")
    def test_document_url_is_saved_when_gemini_is_unavailable(self, get):
        call_command(
            "collect_references_agronomiques",
            culture="riz",
            url="https://isra.sn/guide-riz.pdf",
            extract=True,
        )
        reference = ReferenceRendement.objects.get(culture=self.crop_ref)
        self.assertEqual(reference.statut_validation, "A_VERIFIER")
        self.assertFalse(reference.valide)
        get.assert_not_called()

    @patch("apps.cultures.document_extraction._extract_with_gemini")
    @patch("apps.cultures.document_extraction._download")
    @override_settings(GEMINI_API_KEY="test-key")
    def test_document_extraction_stores_evidence_without_validating(self, download, extract):
        reference = ReferenceRendement.objects.create(
            culture=self.crop_ref,
            source_titre="Guide du riz",
            source_url="https://isra.sn/guide-riz.pdf",
        )
        download.return_value = (b"%PDF-test", "application/pdf", reference.source_url)
        extract.return_value = {
            "culture": "Riz",
            "titre_document": "Guide du riz",
            "source_organisme": "ISRA",
            "variete": "",
            "zone_agroecologique": "Vallée du fleuve Sénégal",
            "systeme_culture": "irrigue",
            "type_cycle": "annuelle",
            "cycle_min": 110,
            "cycle_max": 120,
            "cycle_unite": "jours",
            "rendement_min": None,
            "rendement_moyen": 6000,
            "rendement_max": None,
            "rendement_unite": "kg_ha",
            "besoin_eau_min_mm": None,
            "besoin_eau_max_mm": None,
            "sensibilite_secheresse": "",
            "source_annee": 2020,
            "source_page": "12",
            "preuves": [{"champ": "rendement_moyen", "extrait": "6 t/ha", "page": "12"}],
        }
        from apps.cultures.document_extraction import extract_document

        extract_document(reference)
        reference.refresh_from_db()
        self.assertEqual(reference.rendement_moyen, Decimal("6000"))
        self.assertEqual(reference.source_page, "12")
        self.assertEqual(reference.extraction_preuves[0]["extrait"], "6 t/ha")
        self.assertEqual(reference.statut_validation, "A_VERIFIER")
        self.assertFalse(reference.valide)

    def test_pdf_can_be_imported_and_extracted_without_a_public_url(self):
        extracted = {
            "culture": "Riz",
            "titre_document": "Guide du riz",
            "source_organisme": "ISRA",
            "variete": "",
            "zone_agroecologique": "",
            "systeme_culture": "",
            "type_cycle": "",
            "cycle_min": None,
            "cycle_max": None,
            "cycle_unite": "",
            "rendement_min": None,
            "rendement_moyen": None,
            "rendement_max": None,
            "rendement_unite": "",
            "besoin_eau_min_mm": None,
            "besoin_eau_max_mm": None,
            "sensibilite_secheresse": "",
            "source_annee": None,
            "source_page": "1",
            "preuves": [],
        }
        from apps.cultures.document_extraction import extract_document

        with override_settings(
            STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
        ):
            reference = ReferenceRendement.objects.create(
                culture=self.crop_ref,
                source_titre="Document importé",
                document_fichier=SimpleUploadedFile(
                    "guide-riz.pdf", b"%PDF-1.4\ncontenu test", content_type="application/pdf"
                ),
            )
            with override_settings(GEMINI_API_KEY=""):
                with self.assertRaises(RuntimeError):
                    extract_document(reference)
            reference.refresh_from_db()
            self.assertTrue(reference.document_fichier.name.endswith("guide-riz.pdf"))
            self.assertEqual(reference.statut_validation, "A_VERIFIER")
            with patch("apps.cultures.document_extraction._extract_with_gemini", return_value=extracted) as extract:
                with override_settings(GEMINI_API_KEY="test-key"):
                    extract_document(reference)
            reference.refresh_from_db()
            self.assertTrue(reference.document_fichier.name.endswith("guide-riz.pdf"))
            self.assertEqual(reference.statut_validation, "A_VERIFIER")
            self.assertFalse(reference.valide)
            self.assertEqual(reference.extraction_preuves[-1]["champ"], "culture")
            extract.assert_called_once()

    def test_same_document_cannot_be_added_twice_for_a_crop(self):
        ReferenceRendement.objects.create(
            culture=self.crop_ref,
            source_titre="Guide",
            source_url="https://isra.sn/guide-riz",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ReferenceRendement.objects.create(
                    culture=self.crop_ref,
                    source_titre="Guide duplicaté",
                    source_url="https://isra.sn/guide-riz",
                )

    def test_document_extractor_rejects_non_official_hosts(self):
        from apps.cultures.document_extraction import _download

        with self.assertRaises(ValueError):
            _download("https://example.org/agriculture.pdf")

    def test_extraction_values_without_document_evidence_are_dropped(self):
        from apps.cultures.document_extraction import _keep_only_evidenced_values

        data = {
            "culture": "Riz",
            "titre_document": "Guide",
            "source_organisme": "ISRA",
            "variete": "Variété inventée",
            "zone_agroecologique": "",
            "systeme_culture": "irrigue",
            "type_cycle": "annuelle",
            "cycle_min": 120,
            "cycle_max": None,
            "cycle_unite": "jours",
            "rendement_min": None,
            "rendement_moyen": 5000,
            "rendement_max": None,
            "rendement_unite": "kg_ha",
            "besoin_eau_min_mm": None,
            "besoin_eau_max_mm": None,
            "sensibilite_secheresse": "",
            "source_annee": 2021,
            "source_page": "2",
            "preuves": [{"champ": "rendement_moyen", "extrait": "5 t/ha", "page": "2"}],
        }

        cleaned = _keep_only_evidenced_values(data)

        self.assertEqual(cleaned["rendement_moyen"], 5000)
        self.assertIsNone(cleaned["cycle_min"])
        self.assertIsNone(cleaned["source_annee"])
        self.assertEqual(cleaned["variete"], "")
        self.assertEqual(cleaned["culture"], "")

    @patch("apps.cultures.prediction_service.get_region_weather")
    def test_annual_cycle_returns_period_but_no_fabricated_yield(self, get_weather):
        get_weather.return_value = {
            "temperature": 30,
            "humidite": 55,
            "vent_kmh": 12,
            "precipitation_mm": 0,
            "probabilite_pluie": 0,
            "precipitation_prevue_mm": 0,
            "pluie_prevue": False,
            "conseil": "Conseil météo existant",
            "prevision": {"aujourd_hui": 3},
        }
        self.add_reference()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["recolte_prevue"]["date_debut"], date(2026, 1, 10))
        self.assertEqual(response.data["recolte_prevue"]["date_fin"], date(2026, 1, 15))
        self.assertIsNone(response.data["rendement_estime_kg_ha"])
        self.assertIsNone(response.data["quantite_totale_estimee_kg"])
        self.assertEqual(response.data["meteo"]["temperature"], 30)
        self.assertEqual(response.data["facteurs_favorables"], [])
        self.assertEqual(len(response.data["recommandations"]), 1)
        self.assertEqual(response.data["analyse_ia"]["statut"], "indisponible")
        self.assertEqual(response.data["analyse_ia"]["raison"], "cle_api_absente")

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    @patch("apps.ia.yield_advice._request_gemini")
    @patch("apps.ia.yield_advice.settings.GEMINI_API_KEY", "test-key")
    def test_gemini_advice_is_additive_and_does_not_create_yield(
        self, request, get_weather
    ):
        get_weather.return_value = {
            "temperature": 29,
            "humidite": 60,
            "vent_kmh": 8,
            "precipitation_mm": 0,
            "probabilite_pluie": 75,
            "precipitation_prevue_mm": 3,
            "pluie_prevue": True,
            "conseil": "Conseil météo fondé sur la pluie prévue.",
            "source": "OpenWeather",
            "prevision": {"aujourd_hui": 2},
        }
        request.return_value.text = (
            '{"resume":"Données insuffisantes pour chiffrer le rendement.",'
            '"facteurs_favorables":[],"facteurs_defavorables":[],'
            '"recommandations":[{"texte":"Tenir compte de la pluie prévue.",'
            '"bases":["meteo.pluie_prevue"]}]}'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["analyse_ia"]["statut"], "disponible")
        self.assertIsNone(response.data["rendement_estime_kg_ha"])
        self.assertIsNone(response.data["quantite_totale_estimee_kg"])
        self.assertEqual(response.data["recommandations"][0]["type"], "meteo")
        self.assertEqual(
            response.data["analyse_ia"]["recommandations"],
            [{
                "texte": "Tenir compte de la pluie prévue.",
                "bases": ["meteo.pluie_prevue"],
            }],
        )
        prompt = request.call_args.args[0]
        self.assertIn('"reference_rendement": null', prompt)
        self.assertIn('"unite": null', prompt)
        self.assertNotIn('"culture_suivie_id"', prompt)

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_perennial_cycle_does_not_invent_harvest_date(self, get_weather):
        self.add_reference(
            type_cycle="perenne",
            cycle_min_jours=100,
            cycle_max_jours=200,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["recolte_prevue"]["date_debut"])
        self.assertEqual(response.data["recolte_prevue"]["statut"], "indisponible")

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_unvalidated_or_missing_reference_leaves_period_unavailable(self, get_weather):
        self.add_reference(valide=False)
        response = self.client.get(self.url)
        self.assertIsNone(response.data["recolte_prevue"]["date_debut"])
        self.assertTrue(any("pas validé" in item for item in response.data["limites"]))

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_absent_agronomic_reference_is_reported(self, get_weather):
        response = self.client.get(self.url)
        self.assertIsNone(response.data["type_cycle"])
        self.assertIsNone(response.data["recolte_prevue"]["date_debut"])
        self.assertEqual(response.data["references"], [])
        self.assertTrue(any("Aucun référentiel" in item for item in response.data["limites"]))

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_stage_and_calendar_rule_recommendation_are_specific_to_crop(self, get_weather):
        self.crop.date_semis = timezone.localdate() - timedelta(days=5)
        self.crop.save(update_fields=["date_semis"])
        reference = self.add_reference(cycle_min_jours=20, cycle_max_jours=30)
        stage_reference = StadeReference.objects.create(
            referentiel=reference,
            nom="Développement",
            ordre=1,
            duree_jours=20,
            description="Phase de développement de référence.",
        )
        RegleOperationAgricole.objects.create(
            culture=self.crop_ref,
            stade_reference=stage_reference,
            nom="Surveillance planifiée",
            description="Suivi au stade défini.",
            declencheur="debut_stade",
            decalage_jours=10,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["stade_actuel"]["nom"], "Développement")
        self.assertEqual(response.data["stade_actuel"]["description"], "Phase de développement de référence.")
        recommendation = response.data["recommandations"][0]
        self.assertEqual(recommendation["source"], "règle du calendrier agricole")
        self.assertEqual(recommendation["texte"], "Préparez l'opération « Surveillance planifiée » prévue au calendrier.")

    @patch(
        "apps.cultures.prediction_service.get_region_weather",
        side_effect=RuntimeError("provider unavailable"),
    )
    def test_weather_failure_does_not_fail_prediction(self, get_weather):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["meteo"])
        self.assertTrue(any("météo" in item for item in response.data["limites"]))
        self.assertEqual(response.data["recommandations"], [])

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_other_farmer_cannot_read_prediction_or_harvest(self, get_weather):
        other_crop = CultureSuivie.objects.create(
            agriculteur=self.other_farmer,
            culture=self.crop_ref,
            region=self.region,
            departement=self.departement,
            commune=self.commune,
            superficie=Decimal("1.00"),
            date_semis=date(2026, 1, 1),
            type_sol="limoneux",
        )
        response = self.client.get(
            reverse("prevision-rendement", args=[other_crop.pk])
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.get(
            reverse("recoltes-reelles", args=[other_crop.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_actual_harvest_is_stored_separately_with_units(self):
        url = reverse("recoltes-reelles", args=[self.crop.pk])
        response = self.client.post(
            url,
            {
                "date_recolte": timezone.localdate().isoformat(),
                "quantite": "125.500",
                "unite": "kg",
                "observations": "Récolte pesée",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["unite"], "kg")
        self.assertEqual(RecolteReelle.objects.count(), 1)
        self.assertFalse(hasattr(RecolteReelle, "rendement_estime_kg_ha"))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["quantite"], "125.500")

    def test_harvest_unit_and_future_date_are_validated(self):
        url = reverse("recoltes-reelles", args=[self.crop.pk])
        response = self.client.post(
            url,
            {
                "date_recolte": (timezone.localdate() + timedelta(days=1)).isoformat(),
                "quantite": "3",
                "unite": "sac",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("date_recolte", response.data)

    def test_prediction_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_ten_requested_crops_are_supported_without_fabricated_references(self, _weather):
        codes = ["mil", "arachide", "riz", "mais", "sorgho", "niebe", "manioc", "oignon", "mangue", "pasteque"]
        for code in codes:
            ref, _ = CultureRef.objects.get_or_create(
                code=code, defaults={"nom": code.title(), "cycle_jours": 90}
            )
            crop, _ = CultureSuivie.objects.get_or_create(
                agriculteur=self.farmer,
                culture=ref,
                defaults={
                    "region": self.region,
                    "departement": self.departement,
                    "commune": self.commune,
                    "superficie": Decimal("1.00"),
                    "date_semis": date(2026, 1, 1),
                    "type_sol": "limoneux",
                },
            )
            response = self.client.get(reverse("prevision-rendement", args=[crop.pk]))
            self.assertEqual(response.status_code, 200, code)
            self.assertIsNone(response.data["rendement_estime_kg_ha"], code)
            self.assertIsNone(response.data["quantite_totale_estimee_kg"], code)
            self.assertIsNone(response.data["rendement_reference"], code)

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_sourced_annual_reference_is_separate_from_estimate(self, _weather):
        ReferenceRendement.objects.create(
            culture=self.crop_ref,
            type_cycle="annuelle",
            cycle_min=2,
            cycle_max=3,
            cycle_unite="mois",
            rendement_moyen=Decimal("1200"),
            rendement_unite="kg_ha",
            periode_rendement="campagne",
            source_titre="Source de test",
            valide=True,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rendement_reference"]["rendement"]["moyen"], "1200.000")
        self.assertEqual(response.data["recolte_prevue"]["date_debut"], date(2026, 2, 28))
        self.assertIsNone(response.data["rendement_estime_kg_ha"])
        self.assertIsNone(response.data["quantite_totale_estimee_kg"])

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_reference_production_converts_tonnes_and_never_calls_it_a_forecast(self, _weather):
        self.crop.unite_superficie = "ha"
        self.crop.save(update_fields=["unite_superficie"])
        ReferenceRendement.objects.create(
            culture=self.crop_ref,
            rendement_moyen=Decimal("1.250"),
            rendement_unite="tonne_ha",
            source_titre="Document contrôlé",
            source_url="https://fao.org/rice",
            statut_validation="VALIDE",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rendement_reference_kg_ha"], "1250.000")
        self.assertEqual(response.data["production_reference_kg"], "3125.000")
        self.assertIsNone(response.data["rendement_estime_kg_ha"])
        self.assertIsNone(response.data["quantite_totale_estimee_kg"])
        self.assertEqual(response.data["references"][0]["url"], "https://fao.org/rice")

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_pending_yield_reference_is_never_used(self, _weather):
        self.crop.unite_superficie = "ha"
        self.crop.save(update_fields=["unite_superficie"])
        ReferenceRendement.objects.create(
            culture=self.crop_ref,
            rendement_moyen=Decimal("2.000"),
            rendement_unite="tonne_ha",
            source_titre="Document en revue",
            source_url="https://fao.org/rice",
            statut_validation="A_VERIFIER",
        )

        response = self.client.get(self.url)

        self.assertIsNone(response.data["rendement_reference"])
        self.assertIsNone(response.data["rendement_reference_kg_ha"])
        self.assertIsNone(response.data["production_reference_kg"])

    @patch("apps.cultures.prediction_service.get_region_weather", return_value=None)
    def test_perennial_yield_reference_does_not_date_harvest(self, _weather):
        ReferenceRendement.objects.create(
            culture=self.crop_ref,
            type_cycle="perenne",
            age_arbres_min_annees=3,
            age_arbres_max_annees=8,
            rendement_moyen=Decimal("25"),
            rendement_unite="kg_arbre",
            periode_rendement="annee",
            source_titre="Source arboricole de test",
            valide=True,
        )
        self.crop.age_arbres_annees = 4
        self.crop.save(update_fields=["age_arbres_annees"])
        response = self.client.get(self.url)
        self.assertIsNone(response.data["recolte_prevue"]["date_debut"])
        self.assertIn("pérenne", response.data["recolte_prevue"]["raison_indisponible"])
