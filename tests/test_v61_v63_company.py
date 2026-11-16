"""Company integration: 18 specialist contracts, real/simulated boundaries, handoffs and signed audit."""
import hashlib
import io
import json
import unittest

from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT, SECOND
from drive_storage.company_agents import (
    agents, public_catalog, preflight, company_metrics, run_agent, call_provider,
    create_handoff, resolve_handoff, export_integrity_report,
)


class Response:
    def __init__(self, data):
        self.data = json.dumps(data).encode("utf8")
    def __enter__(self):
        return self
    def __exit__(self, *unused):
        pass
    def read(self, limit):
        return self.data[:limit]


class AgentCompanyTests(CloudWorkflowTests):
    def test_specialist_catalog_is_complete_and_mapped(self):
        profiles = agents()
        self.assertEqual(len(profiles), 18)
        self.assertEqual(set(profiles), {
            "CEO", "PM", "ELE", "HVA", "PLU", "FIR", "BIM", "QSU", "QAC",
            "DOC", "ARC", "STR", "XBI", "XQS", "PLN", "SIT", "HSE", "MAT",
        })
        self.assertEqual(profiles["QSU"]["department"], "qs")
        self.assertIn("BIM", profiles["ELE"]["partners"])
        for profile in profiles.values():
            self.assertTrue(profile["mission"])
            self.assertTrue(profile["output"])
            self.assertTrue(profile["prohibition"])
            self.assertGreaterEqual(len(profile["skills"]), 3)
        self.assertEqual(len(public_catalog()), 18)

    def test_agent_preflight_is_audited_but_not_claimed_to_be_llm(self):
        task_id = self.ws.create_task(
            self.editor, project_id=PROJECT, title="Rà soát sơ đồ cấp điện",
            dept="electrical", assignee="Kỹ sư Điện",
        )["id"]
        state = self.ws.snapshot(self.editor)
        info = preflight(state, PROJECT, task_id, "ELE")
        self.assertIn("Chưa có hồ sơ", info["missing"][0])
        self.assertIn("dueDate", info["task"])
        with self.assertRaises(PermissionError):
            preflight(state, PROJECT, task_id, "HVA")
        with self.assertRaises(PermissionError):
            run_agent(self.ws, self.reader, project_id=PROJECT,
                      task_id=task_id, agent_id="ELE")
        with self.assertRaises(PermissionError):
            run_agent(self.ws, self.editor, project_id=SECOND,
                      task_id=task_id, agent_id="ELE")

        eid = "e" * 32
        result = run_agent(self.ws, self.editor, project_id=PROJECT, task_id=task_id,
                           agent_id="ELE", event_id=eid)
        self.assertFalse(result["existing"])
        self.assertEqual(result["provider"], "none")
        self.assertIn("KHÔNG PHẢI AI", result["draft"])
        report = self.ws.snapshot(self.admin)["agentRuns"][0]
        self.assertEqual(report["actor"], self.editor["email"])
        self.assertEqual(report["mode"], "preflight")
        self.assertTrue(report["reviewRequired"])
        self.assertEqual(report["agentId"], "ELE")
        self.assertEqual(self.ws.snapshot(self.admin)["tasks"][0]["status"], "todo")
        # A retry must not add a duplicate journal record.
        again = run_agent(self.ws, self.editor, project_id=PROJECT, task_id=task_id,
                          agent_id="ELE", event_id=eid)
        self.assertTrue(again["existing"])
        self.assertEqual(len(self.ws.snapshot(self.admin)["agentRuns"]), 1)

    def test_company_kpis_from_authorized_data_only(self):
        self.ws.create_task(self.editor, project_id=PROJECT, title="Quá hạn thử",
                            dept="electrical", assignee="", due_date="2025-01-01")
        state = self.ws.snapshot(self.reader)
        metric = company_metrics(state, today="2026-11-16")
        self.assertEqual(metric["projects"], 1)
        self.assertEqual(metric["overdue"], 1)
        self.assertEqual(metric["unassigned"], 1)
        self.assertEqual(metric["tasks"], 1)
        self.assertTrue(metric["alerts"])
        other = self.ws.snapshot(self.admin)
        self.assertEqual(company_metrics(other, today="2026-11-16")["projects"], 2)

    def test_interdepartment_handoff_is_audited_and_role_scoped(self):
        tid = self.ws.create_task(self.editor, project_id=PROJECT,
                                  title="Kiểm tra va chạm ống gió",
                                  dept="hvac")["id"]
        with self.assertRaises(PermissionError):
            create_handoff(self.ws, self.reader, project_id=PROJECT, task_id=tid,
                           target_department="bim", reason="Cần xác minh mô hình trước nghiệm thu")
        with self.assertRaises(ValueError):
            create_handoff(self.ws, self.editor, project_id=PROJECT, task_id=tid,
                           target_department="hvac", reason="Bộ môn nguồn không được tự chuyển")
        record = create_handoff(self.ws, self.editor, project_id=PROJECT, task_id=tid,
                                target_department="bim", reason="Đối chiếu mô hình và kiểm tra giao diện HVAC")
        handoff_id = record["id"]
        current = self.ws.snapshot(self.admin)["handoffs"][0]
        self.assertEqual(current["status"], "open")
        self.assertEqual(current["targetDept"], "bim")
        with self.assertRaises(ValueError):
            create_handoff(self.ws, self.editor, project_id=PROJECT, task_id=tid,
                           target_department="bim", reason="Yêu cầu phối hợp trùng")
        with self.assertRaises(PermissionError):
            resolve_handoff(self.ws, self.reader, project_id=PROJECT,
                            handoff_id=handoff_id, response="Đã cập nhật mô hình xác nhận")
        resolve_handoff(self.ws, self.admin, project_id=PROJECT,
                        handoff_id=handoff_id,
                        response="Đã tổng hợp vấn đề và giao lại kỹ sư HVAC")
        done = self.ws.snapshot(self.editor)["handoffs"][0]
        self.assertEqual(done["status"], "resolved")
        self.assertEqual(done["resolvedBy"], self.admin["email"])
        self.assertEqual(company_metrics(self.ws.snapshot(self.editor))["handoffsOpen"], 0)

    def test_real_openai_request_uses_server_key_and_no_document_bytes(self):
        task_id = self.ws.create_task(
            self.editor, project_id=PROJECT, title="Kiểm tra khối lượng MEP",
            dept="qs", assignee="QS",
        )["id"]
        requests = []
        def opener(req, timeout):
            requests.append(req)
            self.assertEqual(req.full_url, "https://api.openai.com/v1/chat/completions")
            self.assertEqual(timeout, 25)
            self.assertIn("secret-token", req.get_header("Authorization"))
            payload = json.loads(req.data)
            self.assertEqual(payload["model"], "gpt-4.1-mini")
            self.assertNotIn("secret-token", req.data.decode("utf8"))
            self.assertIn("metadata", payload["messages"][0]["content"].lower())
            return Response({"choices": [{"message": {
                "content": ("Báo cáo dự thảo cho kỹ sư: thiếu bảng khối lượng và đơn giá. "
                            "Cần đối chiếu hồ sơ BOQ có phê duyệt, yêu cầu QS xác minh. ") * 2
            }}]})
        config = {"provider": "openai", "api_key": "secret-token", "model": "gpt-4.1-mini"}
        with self.assertRaises(PermissionError):
            run_agent(self.ws, self.editor, project_id=PROJECT, task_id=task_id,
                      agent_id="QSU", mode="llm", ai_config=config, consent=False)
        result = run_agent(self.ws, self.editor, project_id=PROJECT, task_id=task_id,
                           agent_id="QSU", mode="llm", ai_config=config,
                           consent=True, opener=opener)
        self.assertEqual(len(requests), 1)
        self.assertEqual(result["provider"], "openai")
        self.assertNotIn("secret-token", json.dumps(self.ws.snapshot(self.admin)))
        self.assertTrue(self.ws.snapshot(self.admin)["agentRuns"][0]["reviewRequired"])
        with self.assertRaises(ValueError):
            call_provider({"provider": "openai", "api_key": "secret-token",
                           "model": "../../outside"}, agents()["QSU"], {})

    def test_gemini_provider_and_admin_only_backup(self):
        received = []
        def opener(req, timeout):
            received.append(req)
            self.assertTrue(req.full_url.startswith(
                "https://generativelanguage.googleapis.com/v1beta/models/"))
            self.assertEqual(req.get_header("X-goog-api-key"), "gemini-token")
            return Response({"candidates": [{
                "content": {"parts": [{"text": "Báo cáo thiếu dữ liệu kỹ thuật. "
                "Cần kỹ sư kiểm tra bản gốc và thông số thiết bị trước quyết định."}]}
            }]})
        provider, text = call_provider(
            {"provider": "gemini", "api_key": "gemini-token", "model": "gemini-2.5-flash"},
            agents()["ELE"], {"task": "Metadata"}, opener=opener,
        )
        self.assertEqual(provider, "gemini")
        self.assertIn("kỹ sư", text)
        self.assertEqual(len(received), 1)
        with self.assertRaises(PermissionError):
            export_integrity_report(self.ws, self.editor)
        report = export_integrity_report(self.ws, self.admin)
        self.assertEqual(report["schema"], "XD_MEP_AUDIT_EXPORT_V63")
        self.assertTrue(report["validation"]["passed"])
        self.assertEqual(report["eventCount"], 0)
        self.assertEqual(len(report["sha256"]), 64)
        self.assertNotIn("refresh_token", json.dumps(report))

if __name__ == "__main__":
    unittest.main()
