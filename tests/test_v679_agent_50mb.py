"""V6.7.9 regression: a registered file may be read up to 50 MiB, not 8 MiB.

All local fixtures use synthetic project data; real OAuth/AI/API calls are not made.
DXF input over the old limit uses ezdxf's bounded streaming path.
"""
import hashlib
import io
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipInfo

from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT
from drive_storage.expert_tools import (
    MAX_BYTES, MAX_RECORDS, STREAM_DXF_BYTES, PARSERS,
    parse_bytes, extract_registered,
)


class MaxFileLimitTests(unittest.TestCase):
    def test_limit_is_50_mib_and_smaller_csv_still_works(self):
        self.assertEqual(MAX_BYTES, 50 * 1024 * 1024)
        raw = b"Code,Value\nABC,12\n" + b"\n" * (8 * 1024 * 1024)
        self.assertGreater(len(raw), 8 * 1024 * 1024)
        result = parse_bytes("file.csv", raw)
        self.assertEqual(result["type"], "csv")
        self.assertIn("CSV:row2:col1", [item["source"] for item in result["records"]])
        self.assertLessEqual(len(result["records"]), MAX_RECORDS)

    def test_exact_50_mib_boundary_accepted_over_rejected_without_parsing_large_data(self):
        # The parser is stubbed to isolate validation without decoding 50 MiB.
        with patch.dict(PARSERS, {".csv": lambda b: {
            "type": "csv", "records": [], "warnings": [], "stats": {}
        }}):
            sample = b"x" * MAX_BYTES
            self.assertEqual(parse_bytes("limit.csv", sample)["type"], "csv")
            with self.assertRaisesRegex(ValueError, "50 MB"):
                parse_bytes("too_big.csv", sample + b"x")
            with self.assertRaisesRegex(ValueError, "50 MB"):
                parse_bytes("empty.csv", b"")

    def test_larger_xlsx_with_unsafe_zip_expansion_is_rejected(self):
        import drive_storage.expert_tools as expert
        large = ZipInfo("xl/worksheets/sheet1.xml")
        large.file_size = expert.MAX_XLSX_UNCOMPRESSED + 1
        class FakeArchive:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def infolist(self):
                return [large]
        with patch("drive_storage.expert_tools.ZipFile", return_value=FakeArchive()):
            with self.assertRaisesRegex(ValueError, "giải nén quá lớn"):
                expert._spreadsheet(b"PKbad")

    def test_large_ascii_dxf_uses_streaming_not_in_memory_cad_dom(self):
        from unittest.mock import MagicMock
        import drive_storage.expert_tools as expert
        raw = b"0\nEOF\n" + b" " * STREAM_DXF_BYTES
        drawing = MagicMock()
        entity = MagicMock()
        entity.dxftype.return_value = "LINE"
        entity.dxf.get.side_effect = lambda key, default="": {"layer":"MEP_E","handle":"A1"}.get(key,default)
        drawing.modelspace.return_value = iter([entity])
        with patch("ezdxf.addons.iterdxf.opendxf", return_value=drawing) as open_mock, \
             patch("ezdxf.read", side_effect=AssertionError("Full DXF DOM must not be built")):
            parsed = expert._dxf(raw)
        open_mock.assert_called_once()
        drawing.close.assert_called_once()
        self.assertEqual(parsed["stats"]["entities_checked"], 1)
        self.assertEqual(parsed["stats"]["layers"]["MEP_E"], 1)
        self.assertTrue(any("theo luồng" in w for w in parsed["warnings"]))
        self.assertLessEqual(len(parsed["records"]), MAX_RECORDS)

    def test_copy_and_public_prompts_have_50mb_not_8mb(self):
        root = Path(__file__).resolve().parents[1]
        company = (root / "drive_storage/company_ui.py").read_text(encoding="utf8")
        self.assertIn("tối đa 50 MB/file", company)
        self.assertIn("int(d[\"sizeBytes\"]) <= MAX_BYTES", company)
        self.assertNotIn("tối đa 8 MB", company)
        expert = (root / "drive_storage/expert_tools.py").read_text(encoding="utf8")
        self.assertIn("max_bytes=MAX_BYTES", expert)
        requirements = (root / "requirements.txt").read_text(encoding="utf8")
        self.assertIn("pypdf>=6.13.3", requirements)


class Registered50MiBDriveTests(unittest.TestCase):
    def setUp(self):
        CloudWorkflowTests.setUp(self)
        self.fid = "drive-file-large-000001"
        self.blob = b"Code,Qty\nMEP,21\n" + b"\n" * (9 * 1024 * 1024)
        self.download_limits = []
        self.storage.list_category_files = lambda *, project_id, category: [
            {"id": self.fid, "name": "MEP_BOQ_large.csv",
             "size": str(len(self.blob)), "md5Checksum": hashlib.md5(self.blob).hexdigest()}
        ] if project_id == PROJECT and category == "boq_mep" else []
        def download(*, project_id, category, file_id, max_bytes):
            self.download_limits.append(max_bytes)
            if max_bytes < len(self.blob):
                raise ValueError("download limit too small")
            if project_id != PROJECT or category != "boq_mep" or file_id != self.fid:
                raise PermissionError("wrong file")
            return self.blob
        self.storage.download_small_file = download
        task_id = self.ws.create_task(
            self.editor, project_id=PROJECT, title="BOQ Drive 9 MiB",
            dept="qs", assignee="Kỹ sư QS",
        )["id"]
        self.ws.register_document(self.editor, project_id=PROJECT, category="boq_mep",
                                  file_id=self.fid, code="BOQ-LARGE", task_id=task_id)

    def tearDown(self):
        CloudWorkflowTests.tearDown(self)

    def test_actual_download_and_provenance_for_registered_9mb(self):
        evidence = extract_registered(self.ws, self.editor,
                                      project_id=PROJECT, file_id=self.fid)
        self.assertEqual(self.download_limits, [50 * 1024 * 1024])
        self.assertEqual(evidence["type"], "csv")
        self.assertEqual(evidence["provenance"]["fileId"], self.fid)
        self.assertEqual(evidence["provenance"]["sha256"], hashlib.sha256(self.blob).hexdigest())
        self.assertLessEqual(evidence["recordCount"], MAX_RECORDS)

    def test_oversize_prechecked_before_downloading_or_parsing(self):
        self.storage.list_category_files = lambda *, project_id, category: [
            {"id": self.fid, "name": "MEP_BOQ_large.csv",
             "size": str(MAX_BYTES + 1), "md5Checksum": hashlib.md5(self.blob).hexdigest()}
        ]
        with self.assertRaisesRegex(ValueError, "50 MB"):
            extract_registered(self.ws, self.editor,
                               project_id=PROJECT, file_id=self.fid)
        self.assertEqual(self.download_limits, [])

if __name__ == "__main__":
    unittest.main()
