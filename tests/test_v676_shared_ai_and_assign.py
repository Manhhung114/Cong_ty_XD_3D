"""V6.7.6 tests: Admin-managed encrypted shared API and REAL task-to-Agent dispatch."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from test_v59_v60_cloud_workflow import (
    CloudWorkflowTests, SIGNING_KEY, PROJECT, SECOND, Request
)
from drive_storage.ai_vault import (
    save_shared, read_shared, revoke_shared, effective_config, safe_status,
)
from drive_storage.company_agents import run_agent


class SharedAIAndAgentAssignmentTests(unittest.TestCase):
    def setUp(self):
        CloudWorkflowTests.setUp(self)

        def update(fileId, media_body, fields=""):
            def perform():
                old = self.storage.files[fileId]
                self.storage.media[fileId] = media_body.data
                old["size"] = len(media_body.data)
                return dict(old)
            return Request(perform)

        self.storage.service.update = update
        self.server = SimpleNamespace(secrets={
            "auth": {"cookie_secret": SIGNING_KEY},
            "drive": {
                "root_folder_id": self.storage.root_id,
                "client_id": "id", "client_secret": "secret",
                "refresh_token": "token",
            },
            "ai": {
                "provider": "gemini", "api_key": "LEGACY_SERVER_KEY",
                "model": "gemini-2.5-flash",
            },
        })

    def tearDown(self):
        CloudWorkflowTests.tearDown(self)

    def _save(self):
        return save_shared(
            self.storage, SIGNING_KEY, self.admin,
            provider="gemini", model="gemini-2.5-flash",
            api_key="SHARED_KEY_CORPORATE_0123456789",
            agent_models={"ELE": "gemini-2.5-pro"},
        )

    def test_admin_configure_once_is_encrypted_and_available_for_other_sessions(self):
        with self.assertRaises(PermissionError):
            save_shared(
                self.storage, SIGNING_KEY, self.editor,
                provider="gemini", model="gemini-2.5-flash",
                api_key="SHARED_KEY_CORPORATE_0123456789",
            )
        file_id = self._save()
        raw = self.storage.media[file_id]
        self.assertNotIn(b"SHARED_KEY_CORPORATE", raw)
        self.assertNotIn(b"gemini-2.5-pro", raw)
        self.assertEqual(json.loads(raw)["algorithm"], "AES-256-GCM")
        self.assertEqual(read_shared(self.storage, SIGNING_KEY)[1]["model"],
                         "gemini-2.5-flash")
        with patch("drive_storage.manager.from_streamlit_secrets",
                   return_value=self.storage):
            # All sessions resolve same provider/key server-side, not browser.
            one = effective_config(self.server, "ELE")
            two = effective_config(self.server, "STR")
            self.assertEqual(one["model"], "gemini-2.5-pro")
            self.assertEqual(two["model"], "gemini-2.5-flash")
            self.assertEqual(one["api_key"], "SHARED_KEY_CORPORATE_0123456789")
            public = safe_status(self.server)
            self.assertTrue(public["configured"])
            self.assertTrue(public["shared"])
            self.assertNotIn("api_key", public)
            self.assertNotIn("SHARED_KEY", str(public))

    def test_corrupt_vault_fails_closed_and_refuses_overwrite(self):
        file_id = self._save()
        raw = self.storage.media[file_id]
        envelope = json.loads(raw)
        envelope["ciphertext"] = envelope["ciphertext"][:-5] + "ABCDE"
        self.storage.media[file_id] = json.dumps(envelope).encode()
        with self.assertRaises(PermissionError):
            read_shared(self.storage, SIGNING_KEY)
        with self.assertRaises(PermissionError):
            self._save()
        with self.assertRaises(PermissionError):
            read_shared(self.storage, "other-secret-" + "X"*48)

    def test_revoke_is_persistent_even_with_old_secrets(self):
        self._save()
        revoke_shared(self.storage, self.admin, SIGNING_KEY)
        with patch("drive_storage.manager.from_streamlit_secrets",
                   return_value=self.storage):
            config = effective_config(self.server, "ELE")
            self.assertEqual(config["provider"], "none")
            self.assertFalse(safe_status(self.server)["configured"])
        self.assertTrue(read_shared(self.storage, SIGNING_KEY)[1]["disabled"])
        with self.assertRaises(PermissionError):
            revoke_shared(self.storage, self.reader, SIGNING_KEY)

    def test_task_is_not_agent_run_until_explicit_server_dispatch(self):
        record = self.ws.create_task(
            self.editor, project_id=PROJECT, title="Rà soát bản vẽ điện",
            dept="electrical", assignee="",
        )
        task_id = record["id"]
        first = self.ws.snapshot(self.reader)
        self.assertEqual(first["tasks"][0]["assignee"], "")
        self.assertEqual(first["tasks"][0]["assignedAgentId"], "")
        self.assertEqual(first["agentRuns"], [])
        with self.assertRaises(ValueError):
            self.ws.assign_task(
                self.editor, project_id=PROJECT, task_id=task_id,
                agent_id="STR",
            )
        with self.assertRaises(PermissionError):
            self.ws.assign_task(
                self.reader, project_id=PROJECT, task_id=task_id,
                agent_id="ELE",
            )
        self.ws.assign_task(
            self.editor, project_id=PROJECT, task_id=task_id,
            assignee="Kỹ sư điện", agent_id="ELE",
        )
        assigned = self.ws.snapshot(self.reader)
        self.assertEqual(assigned["tasks"][0]["assignedAgentId"], "ELE")
        self.assertEqual(assigned["tasks"][0]["assignee"], "Kỹ sư điện")
        self.assertEqual(assigned["agentRuns"], [])
        # Explicit action creates signed draft, but never approves task.
        result = run_agent(
            self.ws, self.editor, project_id=PROJECT,
            task_id=task_id, agent_id="ELE", mode="preflight",
        )
        self.assertTrue(result["reviewRequired"])
        done = self.ws.snapshot(self.reader)
        self.assertEqual(len(done["agentRuns"]), 1)
        self.assertEqual(done["tasks"][0]["status"], "todo")
        self.assertTrue(any(x["action"] == "task.assigned" for x in done["events"]))
        self.assertTrue(any(x["action"] == "agent.completed" for x in done["events"]))


if __name__ == "__main__":
    unittest.main()
