"""Offline tests of V5.9 shared Drive event store and V6.0 approvals."""
import io
import re
import sys
import types
import unittest
from unittest.mock import patch

from drive_storage.shared_workspace import SharedWorkspace

ROOT = "root-folder-000000000"
PROJECT = "project-folder-000001"
SECOND = "project-folder-000002"
SIGNING_KEY = "streamlit-cookie-secret-for-v59-tests-0123456789"


class Request:
    def __init__(self, fn):
        self.fn = fn
    def execute(self):
        return self.fn()


class MediaUpload:
    def __init__(self, stream, mimetype, resumable):
        self.data = stream.read()


class FakeService:
    def __init__(self, storage):
        self.storage = storage
    def files(self):
        return self
    def list(self, q="", fields="", pageSize=1000, pageToken=None):
        def query():
            parent = re.search(r"'([^']+)' in parents", q)
            exact = re.search(r"name = '([^']+)'", q)
            parent_id = parent.group(1) if parent else ""
            name = exact.group(1) if exact else None
            items = [dict(x) for x in self.storage.files.values()
                     if parent_id in x["parents"] and (name is None or name == x["name"])]
            return {"files": items}
        return Request(query)
    def create(self, body, media_body=None, fields=""):
        def create():
            fid = "drive-event-" + str(len(self.storage.files) + 100).zfill(12)
            record = {
                "id": fid, "name": body["name"], "parents": body["parents"],
                "mimeType": body.get("mimeType", "application/json"),
                "size": len(media_body.data),
            }
            self.storage.files[fid] = record
            self.storage.media[fid] = media_body.data
            return dict(record)
        return Request(create)
    def get_media(self, fileId):
        return Request(lambda: self.storage.media[fileId])


class FakeStorage:
    def __init__(self):
        self.root_id = ROOT
        self.projects = [
            {"id": PROJECT, "name": "DA001_DEMO_HO_SO"},
            {"id": SECOND, "name": "DA002_DU_AN_THU_HAI"},
        ]
        self.files = {}
        self.media = {}
        self.ledger = ""
        self.service = FakeService(self)
    def _folders_named(self, parent, name):
        if name == "_XD_MEP_WORKSPACE_EVENTS_V59" and self.ledger:
            return [{"id": self.ledger, "name": name}]
        return []
    def folder(self, parent, name):
        self.ledger = "ledger-folder-0000001"
        return self.ledger
    def list_projects(self):
        return list(self.projects)
    def project_by_id(self, pid):
        return next(p for p in self.projects if p["id"] == pid)
    def ensure_project_tree(self, code, name):
        new_id = "project-folder-" + str(len(self.projects) + 4).zfill(6)
        self.projects.append({"id": new_id, "name": code + "_" + name.replace(" ", "_")})
        return new_id
    def list_category_files(self, *, project_id, category):
        return [{"id": "drive-file-123456789", "name": "BOQ_R01.xlsx", "parents": [project_id]}]


class CloudWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.storage = FakeStorage()
        self.mock_import = patch.dict(sys.modules, {
            "googleapiclient": types.ModuleType("googleapiclient"),
            "googleapiclient.http": types.ModuleType("googleapiclient.http"),
        })
        self.mock_import.start()
        sys.modules["googleapiclient.http"].MediaIoBaseUpload = MediaUpload
        self.ws = SharedWorkspace(self.storage, SIGNING_KEY)
        self.admin = {"email": "admin@example.com", "role": "admin", "projects": ["*"]}
        self.editor = {"email": "edit@example.com", "role": "update", "projects": [PROJECT]}
        self.reader = {"email": "read@example.com", "role": "read", "projects": [PROJECT]}

    def tearDown(self):
        self.mock_import.stop()

    def test_create_task_submit_approve_and_persistent_audit(self):
        created = self.ws.create_task(self.editor, project_id=PROJECT, title="Rà soát bản vẽ điện",
                                      dept="electrical", assignee="NV Điện")
        tid = created["id"]
        self.assertEqual(self.ws.snapshot(self.reader)["tasks"][0]["status"], "todo")
        self.ws.start_task(self.editor, project_id=PROJECT, task_id=tid)
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=tid,
                            summary="Đã đối chiếu bản vẽ và khối lượng thiết bị.")
        waiting = self.ws.snapshot(self.reader)
        self.assertEqual(waiting["tasks"][0]["status"], "review")
        with self.assertRaises(PermissionError):
            self.ws.review_task(self.editor, project_id=PROJECT, task_id=tid,
                                decision="approve")
        self.ws.review_task(self.admin, project_id=PROJECT, task_id=tid,
                            decision="approve", comment="Đồng ý")
        result = SharedWorkspace(self.storage, SIGNING_KEY).snapshot(self.reader)
        self.assertEqual(result["tasks"][0]["status"], "done")
        self.assertEqual(result["tasks"][0]["reviewHistory"][-1]["actor"], "admin@example.com")
        self.assertTrue(any(x["action"] == "task.approved" for x in result["events"]))

    def test_project_scope_read_only_and_reject_reason(self):
        with self.assertRaises(PermissionError):
            self.ws.create_task(self.reader, project_id=PROJECT, title="Không có quyền",
                                dept="electrical")
        with self.assertRaises(PermissionError):
            self.ws.create_task(self.editor, project_id=SECOND, title="Sai dự án",
                                dept="electrical")
        self.assertEqual(len(self.ws.snapshot(self.reader)["projects"]), 1)
        task_id = self.ws.create_task(self.editor, project_id=PROJECT,
                                      title="Kiểm tra khối lượng", dept="qs")["id"]
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=task_id,
                            summary="Cần điều chỉnh một số khối lượng trong BOQ.")
        with self.assertRaises(ValueError):
            self.ws.review_task(self.admin, project_id=PROJECT, task_id=task_id,
                                decision="reject", comment="Sai")
        self.ws.review_task(self.admin, project_id=PROJECT, task_id=task_id,
                            decision="reject", comment="Thiếu bảng khối lượng")
        self.assertEqual(self.ws.snapshot(self.editor)["tasks"][0]["status"], "working")

    def test_idempotency_signed_events_and_document_registry(self):
        event_id = "a" * 32
        one = self.ws.create_task(self.editor, project_id=PROJECT,
                                  title="Đếm thiết bị", dept="qs", event_id=event_id)
        two = self.ws.create_task(self.editor, project_id=PROJECT,
                                  title="Đếm thiết bị", dept="qs", event_id=event_id)
        self.assertFalse(one["existing"])
        self.assertTrue(two["existing"])
        self.assertEqual(len(self.ws.snapshot(self.editor)["tasks"]), 1)
        self.ws.register_document(self.editor, project_id=PROJECT,
                                  category="boq_mep", file_id="drive-file-123456789",
                                  code="BOQ-001", task_id=event_id)
        docs = self.ws.snapshot(self.reader)["documents"]
        self.assertEqual(docs[0]["revision"], "R01")
        self.assertEqual(docs[0]["taskId"], event_id)
        fid = next(iter(self.storage.media))
        self.storage.media[fid] = self.storage.media[fid].replace(b"task.created", b"task.deleted")
        with self.assertRaises(PermissionError):
            self.ws.snapshot(self.admin)

    def test_create_project_and_no_duplicate_codes(self):
        pid = self.ws.create_project(self.admin, code="NEW001", name="Du an MEP",
                                     client="Chu dau tu")
        self.assertIn(pid, [p["id"] for p in self.ws.snapshot(self.admin)["projects"]])
        with self.assertRaises(ValueError):
            self.ws.create_project(self.admin, code="NEW001", name="Du an MEP")
        with self.assertRaises(PermissionError):
            self.ws.create_project(self.editor, code="NEW002", name="Du an Xay dung")


if __name__ == "__main__":
    unittest.main()
