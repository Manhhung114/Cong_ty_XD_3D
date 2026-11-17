"""Regression for 14:06 video: editor sees no cancel action on unassigned started task.

The 'update' role may reset started-but-unassigned work to todo with signed
history. Full cancellation remains Admin-only, with no hidden permission bypass.
"""
from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT


class UnassignedWorkingRecallTests(CloudWorkflowTests):
    def test_editor_can_reset_working_task_with_no_human_or_agent(self):
        tid = self.ws.create_task(
            self.editor, project_id=PROJECT,
            title="Đánh giá bản vẽ điện", dept="electrical",
            assignee="", agent_id="",
        )["id"]
        self.ws.start_task(self.editor, project_id=PROJECT, task_id=tid)
        task = next(t for t in self.ws.snapshot(self.reader)["tasks"] if t["id"] == tid)
        self.assertEqual(task["status"], "working")
        self.assertEqual(task["assignee"], "")
        self.assertEqual(task["assignedAgentId"], "")
        event = self.ws.withdraw_task(
            self.editor, project_id=PROJECT, task_id=tid,
            reason="Đưa về Chờ xử lý vì chưa có người nhận",
        )
        self.assertFalse(event["existing"])
        snap = self.ws.snapshot(self.reader)
        task = next(t for t in snap["tasks"] if t["id"] == tid)
        self.assertEqual(task["status"], "todo")
        self.assertEqual(task["withdrawnBy"], self.editor["email"])
        self.assertEqual(task["assignedAgentId"], "")
        self.assertEqual(task["assignee"], "")
        self.assertIn("chưa có người nhận", task["withdrawReason"])
        self.assertEqual(task["reviewHistory"][-1]["decision"], "withdraw")
        self.assertTrue(any(e["action"] == "task.unassigned" for e in self.ws.events()))
        # The editor does not get permanent-cancel privileges from this reset.
        with self.assertRaises(PermissionError):
            self.ws.cancel_task(
                self.editor, project_id=PROJECT, task_id=tid,
                reason="Thử hủy hoàn toàn công việc",
            )

    def test_nothing_to_recall_when_already_todo_unassigned(self):
        tid = self.ws.create_task(
            self.editor, project_id=PROJECT,
            title="Hồ sơ chưa giao", dept="electrical",
        )["id"]
        with self.assertRaisesRegex(ValueError, "chỉ Admin được hủy"):
            self.ws.withdraw_task(
                self.editor, project_id=PROJECT, task_id=tid,
                reason="Không có phân công để thu hồi",
            )
        self.assertEqual(self.ws.snapshot(self.reader)["tasks"][0]["status"], "todo")
        # Admin can explicitly cancel the same unassigned task with a reason.
        self.ws.cancel_task(
            self.admin, project_id=PROJECT, task_id=tid,
            reason="Admin xác nhận không tiếp tục triển khai",
        )
        self.assertEqual(self.ws.snapshot(self.reader)["tasks"][0]["status"], "cancelled")

    def test_viewer_cannot_reset_and_editor_cannot_cross_project(self):
        tid = self.ws.create_task(
            self.editor, project_id=PROJECT,
            title="Đã bắt đầu nhưng chưa giao", dept="electrical",
        )["id"]
        self.ws.start_task(self.editor, project_id=PROJECT, task_id=tid)
        with self.assertRaises(PermissionError):
            self.ws.withdraw_task(
                self.reader, project_id=PROJECT, task_id=tid,
                reason="Tài khoản chỉ đọc không được phép",
            )
        with self.assertRaises(PermissionError):
            self.ws.withdraw_task(
                self.editor, project_id="project-folder-000002", task_id=tid,
                reason="Không thuộc dự án được cấp quyền",
            )

    def test_server_dialog_explains_role_and_unassigned_working(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] /
                  "drive_storage/workspace_ui.py").read_text(encoding="utf8")
        self.assertIn('if eligible and (assigned or task["status"] == "working"):', source)
        self.assertIn("Chỉ Admin mới được Hủy công việc hoàn toàn", source)
        self.assertIn("Đặt lại Chờ xử lý", source)
        self.assertIn('if task["status"] == "todo" and not assigned:', source)
