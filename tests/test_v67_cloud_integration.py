"""V6.7 integration with existing HMAC-signed, project-scoped workflow."""
import unittest

from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT, SECOND
from drive_storage.company_agents import create_handoff, resolve_handoff


class MonitorLedgerIntegration(unittest.TestCase):
    def setUp(self):
        CloudWorkflowTests.setUp(self)

    def tearDown(self):
        CloudWorkflowTests.tearDown(self)

    def test_monitor_snapshot_reuses_signed_events_and_separates_both_systems(self):
        electrical = self.ws.create_task(
            self.editor, project_id=PROJECT,
            title="Điện phối hợp kiến trúc", dept="electrical",
        )["id"]
        structure = self.ws.create_task(
            self.editor, project_id=PROJECT,
            title="Kết cấu phối hợp MEP", dept="structure",
        )["id"]
        first = create_handoff(
            self.ws, self.editor, project_id=PROJECT, task_id=electrical,
            target_department="structure",
            reason="Xin kiểm tra vị trí hộp kỹ thuật xuyên sàn",
        )
        second = create_handoff(
            self.ws, self.editor, project_id=PROJECT, task_id=structure,
            target_department="bim",
            reason="Xin kiểm tra phối hợp kết cấu với BIM MEP",
        )
        snapshot = self.ws.snapshot(self.reader, include_monitor=True)
        self.assertEqual(snapshot["role"], "read")
        monitor = snapshot["monitorData"]
        self.assertEqual(monitor["schema"], "XD_MEP_MONITOR_V67")
        self.assertEqual(len(snapshot["projects"]), 1)
        self.assertEqual(monitor["authorizedProjects"], 1)
        self.assertEqual(len(monitor["tasks"]), 2)
        self.assertEqual(len(monitor["handoffs"]), 2)
        self.assertEqual(
            {x["relation"] for x in monitor["handoffs"]},
            {"mep_to_xd", "xd_to_mep"},
        )
        actions = [e["action"] for e in monitor["events"]]
        self.assertEqual(actions.count("handoff.requested"), 2)
        self.assertNotIn("monitorData", self.ws.snapshot(self.reader))

        resolve_handoff(
            self.ws, self.editor, project_id=PROJECT,
            handoff_id=first["id"],
            response="Đã đối chiếu vị trí và gửi kỹ sư rà lại bản vẽ",
        )
        newer = self.ws.snapshot(self.reader, include_monitor=True)["monitorData"]
        close = next(e for e in newer["events"] if e["action"] == "handoff.resolved")
        self.assertEqual(close["relation"], "mep_to_xd")
        self.assertEqual(close["sourceDept"], "electrical")
        self.assertEqual(close["targetDept"], "structure")

    def test_admin_only_projects_are_not_exposed_to_limited_reader(self):
        self.ws.create_task(
            self.admin, project_id=SECOND,
            title="Dự án bí mật không cấp nhân viên", dept="architecture",
        )
        monitor = self.ws.snapshot(self.reader, include_monitor=True)["monitorData"]
        self.assertTrue(all(t["projectId"] == PROJECT for t in monitor["tasks"]))
        self.assertTrue(all(e["projectId"] == PROJECT for e in monitor["events"]))


if __name__ == "__main__":
    unittest.main()
