"""V6.0.1 real Drive inventory, version tracking and signed document workflow."""
import unittest
from unittest.mock import patch

from drive_storage.document_control import (
    inventory, base_code, revision, allowed_drive_link,
    update_metadata, submit_document, review_document, archive_document,
)
from drive_storage.document_control_ui import _csv_cell, inventory_csv
from test_v59_v60_cloud_workflow import (
    FakeStorage, CloudWorkflowTests, PROJECT, SECOND, SIGNING_KEY,
)
from drive_storage.shared_workspace import SharedWorkspace


class DocumentControlTests(CloudWorkflowTests):
    """Reuse FakeStorage and authenticated identities without external Google calls."""

    def setUp(self):
        super().setUp()
        self.rows = [{
            "id": "drive-file-123456789", "name": "BOQ_ABC_R01.xlsx",
            "size": "1024", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "createdTime": "2026-11-16T00:00:00Z",
            "modifiedTime": "2026-11-16T00:00:00Z",
            "md5Checksum": "test-checksum",
            "webViewLink": "https://drive.google.com/file/d/drive-file-123456789/view",
            "appProperties": {"revision": "1"},
        }, {
            "id": "drive-file-223456789", "name": "BOQ_ABC_R02.xlsx",
            "size": "2048", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "createdTime": "2026-11-17T00:00:00Z",
            "modifiedTime": "2026-11-17T00:00:00Z",
            "md5Checksum": "second-checksum",
            "appProperties": {"revision": "2"},
        }]
        self.storage.list_category_files = lambda *, project_id, category: (
            [dict(x) for x in self.rows] if project_id == PROJECT and category == "boq_mep" else []
        )

    def test_drive_inventory_includes_unregistered_and_revision_groups(self):
        r = inventory(self.ws, self.reader, PROJECT)
        self.assertEqual(r["counts"]["total"], 2)
        self.assertEqual(r["counts"]["unregistered"], 2)
        self.assertEqual([x["revision"] for x in r["items"]], ["R02", "R01"])
        self.assertEqual(sum(x["latest"] for x in r["items"]), 1)
        self.assertEqual({x["group"] for x in r["items"]}, {"boq_mep/BOQ_ABC"})
        with self.assertRaises(PermissionError):
            inventory(self.ws, self.editor, SECOND)

    def test_register_update_submit_approve_and_archive(self):
        fid = self.rows[0]["id"]
        reg = self.ws.register_document(self.editor, project_id=PROJECT, category="boq_mep",
                                        file_id=fid, code="BOQ-EL-001", description="Lần 1")
        self.assertFalse(reg["existing"])
        with self.assertRaises(ValueError):
            self.ws.register_document(self.editor, project_id=PROJECT, category="boq_mep",
                                      file_id=fid, code="BOQ-EL-001")
        self.assertEqual(inventory(self.ws, self.reader, PROJECT)["counts"]["registered"], 1)
        with self.assertRaises(PermissionError):
            update_metadata(self.ws, self.reader, project_id=PROJECT, file_id=fid,
                            code="BOQ-TEST")
        update_metadata(self.ws, self.editor, project_id=PROJECT, file_id=fid,
                        code="BOQ-EL-001", description="Kỹ sư kiểm tra")
        submit_document(self.ws, self.editor, project_id=PROJECT, file_id=fid,
                        comment="Trình kiểm tra BOQ")
        with self.assertRaises(PermissionError):
            review_document(self.ws, self.editor, project_id=PROJECT, file_id=fid,
                            decision="approve")
        with self.assertRaises(ValueError):
            review_document(self.ws, self.admin, project_id=PROJECT, file_id=fid,
                            decision="return", comment="Sai")
        review_document(self.ws, self.admin, project_id=PROJECT, file_id=fid,
                        decision="approve", comment="Đạt yêu cầu nội bộ")
        state = self.ws.snapshot(self.reader)["documents"][0]
        self.assertEqual(state["status"], "approved")
        self.assertEqual(state["md5Checksum"], "test-checksum")
        self.assertEqual(len(state["history"]), 4)
        self.assertEqual(state["history"][-1]["actor"], self.admin["email"])
        with self.assertRaises(ValueError):
            update_metadata(self.ws, self.editor, project_id=PROJECT, file_id=fid,
                            code="MODIFY-APPROVED")
        archive_document(self.ws, self.admin, project_id=PROJECT, file_id=fid,
                         comment="Phiên bản đã được thay thế")
        self.assertEqual(self.ws.snapshot(self.reader)["documents"][0]["status"], "archived")

    def test_request_return_then_resubmit(self):
        fid = self.rows[0]["id"]
        self.ws.register_document(self.admin, project_id=PROJECT, category="boq_mep",
                                  file_id=fid, code="BOQ-01")
        submit_document(self.ws, self.editor, project_id=PROJECT, file_id=fid)
        review_document(self.ws, self.admin, project_id=PROJECT, file_id=fid,
                        decision="return", comment="Thiếu xác nhận khối lượng")
        self.assertEqual(self.ws.snapshot(self.reader)["documents"][0]["status"], "returned")
        submit_document(self.ws, self.editor, project_id=PROJECT, file_id=fid)
        self.assertEqual(self.ws.snapshot(self.reader)["documents"][0]["status"], "pending")

    def test_external_drive_deletion_and_integrity_difference_are_visible(self):
        fid = self.rows[0]["id"]
        self.ws.register_document(self.editor, project_id=PROJECT, category="boq_mep",
                                  file_id=fid, code="BOQ-01")
        self.rows[0]["md5Checksum"] = "changed-checksum"
        items = inventory(self.ws, self.reader, PROJECT)["items"]
        changed = next(x for x in items if x["id"] == fid)
        self.assertTrue(changed["integrityWarning"])
        with self.assertRaises(PermissionError):
            submit_document(self.ws, self.editor, project_id=PROJECT, file_id=fid)
        self.rows = self.rows[1:]
        items = inventory(self.ws, self.reader, PROJECT)["items"]
        lost = next(x for x in items if x["id"] == fid)
        self.assertTrue(lost["missing"])
        self.assertEqual(lost["status"], "missing")
        with self.assertRaises(PermissionError):
            submit_document(self.ws, self.editor, project_id=PROJECT, file_id=fid)

    def test_escaping_revision_and_csv_formula_injection(self):
        self.assertEqual(base_code("BOQ_R01.xlsx"), "BOQ")
        self.assertEqual(revision("BANG_R04.dwg"), "R04")
        self.assertEqual(allowed_drive_link("javascript:alert(1)"), "")
        self.assertEqual(allowed_drive_link("https://evil.example.com/f"), "")
        self.assertEqual(_csv_cell("=HYPERLINK('http://bad')")[:2], "'=")
        r = inventory(self.ws, self.reader, PROJECT)
        self.assertTrue(inventory_csv(r["items"]).startswith("\ufeff".encode("utf8")))


if __name__ == "__main__":
    unittest.main()
