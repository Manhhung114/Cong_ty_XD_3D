"""V7.0 signed lifecycle + CEO/3D monitoring security and regression tests."""
import unittest
from datetime import datetime, timedelta, timezone

from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT
from drive_storage.company_agents import run_agent
from drive_storage.live_agents import (
    execution_event_id, safe_failure_code, project_agent_activity,
    LIVE_WINDOW_SECONDS,
)
from drive_storage.monitoring import build_monitor_packet


class AgentLifecycleProjectionTests(unittest.TestCase):
    def setUp(self):
        CloudWorkflowTests.setUp(self)
        self.task_id = self.ws.create_task(
            self.editor, project_id=PROJECT,
            title="Kiểm tra bản vẽ tủ điện R01", dept="electrical",
            agent_id="ELE", assignee=self.editor["email"],
        )["id"]
        self.attempt = "a" * 32

    def tearDown(self):
        CloudWorkflowTests.tearDown(self)

    def test_task_working_does_not_fabricate_ai_running(self):
        self.ws.start_task(self.editor, project_id=PROJECT, task_id=self.task_id)
        state = self.ws.snapshot(self.reader)
        self.assertEqual(state["agentActivity"], [])
        self.assertEqual(state["agentRuns"], [])
        packet = build_monitor_packet(self.reader, state, self.ws.events())
        self.assertEqual(packet["agentActivity"], [])
        self.assertFalse(packet["capabilities"]["agentRunningHeartbeat"])
        self.assertTrue(packet["capabilities"]["signedAgentLifecycle"])

    def test_start_completed_attempt_correlates_and_blocks_replay(self):
        started = self.ws.record_agent_start(
            self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="preflight", attempt_id=self.attempt)
        self.assertFalse(started["existing"])
        activity = self.ws.snapshot(self.reader)["agentActivity"]
        self.assertEqual(len(activity), 1)
        self.assertIn(activity[0]["state"], ("started_unconfirmed", "stale"))
        self.assertFalse(activity[0]["hasHeartbeat"])
        self.assertEqual(activity[0]["evidence"], "agent.started")
        self.assertNotIn("api_key", str(activity))
        with self.assertRaises(PermissionError):
            self.ws.record_agent_start(
                self.reader, project_id=PROJECT, task_id=self.task_id,
                agent_id="ELE", mode="preflight", attempt_id="b" * 32)
        repeated = self.ws.record_agent_start(
            self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="preflight", attempt_id=self.attempt)
        self.assertTrue(repeated["existing"])
        self.assertFalse(repeated["completed"])
        result = run_agent(
            self.ws, self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="preflight", event_id=self.attempt,
        )
        self.assertTrue(result["reviewRequired"])
        state = self.ws.snapshot(self.reader)
        activity = state["agentActivity"][0]
        self.assertEqual(activity["state"], "completed")
        self.assertEqual(activity["attemptId"], self.attempt)
        self.assertEqual(activity["evidence"], "agent.completed")
        self.assertEqual(state["tasks"][0]["status"], "todo",
                         "Agent completion may not approve task")
        self.assertEqual(len(state["agentRuns"]), 1)
        again = self.ws.record_agent_start(
            self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="preflight", attempt_id=self.attempt)
        self.assertTrue(again["completed"])
        self.assertTrue(again["existing"])

    def test_failure_reason_is_bounded_and_not_private(self):
        self.ws.record_agent_start(
            self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="llm", attempt_id=self.attempt)
        with self.assertRaises(ValueError):
            self.ws.record_agent_failure(
                self.editor, project_id=PROJECT, task_id=self.task_id,
                agent_id="ELE", mode="llm", attempt_id=self.attempt,
                code="x-private-api-key")
        self.ws.record_agent_failure(
            self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="llm", attempt_id=self.attempt,
            code="quota")
        a = self.ws.snapshot(self.reader)["agentActivity"][0]
        self.assertEqual(a["state"], "failed")
        self.assertEqual(a["failureCode"], "quota")
        self.assertNotIn("x-private", str(a))
        # Unknown user cannot forge failed event for another execution.
        with self.assertRaises(PermissionError):
            self.ws.record_agent_failure(
                self.reader, project_id=PROJECT, task_id=self.task_id,
                agent_id="ELE", mode="llm", attempt_id=self.attempt,
                code="internal")
        with self.assertRaises(PermissionError):
            self.ws.record_agent_failure(
                self.admin, project_id=PROJECT, task_id=self.task_id,
                agent_id="ELE", mode="llm", attempt_id="f" * 32,
                code="internal")

    def test_stale_started_attempt_is_not_pretend_heartbeat(self):
        self.ws.record_agent_start(
            self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="expert", attempt_id=self.attempt)
        t = datetime.now(timezone.utc)+timedelta(seconds=LIVE_WINDOW_SECONDS+8)
        status = project_agent_activity(self.ws.snapshot(self.reader),
                                         self.ws.events(), now=t)
        self.assertEqual(status[0]["state"], "stale")
        self.assertFalse(status[0]["hasHeartbeat"])

    def test_scope_excludes_unauthorized_project_activity(self):
        self.ws.record_agent_start(
            self.editor, project_id=PROJECT, task_id=self.task_id,
            agent_id="ELE", mode="preflight", attempt_id=self.attempt)
        state = self.ws.snapshot(self.reader)
        outside_id = "project-folder-000002"
        injected = {
            "id":"f"*32, "at": datetime.now(timezone.utc).isoformat(),
            "actor":self.editor["email"],"project_id":outside_id,
            "action":"agent.started",
            "data":{"task_id":"b"*32,"agent_id":"ELE",
                    "attempt_id":"b"*32,"mode":"preflight"},
        }
        output = project_agent_activity(state, [*self.ws.events(),injected])
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0]["projectId"], PROJECT)
        monitor = build_monitor_packet(self.reader, state,
                                      [*self.ws.events(),injected])
        self.assertTrue(all(x["projectId"]==PROJECT for x in monitor["agentActivity"]))
        self.assertTrue(all(e["projectId"]==PROJECT for e in monitor["events"]))

    def test_event_identifier_and_public_failure_code(self):
        self.assertEqual(len(execution_event_id("a"*32,"started")),32)
        self.assertNotEqual(execution_event_id("a"*32,"started"),
                            execution_event_id("a"*32,"failed"))
        with self.assertRaises(ValueError):
            execution_event_id("bad","started")
        self.assertEqual(safe_failure_code(PermissionError("SECRET")),"permission")
        self.assertEqual(safe_failure_code(ValueError("SECRET")),"validation")
        self.assertEqual(safe_failure_code(RuntimeError("HTTP 429 SECRET")),"quota")
        self.assertEqual(safe_failure_code(RuntimeError("API_KEY SECRET")),"internal")


if __name__=="__main__":
    unittest.main()
