"""V7.1–7.4 private runtime, worker state, human review, cited RAG and DXF tests.

Fake dispatcher; SQLite only for tests; no Redis, LLM or Google OAuth calls.
"""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
import time
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from agent_runtime.api import create_runtime_app
from agent_runtime.security import signature, verify_request, validate_request
from agent_runtime.models import AgentJob, utcnow
from agent_runtime.queue import public, claim, mark
from agent_runtime.graph import next_review
from agent_runtime.standards import query_refs


ROOT = "project-folder-000001"
OTHER = "project-folder-000002"
TASK = "a" * 32
JOB = "b" * 32
EMAIL = "engineer@example.com"
SECRET = "test-secret-longer-than-thirty-two-characters-v74"


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, {
            "AGENT_RUNTIME_ALLOW_SQLITE": "1",
            "AGENT_RUNTIME_SECRET": SECRET,
            "CELERY_BROKER_URL": "redis://never-contact-this-host:6379/1",
            "AGENT_MONTHLY_RESERVE_USD": "10",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.sent = []
        self.app = create_runtime_app(
            "sqlite:///" + str(Path(self.temp.name) / "runtime.sqlite3"),
            dispatcher=lambda job_id: self.sent.append(job_id))
        self.http = TestClient(self.app)
        self.identity = {"email": EMAIL, "role": "update", "projects": [ROOT]}
        self.payload = {
            "jobId": JOB, "projectId": ROOT, "taskId": TASK,
            "agentId": "ELE", "mode": "preflight", "fileId": "",
            "note": "Kiểm tra bản vẽ điện", "consent": False,
            "identity": self.identity,
        }

    def post(self, path, body, *, tamper=False, age=0):
        data = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
        ts = int(time.time()) - age
        sig = signature(SECRET, ts, "POST", path, data)
        if tamper:
            sig = "0" * 64
        return self.http.post(path, content=data, headers={
            "Content-Type": "application/json",
            "X-XD-Timestamp": str(ts),
            "X-XD-Signature": sig,
        })

    def test_real_queue_idempotency_and_scope(self):
        url = "/api/runtime/jobs"
        created = self.post(url, self.payload)
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(created.json()["state"], "queued")
        self.assertFalse(created.json()["hasHeartbeat"])
        self.assertEqual(self.sent, [JOB])
        same = self.post(url, self.payload)
        self.assertEqual(same.status_code, 200)
        self.assertEqual(self.sent, [JOB], "Repeated button must not dispatch twice")
        changed = dict(self.payload, taskId="c" * 32)
        self.assertEqual(self.post(url, changed).status_code, 403)
        other = dict(self.payload, jobId="c" * 32, projectId=OTHER)
        self.assertEqual(self.post(url, other).status_code, 403)
        invalid = dict(self.payload, agentId="UNKNOWN")
        self.assertEqual(self.post(url, invalid).status_code, 422)
        self.assertEqual(self.post(url, self.payload, tamper=True).status_code, 401)
        self.assertEqual(self.post(url, self.payload, age=1000).status_code, 401)

    def test_worker_claim_heartbeat_and_cancel(self):
        self.post("/api/runtime/jobs", self.payload)
        dbmaker = self.app.state.dbmaker
        with dbmaker() as db:
            claimed = claim(db, JOB)
            self.assertIsNotNone(claimed)
            self.assertEqual(claimed.state, "running")
            self.assertIsNone(claim(db, JOB), "No second worker may claim")
            claimed.heartbeat_at = utcnow() - timedelta(seconds=150)
            db.commit()
            self.assertEqual(public(claimed)["state"], "unconfirmed")
        response = self.post("/api/runtime/jobs/cancel", {
            "jobId": JOB, "projectId": ROOT, "identity": self.identity})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["cancelRequested"])
        with dbmaker() as db:
            job = db.get(AgentJob, JOB)
            self.assertEqual(job.state, "running")
            # Running jobs are cooperatively cancelled at safe checkpoints.
            mark(db, JOB, "cancelled", "worker_safepoint")
            db.commit()
            self.assertEqual(public(job)["state"], "cancelled")

    def test_reader_can_query_not_dispatch_or_cancel_others(self):
        self.post("/api/runtime/jobs", self.payload)
        viewer = {"email":"viewer@example.com", "role":"read","projects":[ROOT]}
        view = self.post("/api/runtime/jobs/query", {
            "projectId":ROOT, "identity":viewer})
        self.assertEqual(view.status_code,200,view.text)
        self.assertEqual(len(view.json()["jobs"]),1)
        self.assertFalse(view.json()["jobs"][0]["canCancel"])
        self.assertEqual(self.post("/api/runtime/jobs", {
            **self.payload, "jobId":"c"*32, "identity":viewer}).status_code,403)
        self.assertEqual(self.post("/api/runtime/jobs/cancel", {
            "jobId":JOB,"projectId":ROOT,"identity":viewer}).status_code,403)
        admin = {"email":"admin@example.com","role":"admin","projects":["*"]}
        rows = self.post("/api/runtime/jobs/query",{
            "projectId":ROOT,"identity":admin}).json()["jobs"]
        self.assertTrue(rows[0]["canCancel"])

    def test_api_consent_quota_and_overload(self):
        body=dict(self.payload, mode="llm",jobId="e"*32)
        self.assertEqual(self.post("/api/runtime/jobs",body).status_code,403)
        body["consent"]=True
        with patch.dict(os.environ, {"AGENT_MONTHLY_RESERVE_USD":"0.01"}):
            self.assertEqual(self.post("/api/runtime/jobs",body).status_code,403)
        self.post("/api/runtime/jobs", self.payload)
        with patch.dict(os.environ, {"AGENT_QUEUE_MAX":"1"}):
            response=self.post("/api/runtime/jobs", {
                **self.payload, "jobId":"d"*32,"taskId":"f"*32})
            self.assertEqual(response.status_code,409)

    def test_licensed_source_ingest_and_cited_retrieval(self):
        admin = {"email":"admin@example.com","role":"admin","projects":["*"]}
        data = {
            "projectId":ROOT,"identity":admin,
            "sourceId":"CATALOG-ELE-2026","version":"R02",
            "title":"Catalogue tủ điện tham khảo",
            "citation":"Catalogue ELE, mục 2.1, trang 8",
            "effectiveDate":"2026-10-01",
            "text":"Dòng định mức tủ điện được thể hiện bằng ampere.",
            "copyrightPermitted":False,
        }
        self.assertEqual(self.post("/api/runtime/standards/ingest",data).status_code,403)
        data["copyrightPermitted"]=True
        created=self.post("/api/runtime/standards/ingest",data)
        self.assertEqual(created.status_code,200,created.text)
        q=self.post("/api/runtime/standards/search",{
            "projectId":ROOT,"identity":self.identity,"text":"dòng định mức tủ điện"})
        self.assertEqual(q.status_code,200,q.text)
        matches=q.json()["references"]
        self.assertEqual(len(matches),1)
        self.assertEqual(matches[0]["version"],"R02")
        self.assertEqual(matches[0]["citation"],data["citation"])
        self.assertFalse(matches[0]["complianceVerified"])
        other=self.post("/api/runtime/standards/search",{
            "projectId":OTHER,"identity":self.identity,"text":"dòng định mức"})
        self.assertEqual(other.status_code,403)

    def test_langgraph_human_review_never_autoapprove(self):
        pending=next_review({"task_id":TASK,"qa_decision":"pending"},use_langgraph=True)
        self.assertEqual(pending["next_action"],"human_qa_review")
        self.assertTrue(pending["human_review_required"])
        returned=next_review({"task_id":TASK,"qa_decision":"reject",
                              "reviewer_note":"Sai thông số thiết bị"},use_langgraph=True)
        self.assertEqual(returned["next_action"],"engineer_revision_requires_new_job")
        with self.assertRaises(ValueError):
            next_review({"qa_decision":"reject","reviewer_note":"Sai"})
        good=next_review({"qa_decision":"approve","approver_decision":"approve"})
        self.assertTrue(good["human_review_required"])
        self.assertEqual(good["next_action"],"verify_existing_signed_approval")

    def test_dxf_copy_never_overwrites_original(self):
        import ezdxf
        from agent_runtime.cad_tools import annotate_dxf_copy
        original=Path(self.temp.name)/"original.dxf"
        exported=Path(self.temp.name)/"marked_R02.dxf"
        dwg=ezdxf.new("R2018")
        dwg.modelspace().add_line((0,0),(5,7))
        dwg.saveas(str(original))
        sha=hashlib.sha256(original.read_bytes()).hexdigest()
        with self.assertRaises(PermissionError):
            annotate_dxf_copy(original,exported,[{"x":1,"y":2,"note":"Kiểm tra CB"}])
        result=annotate_dxf_copy(original,exported,
            [{"x":1,"y":2,"note":"Kiểm tra CB"}],human_authorized=True)
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),sha)
        self.assertEqual(result["sourceSha256"],sha)
        self.assertNotEqual(result["outputSha256"],sha)
        self.assertFalse(result["complianceVerified"])
        reopened=ezdxf.readfile(str(exported))
        self.assertEqual(len(reopened.modelspace().query("TEXT")),1)
        with self.assertRaises(ValueError):
            annotate_dxf_copy(original,original,[],human_authorized=True)
        with self.assertRaises(FileExistsError):
            annotate_dxf_copy(original,exported,[],human_authorized=True)

if __name__ == "__main__":
    unittest.main()
