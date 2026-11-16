"""Regression tests for Google Drive OAuth settings navigation and configuration."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class TestGoogleDriveLoginUI(unittest.TestCase):
    def test_server_route(self):
        text = (ROOT / "streamlit_app.py").read_text(encoding="utf8")
        self.assertIn("require_login(st)",text)
        self.assertIn("drive_dialog(st)",text)
        self.assertNotIn("render_google_drive_storage(st)", text)

    def test_iframe_settings_link(self):
        one = (ROOT / "src/core/api_settings.js").read_text(encoding="utf8")
        two = (ROOT / "static/src/core/api_settings.js").read_text(encoding="utf8")
        self.assertEqual(one, two)
        self.assertIn('id="driveSettingsCard"', one)
        self.assertIn("Google Drive đã tích hợp", one)
        self.assertNotIn('href="https://congtyxd.streamlit.app/?drive=settings"', one)

    def test_admin_preflight(self):
        panel = (ROOT / "drive_storage/streamlit_panel.py").read_text(encoding="utf8")
        self.assertIn("def display(st, expanded=False):", panel)
        self.assertIn("missing_auth", panel)
        self.assertIn("https://congtyxd.streamlit.app/oauth2callback", panel)

    def test_streamlit_version(self):
        req = (ROOT / "requirements.txt").read_text(encoding="utf8")
        self.assertIn("streamlit[auth]==1.67.0", req)

if __name__ == "__main__": unittest.main()
