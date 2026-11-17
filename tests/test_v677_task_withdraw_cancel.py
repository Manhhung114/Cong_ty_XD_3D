"""V6.7.7: signed non-destructive task withdrawal/cancellation and role regression."""
from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT
from drive_storage.company_agents import run_agent, create_handoff


class TaskWithdrawCancelTests(CloudWorkflowTests):
    def test_withdraw_resets_assignment_and_preserves_agent_draft_and_audit(self):
        task_id = self.ws.create_task(
            self.editor, project_id=PROJECT, title="Kiểm tra hồ sơ điện",
            dept="electrical", assignee="Kỹ sư điện", agent_id="ELE",
        )["id"]
        self.ws.start_task(self.editor, project_id=PROJECT, task_id=task_id)
        run_agent(self.ws, self.editor, project_id=PROJECT, task_id=task_id,
                  agent_id="ELE", mode="preflight")
        event = self.ws.withdraw_task(
            self.editor, project_id=PROJECT, task_id=task_id,
            reason="Thu hồi do thay đổi kế hoạch kiểm tra",
        )
        self.assertFalse(event["existing"])
        snap = self.ws.snapshot(self.reader)
        task = next(t for t in snap["tasks"] if t["id"] == task_id)
        self.assertEqual(task["status"], "todo")
        self.assertEqual(task["assignee"], "")
        self.assertEqual(task["assignedAgentId"], "")
        self.assertEqual(task["withdrawnBy"], self.editor["email"])
        self.assertIn("thay đổi kế hoạch", task["withdrawReason"])
        self.assertEqual(task["reviewHistory"][-1]["decision"], "withdraw")
        self.assertEqual(len(snap["agentRuns"]), 1)
        self.assertEqual(snap["agentRuns"][0]["taskId"], task_id)
        self.assertTrue(any(e["action"] == "task.unassigned" for e in snap["events"]))
        self.assertTrue(any(e["action"] == "task.unassigned" for e in self.ws.events()))
        self.ws.assign_task(self.editor, project_id=PROJECT, task_id=task_id,
                            assignee="Kỹ sư thay thế", agent_id="ELE")
        assigned = self.ws.snapshot(self.reader)["tasks"][0]
        self.assertEqual(assigned["assignee"], "Kỹ sư thay thế")
        self.assertEqual(assigned["assignedAgentId"], "ELE")
        self.assertEqual(assigned["withdrawnAt"], "")
        self.assertEqual(assigned["reviewHistory"][-1]["decision"], "withdraw")
        self.assertEqual(len(self.ws.snapshot(self.reader)["agentRuns"]), 1)

    def test_admin_cancel_active_task_preserves_history_and_blocks_future_actions(self):
        tid = self.ws.create_task(
            self.editor, project_id=PROJECT, title="Thi công hệ thống HVAC",
            dept="hvac", assignee="Nhân sự HVAC",
        )["id"]
        self.ws.start_task(self.editor, project_id=PROJECT, task_id=tid)
        result = self.ws.cancel_task(
            self.admin, project_id=PROJECT, task_id=tid,
            reason="Hủy do chủ đầu tư dừng hạng mục",
        )
        self.assertFalse(result["existing"])
        task = next(t for t in self.ws.snapshot(self.reader)["tasks"] if t["id"] == tid)
        self.assertEqual(task["status"], "cancelled")
        self.assertEqual(task["assignee"], "")
        self.assertEqual(task["assignedAgentId"], "")
        self.assertEqual(task["cancelledBy"], self.admin["email"])
        self.assertEqual(task["reviewHistory"][-1]["decision"], "cancel")
        self.assertIn("chủ đầu tư", task["cancelReason"])
        self.assertTrue(any(e["action"] == "task.cancelled" for e in self.ws.events()))
        with self.assertRaises(ValueError):
            self.ws.assign_task(self.editor, project_id=PROJECT, task_id=tid, agent_id="HVAC")
        with self.assertRaises(ValueError):
            self.ws.start_task(self.editor, project_id=PROJECT, task_id=tid)
        with self.assertRaises(ValueError):
            self.ws.submit_task(self.editor, project_id=PROJECT, task_id=tid,
                                summary="Đã kết thúc đầy đủ công việc")
        with self.assertRaises(ValueError):
            self.ws.cancel_task(self.admin, project_id=PROJECT, task_id=tid,
                                reason="Thử hủy một lần nữa")
        with self.assertRaises(PermissionError):
            run_agent(self.ws, self.editor, project_id=PROJECT, task_id=tid,
                      agent_id="HVAC", mode="preflight")
        with self.assertRaises(PermissionError):
            create_handoff(self.ws, self.editor, project_id=PROJECT, task_id=tid,
                           target_department="electrical",
                           reason="Yêu cầu phối hợp từ nhiệm vụ đã hủy")

    def test_admin_can_cancel_submitted_task_but_not_approved(self):
        t1 = self.ws.create_task(self.editor, project_id=PROJECT,
                                 title="Thẩm tra hồ sơ kết cấu", dept="structure")["id"]
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=t1,
                            summary="Hồ sơ đã trình kiểm tra phê duyệt")
        self.ws.cancel_task(self.admin, project_id=PROJECT, task_id=t1,
                            reason="Hủy trước khi duyệt vì đổi phạm vi")
        a = next(t for t in self.ws.snapshot(self.reader)["tasks"] if t["id"] == t1)
        self.assertEqual(a["status"], "cancelled")
        self.assertEqual(a["reviewHistory"][0]["decision"], "submitted")
        self.assertEqual(a["reviewHistory"][-1]["decision"], "cancel")
        t2 = self.ws.create_task(self.editor, project_id=PROJECT,
                                 title="Duyệt hồ sơ PCCC", dept="fire")["id"]
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=t2,
                            summary="Báo cáo đủ điều kiện trình phê duyệt")
        self.ws.review_task(self.admin, project_id=PROJECT, task_id=t2,
                            decision="approve")
        with self.assertRaises(ValueError):
            self.ws.cancel_task(self.admin, project_id=PROJECT, task_id=t2,
                                reason="Không được hủy nhiệm vụ hoàn tất")

    def test_withdraw_and_cancel_permissions_reason_and_cross_project(self):
        tid = self.ws.create_task(self.editor, project_id=PROJECT,
                                  title="Rà soát điện tầng ba", dept="electrical",
                                  assignee="Phụ trách")["id"]
        with self.assertRaises(PermissionError):
            self.ws.withdraw_task(self.reader, project_id=PROJECT, task_id=tid,
                                  reason="Người xem không được rút")
        with self.assertRaises(PermissionError):
            self.ws.cancel_task(self.editor, project_id=PROJECT, task_id=tid,
                                reason="Nhân viên không được hủy")
        with self.assertRaises(PermissionError):
            self.ws.cancel_task(self.reader, project_id=PROJECT, task_id=tid,
                                reason="Người xem không được hủy")
        with self.assertRaises(ValueError):
            self.ws.withdraw_task(self.editor, project_id=PROJECT, task_id=tid,
                                  reason="Sai")
        with self.assertRaises(ValueError):
            self.ws.cancel_task(self.admin, project_id=PROJECT, task_id=tid,
                                reason="Sai")
        with self.assertRaises(PermissionError):
            self.ws.withdraw_task(self.editor, project_id="project-folder-000002",
                                  task_id=tid, reason="Sai phạm vi của dự án")
        self.ws.withdraw_task(self.editor, project_id=PROJECT, task_id=tid,
                              reason="Cần kiểm tra phân công lại")
        with self.assertRaises(ValueError):
            self.ws.withdraw_task(self.editor, project_id=PROJECT, task_id=tid,
                                  reason="Đã thu hồi trước đó")
        self.assertEqual(self.ws.snapshot(self.reader)["tasks"][0]["status"], "todo")
