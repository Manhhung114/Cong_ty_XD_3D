"""Offline regression for the read-only Gemini/OpenAI Admin connectivity probe."""
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from drive_storage.ai_probe import probe_ai_connection

ROOT = Path(__file__).resolve().parents[1]
KEY = "test-secret-api-key-1234567890"


class _Response:
    def __init__(self, code=200):
        self.code = code

    def getcode(self):
        return self.code

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class ConnectionProbeTests(unittest.TestCase):
    def test_gemini_success_only_authenticated_read_no_secret_in_result(self):
        calls = []

        def fake_open(request):
            calls.append(request)
            return _Response()

        with patch("drive_storage.ai_probe._open", side_effect=fake_open):
            result = probe_ai_connection("gemini", "gemini-2.5-flash", KEY)
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["model"], "gemini-2.5-flash")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get_method(), "GET")
        self.assertEqual(calls[0].full_url,
                         "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash")
        self.assertEqual(calls[0].get_header("X-goog-api-key"), KEY)
        self.assertNotIn(KEY, str(result) + calls[0].full_url)
        self.assertIsNone(calls[0].data)

    def test_openai_uses_bearer_and_exact_model_endpoint(self):
        with patch("drive_storage.ai_probe._open", return_value=_Response()) as open_mock:
            result = probe_ai_connection("openai", "gpt-4.1-mini", KEY)
        self.assertTrue(result["ok"])
        request = open_mock.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/models/gpt-4.1-mini")
        self.assertEqual(request.get_header("Authorization"), "Bearer " + KEY)
        self.assertNotIn(KEY, str(result))
        self.assertEqual(request.get_method(), "GET")

    def test_status_errors_and_network_failure_never_echo_private_details(self):
        for code in (400, 401, 403, 404, 429, 503, 302):
            with self.subTest(code=code):
                http = HTTPError("https://api.openai.com/v1/models/gpt-4.1-mini", code,
                                 "Provider returned: " + KEY, None, None)
                with patch("drive_storage.ai_probe._open", side_effect=http):
                    result = probe_ai_connection("openai", "gpt-4.1-mini", KEY)
                self.assertFalse(result["ok"])
                self.assertNotIn(KEY, str(result))
                self.assertNotIn("Provider returned", str(result))
        with patch("drive_storage.ai_probe._open",
                   side_effect=URLError("Provider diagnostic: " + KEY)):
            result = probe_ai_connection("gemini", "gemini-2.5-flash", KEY)
        self.assertFalse(result["ok"])
        self.assertNotIn(KEY, str(result))

    def test_invalid_provider_model_and_key_fail_before_http(self):
        for provider, model, key in [
            ("evil", "gpt-4.1-mini", KEY),
            ("openai", "https://example.com/", KEY),
            ("gemini", "gemini-2.5-flash", "short"),
            ("openai", "../secrets", KEY),
        ]:
            with self.subTest(provider=provider, model=model):
                with patch("drive_storage.ai_probe._open") as open_mock:
                    with self.assertRaises(ValueError):
                        probe_ai_connection(provider, model, key)
                    open_mock.assert_not_called()

    def test_admin_ui_has_live_check_without_persisting_or_exposing_keys(self):
        ui = (ROOT / "drive_storage/ai_settings_ui.py").read_text(encoding="utf8")
        st = (ROOT / "streamlit_app.py").read_text(encoding="utf8")
        bridge = (ROOT / "drive_storage/in_app.py").read_text(encoding="utf8")
        for path in ["src/core/api_settings.js", "static/src/core/api_settings.js"]:
            js = (ROOT / path).read_text(encoding="utf8")
            self.assertIn('data-drive-kind="ai_check"', js)
        self.assertIn('st.form_submit_button("🔎 Kiểm tra kết nối API"', ui)
        self.assertIn('result = probe_ai_connection(provider, model, test_key)', ui)
        self.assertIn("def ai_connection_dialog(st):", ui)
        self.assertIn("can_admin(identity_for(st))", ui)
        self.assertIn("ai_connection_dialog(st)", st)
        self.assertIn('if action.get("kind") == "ai_check":', st)
        self.assertIn('"ai_check"', bridge)
        # Previously metadata-only Agent runs bypassed the central Drive vault.
        company = (ROOT / "drive_storage/company_ui.py").read_text(encoding="utf8")
        self.assertEqual(company.count("ai_config=effective_config(st, agent_id)"), 2)


if __name__ == "__main__":
    unittest.main()
