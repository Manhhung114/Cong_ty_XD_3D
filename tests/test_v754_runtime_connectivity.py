"""V7.5.4 regression: backend connection must be verified before enabling V7.4 queue.

Unit test is hermetic: no network, no Streamlit Cloud secrets and no AI calls.
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agent_runtime.client import runtime_status


SECRET = "a-long-worker-hmac-test-secret-of-more-than-32-chars"
URL = "https://worker.invalid"
IDENTITY = {"email": "engineer@example.com", "role": "update", "projects": ["project-folder-000001"]}
PROJECT = "project-folder-000001"


def st(configured=True):
    return SimpleNamespace(secrets={"runtime": {
        "api_url": URL, "internal_secret": SECRET,
    }} if configured else {})


class RuntimeStatusTests(unittest.TestCase):
    def test_no_runtime_config_is_not_a_working_queue(self):
        with patch.dict("os.environ", {}, clear=True):
            status = runtime_status(st(False), IDENTITY, PROJECT)
        self.assertEqual(status["reason"], "not_configured")
        self.assertFalse(status["connected"])
        self.assertIn("PostgreSQL", status["message"])

    def test_signed_api_success_is_not_claimed_as_worker_heartbeat(self):
        with patch.dict("os.environ", {}, clear=True), patch(
                "agent_runtime.client.RuntimeClient.send", return_value={
                    "jobs": [{"id": "a" * 32, "state": "queued"}]
                }) as send:
            status = runtime_status(st(), IDENTITY, PROJECT)
        self.assertTrue(status["connected"])
        self.assertEqual(status["reason"], "api_connected")
        self.assertEqual(status["jobs"][0]["state"], "queued")
        self.assertIn("heartbeat", status["message"])
        send.assert_called_once_with(
            "/api/runtime/jobs/query", {"projectId": PROJECT, "identity": IDENTITY},
            timeout=4)

    def test_unreachable_api_disables_queue(self):
        with patch.dict("os.environ", {}, clear=True), patch(
                "agent_runtime.client.RuntimeClient.send",
                side_effect=RuntimeError("Cannot contact private API")):
            status = runtime_status(st(), IDENTITY, PROJECT)
        self.assertFalse(status["connected"])
        self.assertEqual(status["reason"], "api_unreachable")
        self.assertNotIn(URL, status["message"])

    def test_api_permission_denied_disables_queue(self):
        with patch.dict("os.environ", {}, clear=True), patch(
                "agent_runtime.client.RuntimeClient.send",
                side_effect=PermissionError("private token")):
            status = runtime_status(st(), IDENTITY, PROJECT)
        self.assertFalse(status["connected"])
        self.assertEqual(status["reason"], "access_denied")
        self.assertNotIn("private token", status["message"])

    def test_malformed_api_response_cannot_enable_queue(self):
        with patch.dict("os.environ", {}, clear=True), patch(
                "agent_runtime.client.RuntimeClient.send",
                return_value={"jobs": {"not": "a list"}}):
            status = runtime_status(st(), IDENTITY, PROJECT)
        self.assertFalse(status["connected"])
        self.assertEqual(status["reason"], "api_unreachable")


if __name__ == "__main__":
    unittest.main()
