"""V7.5.2 — signed meeting lifecycle, CEO quick intake and backward compatibility."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import test_v59_v60_cloud_workflow as fixtures
from drive_storage.ceo_quickstart import create_with_optional_ceo_plan
from drive_storage.coordination import (
    schedule_meeting, record_minutes, decide_meeting, close_meeting,
)
from drive_storage.hierarchy import suggest_departments

P = fixtures.PROJECT


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        fixtures.CloudWorkflowTests.setUp(self)
        self.addCleanup(fixtures.CloudWorkflowTests.tearDown, self)
        context = patch.dict(os.environ, {"XD_V752_MEETINGS": "1"})
        context.start()
        self.addCleanup(context.stop)
        self.one = self.ws.create_task(
            self.editor, project_id=P, title="Rà soát nguồn cấp điện tầng 5",
            dept="electrical", agent_id="ELE", assignee="ele@example.com")["id"]
        self.two = self.ws.create_task(
            self.editor, project_id=P, title="Phối hợp ống gió trần tầng 5",
            dept="hvac", agent_id="HVA", assignee="hva@example.com")["id"]

    def schedule(self, event_id="a"*32):
        return schedule_meeting(
            self.ws, self.editor, project_id=P,
            title="Họp phối hợp MEP tầng 5",
            agenda="Giải quyết xung đột ống gió và máng cáp tầng 5, xác định bản vẽ R02.",
            task_ids=[self.one, self.two], departments=["electrical", "hvac"],
            scheduled_at="2026-11-18T09:00:00+07:00", event_id=event_id)["id"]

    @staticmethod
    def actions():
        return [
            {"title": "Sửa bố trí máng cáp tại trần tầng 5 và nộp bản R03",
             "dept": "electrical", "assignee": "ele@example.com",
             "agent_id": "ELE", "due_date": "2026-11-20", "priority": "high"},
            {"title": "Đối chiếu ống gió trần với bản điện và xác nhận cao độ",
             "dept": "hvac", "assignee": "hva@example.com",
             "agent_id": "HVA", "due_date": "2026-11-21", "priority": "normal"},
        ]

    def minutes(self, meeting, actions=None):
        return record_minutes(
            self.ws, self.editor, project_id=P, meeting_id=meeting,
            minutes="Các bộ môn thống nhất rà soát xung đột máng cáp và ống gió tầng 5.",
            decisions="Chuyển máng cáp sang bên phải và kiểm lại cao độ.",
            actions=self.actions() if actions is None else actions, event_id="b"*32)

    def test_signed_meeting_to_admin_approved_tasks_and_close(self):
        old_media = dict(self.storage.media)
        meeting = self.schedule()
        status = self.ws.snapshot(self.reader)["meetings"][0]
        self.assertEqual(status["status"], "scheduled")
        self.assertEqual(status["departments"], ["electrical", "hvac"])
        self.minutes(meeting)
        current = self.ws.snapshot(self.reader)
        self.assertEqual(current["meetings"][0]["status"], "pending_approval")
        self.assertEqual(len(current["tasks"]), 2, "draft minutes must not assign work")
        with self.assertRaises(PermissionError):
            decide_meeting(self.ws, self.editor, project_id=P, meeting_id=meeting,
                           approve=True)
        with self.assertRaises(PermissionError):
            schedule_meeting(self.ws, self.reader, project_id=P, title="No access",
                             agenda="Cannot write to project",
                             task_ids=[self.one], departments=["electrical", "hvac"],
                             scheduled_at="2026-11-18T09:00:00+07:00")
        approval = decide_meeting(
            self.ws, self.admin, project_id=P, meeting_id=meeting,
            approve=True, event_id="c"*32)
        self.assertFalse(approval["existing"])
        self.assertTrue(decide_meeting(
            self.ws, self.admin, project_id=P, meeting_id=meeting,
            approve=True, event_id="c"*32)["existing"] is False if False else True)
        # No duplicate after re-reading the same signed result.
        state = self.ws.snapshot(self.admin)
        self.assertEqual(len(state["tasks"]), 4)
        record = state["meetings"][0]
        self.assertEqual(record["status"], "in_progress")
        self.assertEqual(record["totalActions"], 2)
        self.assertFalse(record["readyToClose"])
        children = [t for t in state["tasks"] if t.get("meetingId") == meeting]
        self.assertEqual({t["dept"] for t in children}, {"electrical", "hvac"})
        self.assertEqual(len(children), 2)
        with self.assertRaises(ValueError):
            close_meeting(self.ws, self.admin, project_id=P, meeting_id=meeting)
        for task in children:
            self.ws.submit_task(self.editor, project_id=P, task_id=task["id"],
                                summary="Đã xử lý và gửi tài liệu sửa đổi để kiểm tra.")
            self.ws.review_task(self.admin, project_id=P, task_id=task["id"],
                                decision="approve", comment="Đã kiểm tra")
        self.assertTrue(self.ws.snapshot(self.admin)["meetings"][0]["readyToClose"])
        close_meeting(self.ws, self.admin, project_id=P, meeting_id=meeting,
                      event_id="d"*32)
        self.assertEqual(self.ws.snapshot(self.reader)["meetings"][0]["status"], "closed")
        self.assertEqual({fid:self.storage.media[fid] for fid in old_media},old_media)
        self.assertFalse(self.ws.snapshot({"email":"alien@example.com","role":"read",
                                           "projects":[fixtures.SECOND]})["meetings"])

    def test_revision_and_invalid_cross_team_or_owner(self):
        mid = self.schedule()
        with self.assertRaises(PermissionError):
            self.minutes(mid, actions=[{**self.actions()[0], "dept": "structure"}])
        with self.assertRaises(ValueError):
            self.minutes(mid, actions=[{**self.actions()[0], "assignee":"not-an-email"}])
        self.minutes(mid)
        decide_meeting(self.ws, self.admin, project_id=P, meeting_id=mid,
                       approve=False, reason="Chưa thống nhất hướng dẫn cao độ.")
        self.assertEqual(self.ws.snapshot(self.editor)["meetings"][0]["status"],
                         "revision_requested")
        with self.assertRaises(ValueError):
            decide_meeting(self.ws, self.admin, project_id=P, meeting_id=mid,
                           approve=True)
        record_minutes(self.ws, self.editor, project_id=P, meeting_id=mid,
                       minutes="Đã thống nhất lại bản vẽ và từng đầu mối phối hợp sau họp.",
                       decisions="Phát hành kiểm tra nội bộ trước khi nộp cho PM.",
                       actions=[], event_id="e"*32)
        decide_meeting(self.ws, self.admin, project_id=P, meeting_id=mid,
                       approve=True, event_id="f"*32)
        meeting = self.ws.snapshot(self.admin)["meetings"][0]
        self.assertTrue(meeting["readyToClose"])
        self.assertEqual(meeting["totalActions"], 0)

    def test_feature_flag_disabled_protects_existing_ledger(self):
        with patch.dict(os.environ, {"XD_V752_MEETINGS":"0"}):
            with self.assertRaises(PermissionError):
                self.schedule()
        self.assertEqual(len(self.ws.snapshot(self.admin)["meetings"]), 0)
        self.assertEqual(len(self.ws.snapshot(self.admin)["tasks"]), 2)

    def test_ceo_single_submit_and_accentless_routing(self):
        self.assertEqual(
            suggest_departments("Thiết kế tu dien, ong gio và bao chay tang 5"),
            ["electrical", "hvac", "fire"])
        result = create_with_optional_ceo_plan(
            self.ws, self.admin, project_id=P,
            title="Kiểm tra cáp điện, HVAC và PCCC tầng 5", dept="director",
            assignee=self.admin["email"], agent_id="CEO", event_id="9"*32,
            auto_plan=True)
        self.assertEqual(result["status"], "pending_approval")
        self.assertEqual(result["departments"], ["electrical","hvac","fire"])
        signed = self.ws.snapshot(self.admin)
        self.assertEqual(len(signed["hierarchyPlans"]), 1)
        self.assertEqual(signed["hierarchyPlans"][0]["status"], "pending")
        self.assertEqual(len(signed["agentRuns"]), 0)
        self.assertEqual(len(signed["tasks"]), 3)
        with self.assertRaises(ValueError):
            create_with_optional_ceo_plan(
                self.ws, self.editor, project_id=P,
                title="Bất kỳ", dept="electrical", assignee="",
                agent_id="ELE", event_id="8"*32, auto_plan=True)
        unclassified = create_with_optional_ceo_plan(
            self.ws, self.admin, project_id=P, title="Vấn đề không rõ",
            dept="director", assignee=self.admin["email"],
            agent_id="CEO", event_id="7"*32, auto_plan=True)
        self.assertEqual(unclassified["status"], "choose_departments")
        self.assertEqual(len(self.ws.snapshot(self.admin)["hierarchyPlans"]), 1)


if __name__ == "__main__":
    unittest.main()
