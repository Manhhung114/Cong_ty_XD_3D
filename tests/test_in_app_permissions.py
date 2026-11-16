"""RBAC regression tests inspired by QLDA's Read / Update / Admin model."""
import unittest
from pathlib import Path
from unittest.mock import patch

from drive_storage.access_control import (
    empty_policy, validate_policy, set_user, revoke_user, legacy_policy,
    identity_for, allows_project, can_upload, can_admin, read_policy, _signature,
)

ROOT = Path(__file__).resolve().parents[1]
ROOT_ID = "drive-root-123456"
SIGNING_KEY = "test-signing-secret-0123456789abcdef-123456"
PROJECT = "project-one-123456"
OTHER = "project-two-123456"


class Account(dict):
    def __init__(self, logged=True, **kwargs):
        super().__init__(kwargs)
        self.is_logged_in = logged


class StreamlitFake:
    def __init__(self, email, verified=True, members=()):
        self.user = Account(email=email, email_verified=verified)
        self.secrets = {
            "drive": {
                "allowed_email": "owner@example.com",
                "root_folder_id": ROOT_ID,
                "client_id": "fake",
                "client_secret": "fake",
                "refresh_token": "fake",
            },
            "access": {"members": list(members)},
            "auth": {"cookie_secret": SIGNING_KEY},
        }


class Request:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeFiles:
    def __init__(self, data=None):
        self.data = data

    def list(self, **kwargs):
        if self.data is None:
            return Request({"files": []})
        return Request({"files": [{
            "id": "policy-file-12345",
            "name": "_XD_MEP_ACCESS_ROLES_V1.json",
            "parents": [ROOT_ID],
            "mimeType": "application/json",
            "size": str(len(self.data)),
        }]})

    def get_media(self, **kwargs):
        return Request(self.data)


class FakeStorage:
    root_id = ROOT_ID

    def __init__(self, raw=None):
        self.files_api = FakeFiles(raw)
        self.service = self

    def files(self):
        return self.files_api


class AccessTests(unittest.TestCase):
    def test_owner_only_admin_and_unverified_rejected(self):
        st = StreamlitFake("owner@example.com")
        with patch("drive_storage.manager.from_streamlit_secrets", return_value=FakeStorage()):
            self.assertEqual(identity_for(st)["role"], "admin")
            self.assertIsNone(identity_for(StreamlitFake("stranger@example.com")))
            self.assertIsNone(identity_for(StreamlitFake("owner@example.com", verified=False)))

    def test_legacy_members_and_managed_revocation(self):
        st = StreamlitFake("member@example.com", members=["member@example.com"])
        with patch("drive_storage.manager.from_streamlit_secrets", return_value=FakeStorage()):
            self.assertEqual(identity_for(st)["role"], "update")
        import json
        policy = empty_policy()
        raw = json.dumps({**policy, "_signature": _signature(policy, SIGNING_KEY)}).encode("utf8")
        with patch("drive_storage.manager.from_streamlit_secrets", return_value=FakeStorage(raw)):
            self.assertIsNone(identity_for(st))

    def test_qlda_roles_project_scopes_and_revoke(self):
        initial = legacy_policy([])
        policy = set_user(
            initial, email="engineer@example.com", name="Engineer",
            role="read", projects=[PROJECT], active=True,
            actor="owner@example.com", owner="owner@example.com",
        )
        self.assertEqual(policy["users"]["engineer@example.com"]["role"], "read")
        ident = {"role": "read", "projects": [PROJECT]}
        self.assertTrue(allows_project(ident, PROJECT))
        self.assertFalse(allows_project(ident, OTHER))
        self.assertFalse(can_upload(ident))
        self.assertFalse(can_admin(ident))
        policy = set_user(
            policy, email="engineer@example.com", name="Engineer",
            role="update", projects=["*"], active=True,
            actor="owner@example.com", owner="owner@example.com",
        )
        self.assertTrue(can_upload(policy["users"]["engineer@example.com"]))
        final = revoke_user(policy, email="engineer@example.com",
                            actor="owner@example.com", owner="owner@example.com")
        self.assertNotIn("engineer@example.com", final["users"])

    def test_owner_cannot_be_demoted_and_policy_is_fail_closed(self):
        with self.assertRaises(PermissionError):
            set_user(empty_policy(), email="owner@example.com", name="Owner",
                     role="read", projects=["*"], active=True,
                     actor="owner@example.com", owner="owner@example.com")
        with self.assertRaises(ValueError):
            validate_policy({"version": 2, "users": {}})
        with self.assertRaises(ValueError):
            validate_policy({"version": 1, "users": {"a@example.com": {"role": "superuser"}}})

    def test_read_manifest_and_corrupted_manifest(self):
        import json
        policy = empty_policy()
        raw = json.dumps({**policy, "_signature": _signature(policy, SIGNING_KEY)}).encode("utf8")
        file_id, policy = read_policy(FakeStorage(raw), SIGNING_KEY)
        self.assertEqual(file_id, "policy-file-12345")
        self.assertEqual(policy["users"], {})
        with self.assertRaises((ValueError, UnicodeDecodeError)):
            read_policy(FakeStorage(b'not-json'), SIGNING_KEY)

    def test_settings_admin_only_and_dialog_wired(self):
        app = (ROOT / "src/app.js").read_text(encoding="utf8")
        ui = (ROOT / "src/core/api_settings.js").read_text(encoding="utf8")
        backend = (ROOT / "drive_storage/in_app.py").read_text(encoding="utf8")
        self.assertIn("window.__xdAuthRole!=='admin'", app)
        self.assertIn('data-drive-kind="access"', ui)
        self.assertIn('id="roleSettingsCard"', ui)
        self.assertIn("if not can_admin(actor):", backend)
        self.assertEqual(ui, (ROOT / "static/src/core/api_settings.js").read_text(encoding="utf8"))


if __name__ == "__main__":
    unittest.main()
