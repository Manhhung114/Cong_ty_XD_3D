"""V6.8.0: signed accept/return workflow and persistent UX feedback.

Tests are fully local with mock Drive, no real project/API secrets involved.
"""
import io
import unittest
from urllib.error import HTTPError, URLError
from pathlib import Path

from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT
from drive_storage.company_agents import _request_json


class ReviewDecisionStatusTests(unittest.TestCase):
    def setUp(self):
        CloudWorkflowTests.setUp(self)
        self.tid = self.ws.create_task(
            self.editor, project_id=PROJECT,
            title="Kiểm tra bản vẽ tủ điện", dept="electrical",
            assignee="Kỹ sư điện", agent_id="ELE",
        )["id"]

    def tearDown(self):
        CloudWorkflowTests.tearDown(self)

    def task(self):
        return next(t for t in self.ws.snapshot(self.reader)["tasks"]
                    if t["id"] == self.tid)

    def test_returned_task_requires_rework_and_new_submission(self):
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=self.tid,
                            summary="Rà soát thiết bị và kiểm kê bản vẽ DXF")
        self.assertEqual(self.task()["status"], "review")
        self.assertEqual(self.task()["lastReviewDecision"], "submitted")
        with self.assertRaises(ValueError):
            self.ws.review_task(self.admin, project_id=PROJECT, task_id=self.tid,
                                decision="reject", comment="Sai")
        self.ws.review_task(self.admin, project_id=PROJECT, task_id=self.tid,
                            decision="reject",
                            comment="Thiếu kiểm tra điện áp thiết bị và dòng định mức")
        returned = self.task()
        self.assertEqual(returned["status"], "working")
        self.assertEqual(returned["lastReviewDecision"], "reject")
        self.assertEqual(returned["lastReviewer"], self.admin["email"])
        self.assertIn("dòng định mức", returned["lastReviewNote"])
        self.assertTrue(returned["lastReviewedAt"])
        self.assertEqual(returned["reviewHistory"][-1]["decision"], "reject")
        self.assertTrue(any(e["action"] == "task.returned" for e in self.ws.events()))
        # The old rejection remains in signed history after correction.
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=self.tid,
                            summary="Đã bổ sung kiểm tra dòng định mức và điện áp")
        self.assertEqual(self.task()["lastReviewDecision"], "submitted")
        self.assertEqual(self.task()["reviewHistory"][-2]["decision"], "reject")
        self.ws.review_task(self.admin, project_id=PROJECT, task_id=self.tid,
                            decision="approve", comment="Chấp thuận sau thẩm tra")
        accepted = self.task()
        self.assertEqual(accepted["status"], "done")
        self.assertEqual(accepted["lastReviewDecision"], "approve")
        self.assertEqual(accepted["lastReviewer"], self.admin["email"])
        self.assertEqual(accepted["lastReviewNote"], "Chấp thuận sau thẩm tra")
        self.assertEqual(len(accepted["reviewHistory"]), 4)
        self.assertTrue(any(e["action"] == "task.approved" for e in self.ws.events()))

    def test_only_admin_can_decide_and_no_duplicate_review(self):
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=self.tid,
                            summary="Trình báo cáo đã được kỹ sư rà soát")
        with self.assertRaises(PermissionError):
            self.ws.review_task(self.editor, project_id=PROJECT, task_id=self.tid,
                                decision="approve")
        self.ws.review_task(self.admin, project_id=PROJECT, task_id=self.tid,
                            decision="reject", comment="Cần làm rõ dữ liệu nguồn")
        with self.assertRaises(ValueError):
            self.ws.review_task(self.admin, project_id=PROJECT, task_id=self.tid,
                                decision="approve")


class AgentProviderErrorGuidanceTests(unittest.TestCase):
    def test_safe_429_message_without_leaking_provider_body(self):
        private = "SUPERSECRET"
        for code, expected in [(400,"400"), (401,"401"), (403,"403"),
                               (404,"404"), (429,"429"), (503,"503")]:
            with self.subTest(code=code):
                def unavailable(*args, **kwargs):
                    raise HTTPError(
                        "https://example.com/?key=" + private, code,
                        "provider response " + private, None, io.BytesIO(private.encode()))
                with self.assertRaisesRegex(RuntimeError, expected) as caught:
                    _request_json("https://example.com", {"x-goog-api-key": private},
                                  {"test": True}, opener=unavailable)
                self.assertNotIn(private, str(caught.exception))
        def network(*args, **kwargs):
            raise URLError("debug " + private)
        with self.assertRaises(RuntimeError) as caught:
            _request_json("https://example.com", {"Authorization": private},
                          {"test": True}, opener=network)
        self.assertNotIn(private, str(caught.exception))

    def test_ui_and_dialogs_explain_confirmation_not_autoapproval(self):
        root = Path(__file__).resolve().parents[1]
        ui = (root / "drive_storage/workspace_ui.py").read_text(encoding="utf8")
        app = (root / "streamlit_app.py").read_text(encoding="utf8")
        company = (root / "drive_storage/company_ui.py").read_text(encoding="utf8")
        document = (root / "drive_storage/document_control_ui.py").read_text(encoding="utf8")
        self.assertIn("Gửi lại báo cáo đã sửa", ui)
        self.assertIn("Không chấp thuận / Yêu cầu sửa", ui)
        self.assertIn("Đã trả lại công việc và lưu lý do", ui)
        self.assertIn("Kỹ sư cần kiểm chứng", company)
        self.assertIn("Không tạo báo cáo giả", company)
        self.assertIn('on_dismiss=lambda: st.session_state.pop("xd_workspace_dialog", None)', company)
        self.assertIn('on_dismiss=lambda: st.session_state.pop("xd_workspace_dialog", None)', document)
        self.assertIn("xd_last_action_notice", app)
        self.assertIn('shared_state["lastActionNotice"] = notice', app)

if __name__ == "__main__":
    unittest.main()
