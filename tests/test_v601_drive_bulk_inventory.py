"""Verify one-pass Drive category scan avoids duplicate tree lookups and writes."""
import re
import unittest

from drive_storage.manager import DriveStorage

ROOT="root-folder-123456789"
PROJECT="project-folder-123456789"
BOQ_PARENT="boq-parent-123456789"
BOQ_MEP="boq-mep-leaf-123456789"
FOLDER="application/vnd.google-apps.folder"


class Request:
    def __init__(self, payload):
        self.payload=payload
    def execute(self):
        return self.payload


class FakeGoogleDrive:
    def __init__(self):
        self.calls={}
        self.children={
            PROJECT:[{"id":BOQ_PARENT,"name":"03_BOQ_DU_TOAN","mimeType":FOLDER,"parents":[PROJECT]}],
            BOQ_PARENT:[{"id":BOQ_MEP,"name":"MEP","mimeType":FOLDER,"parents":[BOQ_PARENT]}],
            BOQ_MEP:[
                {"id":"file-abc-123456789","name":"BOQ_R01.xlsx","mimeType":"application/vnd.ms-excel",
                 "parents":[BOQ_MEP],"size":"1000","md5Checksum":"checksum01"},
                {"id":"file-def-123456789","name":"BOQ_R02.xlsx","mimeType":"application/vnd.ms-excel",
                 "parents":[BOQ_MEP],"size":"2000","md5Checksum":"checksum02"},
            ],
        }
    def files(self):
        return self
    def list(self, **kw):
        matched=re.search(r"'([^']+)' in parents", kw["q"])
        self.assert_parent = matched.group(1)
        self.calls[self.assert_parent]=self.calls.get(self.assert_parent,0)+1
        return Request({"files":list(self.children.get(self.assert_parent,[]))})


class BulkDriveTests(unittest.TestCase):
    def test_one_pass_scan_and_no_read_time_folder_creation(self):
        svc=FakeGoogleDrive()
        store=DriveStorage(svc,ROOT)
        store.project_by_id=lambda pid: {"id": PROJECT,"name":"S234"} if pid==PROJECT else None
        result=store.list_project_files(project_id=PROJECT)
        self.assertEqual(len(result),2)
        self.assertEqual({x["category"] for x in result},{"boq_mep"})
        self.assertEqual({x["md5Checksum"] for x in result},{"checksum01","checksum02"})
        self.assertEqual(svc.calls[PROJECT],1)
        self.assertEqual(svc.calls[BOQ_PARENT],1)
        self.assertEqual(svc.calls[BOQ_MEP],1)
        self.assertEqual(sum(svc.calls.values()),3)

    def test_ambiguous_category_folder_fails_closed(self):
        svc=FakeGoogleDrive()
        svc.children[PROJECT].append({"id":"another-folder-123456","name":"03_BOQ_DU_TOAN",
                                       "mimeType":FOLDER,"parents":[PROJECT]})
        store=DriveStorage(svc,ROOT)
        store.project_by_id=lambda pid:{"id":PROJECT}
        with self.assertRaises(RuntimeError):
            store.list_project_files(project_id=PROJECT)

if __name__=="__main__":
    unittest.main()
