import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from .yield_advice import _request_gemini, analyze_agricultural_context


class AgriculturalAdviceTests(SimpleTestCase):
    def setUp(self):
        self.context = {
            "culture": "Riz",
            "date_semis": "2026-06-01",
            "cycle_agronomique": None,
            "stade_cultural": None,
            "superficie": {"valeur": "2.50", "unite": None},
            "zone_agroecologique_declaree": None,
            "meteo": None,
            "reference_rendement": None,
            "limites": ["Référence de rendement absente."],
        }

    @override_settings(GEMINI_API_KEY="test-secret", GEMINI_MODEL="test-model")
    def test_configured_sdk_request_uses_json_and_bounded_timeout(self):
        fake_google = ModuleType("google")
        fake_genai = SimpleNamespace(Client=MagicMock())
        fake_types = SimpleNamespace(
            HttpOptions=MagicMock(return_value="http-options"),
            HttpRetryOptions=MagicMock(return_value="retry-options"),
            GenerateContentConfig=MagicMock(return_value="generation-config"),
        )
        fake_google.genai = fake_genai
        fake_genai.types = fake_types
        fake_google_genai = ModuleType("google.genai")
        fake_google_genai.types = fake_types

        with patch.dict(sys.modules, {
            "google": fake_google,
            "google.genai": fake_google_genai,
        }):
            _request_gemini("prepared context")

        fake_types.HttpOptions.assert_called_once_with(
            timeout=12_000, retry_options="retry-options"
        )
        fake_types.HttpRetryOptions.assert_called_once_with(attempts=1)
        fake_genai.Client.assert_called_once_with(
            api_key="test-secret", http_options="http-options"
        )
        call = fake_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(call.kwargs["model"], "test-model")
        self.assertEqual(call.kwargs["contents"], "prepared context")
        self.assertEqual(call.kwargs["config"], "generation-config")
        fake_types.GenerateContentConfig.assert_called_once()

    @override_settings(GEMINI_API_KEY="")
    @patch("apps.ia.yield_advice._request_gemini")
    def test_missing_key_does_not_call_provider(self, request):
        result = analyze_agricultural_context(self.context)
        self.assertEqual(result["statut"], "indisponible")
        self.assertEqual(result["raison"], "cle_api_absente")
        request.assert_not_called()

    @override_settings(GEMINI_API_KEY="test-secret", GEMINI_MODEL="test-model")
    @patch("apps.ia.yield_advice._request_gemini")
    def test_valid_json_is_returned_as_qualitative_advice(self, request):
        request.return_value.text = (
            '{"resume":"Rendement non estimable.",'
            '"facteurs_favorables":[],"facteurs_defavorables":[],'
            '"recommandations":[]}'
        )
        result = analyze_agricultural_context(self.context)
        self.assertEqual(result["statut"], "disponible")
        self.assertEqual(result["resume"], "Rendement non estimable.")
        self.assertNotIn("test-secret", str(result))
        prompt = request.call_args.args[0]
        self.assertIn('"reference_rendement": null', prompt)
        self.assertIn('"unite": null', prompt)
        self.assertNotIn("agriculteur", prompt)

    @override_settings(GEMINI_API_KEY="test-secret")
    @patch("apps.ia.yield_advice._request_gemini")
    def test_invalid_model_json_is_rejected(self, request):
        request.return_value.text = "not JSON"
        result = analyze_agricultural_context(self.context)
        self.assertEqual(result["statut"], "indisponible")
        self.assertEqual(result["raison"], "reponse_modele_invalide")
        self.assertEqual(result["recommandations"], [])

    @override_settings(GEMINI_API_KEY="test-secret")
    @patch(
        "apps.ia.yield_advice._request_gemini",
        side_effect=TimeoutError("secret provider detail"),
    )
    def test_provider_error_is_sanitized(self, request):
        result = analyze_agricultural_context(self.context)
        self.assertEqual(result["statut"], "indisponible")
        self.assertEqual(result["raison"], "fournisseur_indisponible")
        self.assertNotIn("secret provider detail", str(result))

    @override_settings(GEMINI_API_KEY="test-secret")
    @patch("apps.ia.yield_advice._request_gemini")
    def test_wrongly_typed_fields_are_rejected(self, request):
        request.return_value.text = (
            '{"resume":"ok","facteurs_favorables":[1],'
            '"facteurs_defavorables":[],"recommandations":[]}'
        )
        result = analyze_agricultural_context(self.context)
        self.assertEqual(result["raison"], "reponse_modele_invalide")

    @override_settings(GEMINI_API_KEY="test-secret")
    @patch("apps.ia.yield_advice._request_gemini")
    def test_advice_citing_missing_data_is_rejected(self, request):
        request.return_value.text = (
            '{"resume":"Une pluie est attendue.",'
            '"facteurs_favorables":[],"facteurs_defavorables":[],'
            '"recommandations":[{"texte":"Reporter l\'irrigation.",'
            '"bases":["meteo.pluie_prevue"]}]}'
        )
        result = analyze_agricultural_context(self.context)
        self.assertEqual(result["statut"], "indisponible")
        self.assertEqual(result["raison"], "reponse_modele_invalide")

    @override_settings(GEMINI_API_KEY="test-secret")
    @patch("apps.ia.yield_advice._request_gemini")
    def test_advice_may_cite_nested_reference_or_harvest_evidence(self, request):
        request.return_value.text = (
            '{"resume":"Référence disponible.","facteurs_favorables":[], '
            '"facteurs_defavorables":[],"recommandations":[{"texte":"Comparer aux observations.",'
            '"bases":["recoltes_reelles_comparables.0.rendement_observe_kg_ha"]}]}'
        )
        context = {
            **self.context,
            "recoltes_reelles_comparables": [
                {"rendement_observe_kg_ha": "500.000", "source": "masquée"}
            ],
        }
        result = analyze_agricultural_context(context)
        self.assertEqual(result["statut"], "disponible")
