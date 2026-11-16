"""Fail-closed Google authentication and in-sheet Drive access regression checks."""
import unittest
from pathlib import Path
from drive_storage.in_app import access_role
from scripts.build_streamlit_runtime_v2 import build

ROOT = Path(__file__).resolve().parents[1]

class User(dict):
    def __init__(self, logged_in=True, **values):
        super().__init__(values)
        self.is_logged_in = logged_in

class Streamlit:
    def __init__(self, user, members=()):
        self.user = user
        self.secrets = {
            "drive": {"allowed_email": "owner@example.com"},
            "access": {"members": list(members)},
        }

class RoleGateTests(unittest.TestCase):
    def test_owner_admin_and_verified_member(self):
        owner = Streamlit(User(email="Owner@Example.com", email_verified=True))
        member = Streamlit(User(email="member@example.com", email_verified=True), members=["MEMBER@example.com"])
        self.assertEqual(access_role(owner), "admin")
        self.assertEqual(access_role(member), "member")

    def test_unverified_unlisted_and_anonymous_rejected(self):
        self.assertIsNone(access_role(Streamlit(User(email="owner@example.com", email_verified=False))))
        self.assertIsNone(access_role(Streamlit(User(email="outsider@example.com", email_verified=True))))
        self.assertIsNone(access_role(Streamlit(User(logged_in=False, email="owner@example.com", email_verified=True))))

    def test_server_scoped_bootstrap_and_safe_sheet(self):
        html = build(ROOT / "static", role="member", nonce="A"*32, initial_section="tasks",
                     account_email="owner@example.com", drive_configured=True)
        self.assertIn('window.__xdAuthRole = "member"', html)
        self.assertIn('window.__xdInitialSheet = "tasks"', html)
        self.assertIn('window.__xdDriveConfigured = true', html)
        with self.assertRaises(ValueError):
            build(ROOT / "static", role="owner")

    def test_no_public_pages_static_app(self):
        wf = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf8")
        self.assertIn("test ! -d _public/src", wf)
        self.assertNotIn("cp -r src assets", wf)

if __name__ == "__main__":
    unittest.main()
