"""Release checks at the Streamlit entry point and the registered-file boundary."""
from datetime import date
from hashlib import md5, sha256
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_v59_v60_cloud_workflow as fixtures
from drive_storage.company_agents import public_catalog
from drive_storage.document_control import submit_document, review_document
from drive_storage.expert_orchestrator import run_expert
from drive_storage.expert_tools import parse_bytes
from drive_storage.v75_checks import _finding
from drive_storage.v75_registers import HEADERS, check_register
from drive_storage.v75_rollout import BUILD_LABEL, qcx_enabled

ROOT = Path(__file__).resolve().parents[1]


class StreamlitReleaseTests(unittest.TestCase):
    def test_default_catalog_for_selected_project_and_rollback_switch(self):
        with patch.dict(os.environ, {}, clear=True):
            profiles = {p["id"]: p for p in public_catalog(fixtures.PROJECT)}
            self.assertEqual(len(profiles), 20)
            self.assertIn("ifc_revision_delta", profiles["BIM"]["expert_tools"])
            self.assertIn("jsa_ptw_register", profiles["HSE"]["expert_tools"])
            self.assertTrue(profiles["LEG"]["execution_disabled"])
            self.assertTrue(profiles["QCX"]["execution_disabled"])
        with patch.dict(os.environ, {"XD_V75_QCX": "1"}, clear=True):
            self.assertFalse(qcx_enabled(fixtures.PROJECT))
        with patch.dict(os.environ, {"XD_V75_CATALOG": "0"}, clear=True):
            self.assertEqual(len(public_catalog(fixtures.PROJECT)), 18)

    def test_streamlit_entrypoint_login_smoke(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(ROOT / "streamlit_app.py"))
        app.secrets["auth"] = {"cookie_secret": "fake-for-local-app-smoke"}
        app.secrets["drive"] = {"allowed_email": "fixture@example.com"}
        with (patch("drive_storage.workspace_ui.load_snapshot") as load_snapshot,
              patch("drive_storage.in_app.mount_bridge") as mount_bridge):
            app.run(timeout=15)
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Công ty Xây dựng & MEP AI 3D")
        self.assertEqual(app.caption[0].value, BUILD_LABEL)
        self.assertEqual(app.button[0].label, "Đăng nhập với Google")
        self.assertEqual(json.loads((ROOT / "VERSION_MANIFEST.json").read_text())
                         ["staged_release"]["version"], BUILD_LABEL[1:])
        load_snapshot.assert_not_called()
        mount_bridge.assert_not_called()


class SpecialistRegisterTests(unittest.TestCase):
    def test_specialist_register_checks(self):
        cases = {
            "boq_acceptance_register": [
                ("EL01,m,m,10.500,11.250,BB01", "mismatch"),
                ("EL02,m,cm,10,1,BB02", "invalid_input"),
                ("EL03,m,m,10,9,BB03", "calculated"),
            ],
            "jsa_ptw_register": [
                ("EL,JS01,PT01,HSE,2026-11-16,2026-11-17,issued", "sampled"),
                ("CT,JS02,PT02,HSE,2026-11-01,2026-11-16,issued", "mismatch"),
                ("XD,JS03,PT03,HSE,2026-02-30,2026-03-01,issued", "invalid_input"),
            ],
            "material_certificate_register": [
                ("EL,LOT1,SUB1,CO1,CQ1,2026-11-16,2026-11-17", "mismatch"),
                ("EL,LOT2,SUB1,CO2,,2026-11-16,2026-11-17", "insufficient"),
                ("EL,LOT1,SUB1,CO1,CQ1,2026-11-16,2026-11-16", "invalid_input"),
            ],
            "bim_issue_register": [
                ("f270c2a8-e1ab-48c0-9da7-dafae2fd8a2a,3YdUF4ky90nuVnA2z5k37A,R02,MEP,2026-11-16,open", "mismatch"),
                ("f370c2a8-e1ab-48c0-9da7-dafae2fd8a2a,invalid,R02,MEP,2026-11-16,closed", "invalid_input"),
            ],
        }
        for tool, rows in cases.items():
            with self.subTest(tool=tool):
                csv = ",".join(HEADERS[tool]) + "\n" + "\n".join(row for row, _ in rows)
                parsed = parse_bytes("register.csv", csv.encode())
                results = list(check_register(tool, parsed["stats"]["table_rows"], _finding, date(2026, 11, 17)))
                self.assertEqual([r["level"] for r in results], [level for _, level in rows])
                self.assertTrue(all(r["standardCheck"] == "not_assessed" for r in results))
                self.assertTrue(all(r["sources"][0].startswith("CSV!row") for r in results))
        qty_rows = parse_bytes("boq.csv", (
            b"item_code,boq_unit,accepted_unit,boq_quantity,accepted_quantity,acceptance_ref\n"
            b"A,m,m,10.500,11.250,BB01\n"
        ))["stats"]["table_rows"]
        result = next(check_register("boq_acceptance_register", qty_rows, _finding, date(2026, 11, 17)))
        self.assertEqual(result["values"]["delta"], "0.750")


class IFCRevisionReleaseTests(unittest.TestCase):
    def setUp(self):
        fixtures.CloudWorkflowTests.setUp(self)
        self.addCleanup(fixtures.CloudWorkflowTests.tearDown, self)
        self.env = patch.dict(os.environ, {"XD_V75_CATALOG": "release"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_ifc_file_pair_reads_only_approved_registered_revisions_and_saves_two_hashes(self):
        import ifcopenshell

        pid = fixtures.PROJECT
        task = self.ws.create_task(self.editor, project_id=pid, title="Rà thay đổi IFC",
                                   dept="bim", agent_id="BIM")["id"]
        a, b, c = (ifcopenshell.guid.new() for _ in range(3))

        def model(elements):
            file = ifcopenshell.file(schema="IFC4")
            for gid, name in elements:
                file.create_entity("IfcWall", GlobalId=gid, Name=name)
            return file.to_string().encode()

        files = {
            "ifc-release-v750-r01": ("MODEL_R01.ifc", model([(a, "Wall-A"), (b, "Wall-B")])),
            "ifc-release-v750-r02": ("MODEL_R02.ifc", model([(a, "Wall-A-Changed"), (c, "Wall-C")])),
        }
        self.storage.list_category_files = lambda **kw: [
            {"id": fid, "name": name, "size": str(len(blob)), "md5Checksum": md5(blob).hexdigest()}
            for fid, (name, blob) in files.items()
        ] if kw == {"project_id": pid, "category": "bim_mep"} else []
        read_ids = []

        def download(**kw):
            self.assertEqual(kw["project_id"], pid)
            read_ids.append(kw["file_id"])
            return files[kw["file_id"]][1]

        self.storage.download_small_file = download
        for fid in files:
            self.ws.register_document(self.editor, project_id=pid, category="bim_mep",
                                      file_id=fid, task_id=task)
        older, current = files.keys()
        run = {"project_id": pid, "task_id": task, "agent_id": "BIM",
               "file_id": current, "baseline_file_id": older, "event_id": "f" * 32}
        with self.assertRaises(PermissionError):
            run_expert(self.ws, self.editor, **run)
        self.assertEqual(read_ids, [])
        for fid in files:
            submit_document(self.ws, self.editor, project_id=pid, file_id=fid)
            review_document(self.ws, self.admin, project_id=pid, file_id=fid, decision="approve")
        for overrides in [{"file_id": older, "baseline_file_id": current},
                          {"baseline_file_id": "outside-project-ifc"},
                          {"mode": "expert_llm", "consent": True}]:
            with self.assertRaises((PermissionError, ValueError)):
                run_expert(self.ws, self.editor, **{**run, **overrides})
        self.assertEqual(read_ids, [])
        result = run_expert(self.ws, self.editor, **run)
        self.assertTrue(result["reviewRequired"])
        self.assertIn('"added":1,"removed":1,"changed":1', result["draft"])
        signed = self.ws.snapshot(self.reader)["agentRuns"][0]
        self.assertEqual({ref["fileId"]: ref["sha256"] for ref in signed["evidence"]},
                         {fid: sha256(blob).hexdigest() for fid, (_, blob) in files.items()})
        self.assertEqual(read_ids, [current, older])
        self.assertTrue(run_expert(self.ws, self.editor, **run)["existing"])
        self.assertEqual(read_ids, [current, older])
        with self.assertRaises(PermissionError):
            run_expert(self.ws, self.editor, **{**run, "baseline_file_id": ""})


if __name__ == "__main__":
    unittest.main()
