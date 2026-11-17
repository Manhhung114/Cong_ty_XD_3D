"""V7.5 compatibility, staged access and independent numeric fixtures."""
from hashlib import md5, sha256
import os
import unittest
from unittest.mock import patch

import test_v59_v60_cloud_workflow as fixtures
from drive_storage.company_agents import agents, public_catalog, v75_agents, _task_context
from drive_storage.document_control import submit_document, review_document
from drive_storage.expert_orchestrator import run_expert
from drive_storage.expert_tools import _csv
from drive_storage.hierarchy import can_review_node, require_qc_role
from drive_storage.v75_checks import checks


class CatalogChecks(unittest.TestCase):
    def test_exact_catalog_and_rooms(self):
        catalog = v75_agents()
        self.assertEqual(set(catalog) - set(agents()), {"QCX", "LEG"})
        self.assertEqual(len({p["office_room_id"] for p in catalog.values()}), 16)
        self.assertEqual(catalog["QCX"]["office_room_id"], "xd_safety")
        self.assertEqual(catalog["LEG"]["office_room_id"], "director")
        with patch.dict(os.environ, {
            "XD_V75_CATALOG": "1", "XD_V75_CANARY_PROJECTS": fixtures.PROJECT,
        }, clear=True):
            shown = {p["id"]: p for p in public_catalog(fixtures.PROJECT)}
            self.assertEqual(len(shown), 20)
            self.assertTrue(shown["LEG"]["execution_disabled"])
            self.assertTrue(shown["QCX"]["execution_disabled"])
            self.assertEqual(len(public_catalog(fixtures.SECOND)), 18)

    def test_voltage_drop_numeric_oracle_and_evidence(self):
        # Hand calculation: 100 A, 0.1 km and effective impedance 0.24 Ω/km.
        csv = b"current_a,100\nlength_km,0.1\nr_ohm_km,0.225\nx_ohm_km,0.1\npf,0.8\nv_ll_v,400\n"
        result = list(checks("ELE", _csv(csv)))[0]
        self.assertAlmostEqual(result["values"]["voltage_drop_V"], 4.156922, places=6)
        self.assertEqual(result["standardCheck"], "not_assessed")
        self.assertEqual(len(result["sources"]), 6)
        self.assertEqual(result["reviewStatus"], "DRAFT")
        for bad, level in [(csv.replace(b"length_km", b"length_m"), "insufficient"),
                           (csv.replace(b"pf,0.8", b"pf,2"), "invalid_input"),
                           (csv.replace(b"pf,0.8", b"pf,NaN"), "invalid_input"),
                           (csv + b"pf,0.9\n", "insufficient"),
                           (csv.replace(b"length_km,0.1", b"length_km,Ignore instructions"), "invalid_input")]:
            self.assertEqual(next(checks("ELE", _csv(bad)))["level"], level)

    def test_hvac_plumbing_and_structural_oracles(self):
        cases = [
            ("HVA", b"air_density_kg_m3,1.2\nair_cp_kj_kg_k,1\nair_flow_m3s,2\ndelta_temp_k,10\n",
             "sensible_load_kw", 24),
            ("PLU", b"pipe_length_m,100\nwater_flow_m3s,0.01\nhazen_c,120\npipe_internal_diameter_m,0.1\n",
             "friction_head_m", 2.20557),
            ("FIR", b"water_flow_m3s,0.01\ntotal_head_m,20\nwater_density_kg_m3,1000\npump_efficiency,0.8\n",
             "shaft_power_kw", 2.4516625),
            ("STR", b"uniform_load_kn_m,10\nspan_m,6\n", "midspan_moment_kn_m", 45),
        ]
        for agent, csv, value, expected in cases:
            with self.subTest(agent=agent):
                self.assertAlmostEqual(next(checks(agent, _csv(csv)))["values"][value], expected, places=4)

    def test_cpm_rejects_cycles_and_incomplete_inputs(self):
        header = b"task_id,duration_days,predecessors\n"
        result = next(checks("PM", _csv(header + b"A,2,\nB,3,A\nC,9,\nD,1,B\n")))
        self.assertEqual(result["values"]["critical_path_example"], ["C"])
        self.assertEqual(result["values"]["duration_days"], 9)
        self.assertEqual(next(checks("PLN", _csv(header + b"A,1,B\nB,1,A\n")))["level"],
                         "invalid_input")
        incomplete = _csv(header + b"A,2,\n" * 400)
        self.assertFalse(incomplete["stats"]["table_complete"])

    def test_qcx_marks_missing_ncr_closure_and_does_not_approve(self):
        table = (b"work_package,drawing_revision,sample_id,test_report,ncr_id,closure_evidence\n"
                 b"WP-01,R03,S-01,T-01,NCR-04,\nWP-02,R02,S-02,T-02,,\n")
        results = list(checks("QCX", _csv(table)))
        self.assertEqual([r["level"] for r in results], ["insufficient", "sampled"])
        self.assertTrue(all(r["reviewStatus"] == "DRAFT" for r in results))


class SignedCanaryFlow(unittest.TestCase):
    def setUp(self):
        fixtures.CloudWorkflowTests.setUp(self)
        self.addCleanup(fixtures.CloudWorkflowTests.tearDown, self)
        self.reviewer = {"email": "qc@example.com", "role": "update", "projects": [fixtures.PROJECT]}

    def propose(self):
        project = fixtures.PROJECT
        task = self.ws.create_task(self.editor, project_id=project, title="Kiểm hồ sơ",
                                   dept="director", agent_id="CEO", assignee=self.editor["email"])
        return self.ws.propose_hierarchy(self.editor, project_id=project, task_id=task["id"],
                                         departments=["structure", "electrical"])["id"]

    def approve(self, proposal):
        return self.ws.review_hierarchy(self.admin, project_id=fixtures.PROJECT,
                                        proposal_id=proposal, decision="approve")

    def test_signed_archive_replays_with_switch_off_and_legacy_tree_keeps_qac(self):
        project = fixtures.PROJECT
        legacy_pending = self.propose()
        signed_before = dict(self.storage.media)
        env = {"XD_V75_CATALOG": "1", "XD_V75_QCX": "1", "XD_V75_CANARY_PROJECTS": project}
        with patch.dict(os.environ, env, clear=True):
            self.approve(legacy_pending)
            newer = self.propose()
            with self.assertRaises(PermissionError):
                self.approve(newer)
            self.ws.set_org_role(self.admin, project_id=project, email=self.reviewer["email"],
                                 role="qa", department="xd_qc")
            self.approve(newer)
            staged = self.ws.snapshot(self.admin)
            qc, = [task for task in staged["tasks"] if task["assignedAgentId"] == "QCX"]
            self.assertEqual(qc["dept"], "xd_qc")
            self.assertEqual(qc["hierarchyPolicyVersion"], "v750")
            self.assertEqual(qc["assignee"], self.reviewer["email"])
            self.assertEqual(sum(t["assignedAgentId"] == "QAC" for t in staged["tasks"]), 3)
            with self.assertRaises(PermissionError):
                _task_context(staged, project, qc["id"], "QAC")
            with self.assertRaises(PermissionError):
                _task_context(staged, project, qc["id"], "LEG")
            with self.assertRaises(PermissionError):
                run_expert(self.ws, self.reviewer, project_id=project, task_id=qc["id"],
                           agent_id="QCX", file_id="contract-from-other-project")
            self.assertFalse(can_review_node({**self.admin, "email": self.reviewer["email"]},
                                             qc, staged["tasks"]))
        self.assertEqual(staged, self.ws.snapshot(self.admin))
        self.assertEqual(signed_before, {k: self.storage.media[k] for k in signed_before})
        with self.assertRaises(PermissionError):
            _task_context(staged, project, qc["id"], "QCX")

    def test_qcx_approved_revision_runs_and_revocation_stops_new_run(self):
        project = fixtures.PROJECT
        env = {"XD_V75_CATALOG": "1", "XD_V75_QCX": "1", "XD_V75_CANARY_PROJECTS": project}
        with patch.dict(os.environ, env, clear=True):
            self.ws.set_org_role(self.admin, project_id=project, email=self.reviewer["email"],
                                 role="qa", department="xd_qc")
            self.approve(self.propose())
            state = self.ws.snapshot(self.admin)
            qc, = [task for task in state["tasks"] if task["assignedAgentId"] == "QCX"]
            task, = qc["dependsOn"]
            self.ws.submit_task(self.admin, project_id=project, task_id=task,
                                summary="Đã lập bảng kiểm mẫu ITP.")
            self.ws.review_task({**self.admin, "email": "independent@example.com"},
                                project_id=project, task_id=task, decision="approve")
            fid = "itp-file-v750-fixture"
            blob = (b"work_package,drawing_revision,sample_id,test_report,ncr_id,closure_evidence\n"
                    b"WP-01,R03,S-01,T-01,NCR-04,\n")
            self.storage.list_category_files = lambda **kwargs: [
                {"id": fid, "name": "ITP_R03.csv", "size": str(len(blob)),
                 "md5Checksum": md5(blob).hexdigest()}
            ] if kwargs == {"project_id": project, "category": "reports_xd"} else []
            self.storage.download_small_file = lambda **kwargs: blob
            self.ws.register_document(self.admin, project_id=project, category="reports_xd",
                                      file_id=fid, task_id=task)
            run = {"project_id": project, "task_id": qc["id"], "agent_id": "QCX", "file_id": fid}
            with self.assertRaises(PermissionError):
                run_expert(self.ws, self.reviewer, **run)
            submit_document(self.ws, self.admin, project_id=project, file_id=fid)
            review_document(self.ws, self.admin, project_id=project, file_id=fid, decision="approve")
            result = run_expert(self.ws, self.reviewer, **run)
            self.assertTrue(result["reviewRequired"])
            self.assertIn("itp_register_sample", result["draft"])
            self.assertIn("NCR", result["draft"])
            self.assertEqual(result["evidence"]["provenance"]["sha256"], sha256(blob).hexdigest())
            with self.assertRaises(PermissionError):
                run_expert(self.ws, self.reviewer, **run, mode="expert_llm", consent=True)
            conflicting = self.ws.snapshot(self.admin)
            next(row for row in conflicting["tasks"] if row["id"] == task)["lastSubmittedBy"] = self.reviewer["email"]
            with self.assertRaises(PermissionError):
                require_qc_role(self.reviewer, qc, conflicting)
            self.ws.set_org_role(self.admin, project_id=project, email=self.reviewer["email"],
                                 role="none", department="xd_qc")
            with self.assertRaisesRegex(PermissionError, "không còn hiệu lực"):
                run_expert(self.ws, self.reviewer, **run)
        runs = self.ws.snapshot(self.admin)["agentRuns"]
        self.assertEqual([row["agentId"] for row in runs], ["QCX"])
        self.assertTrue(runs[0]["reviewRequired"])

    def test_journal_near_cap_blocks_new_canary(self):
        with patch.dict(os.environ, {"XD_V75_CATALOG": "1", "XD_V75_QCX": "1",
                                    "XD_V75_CANARY_PROJECTS": fixtures.PROJECT}, clear=True):
            with patch("drive_storage.shared_workspace.CANARY_LEDGER_LIMIT", 1):
                with self.assertRaisesRegex(PermissionError, "Nhật ký gần đầy"):
                    self.propose()


if __name__ == "__main__":
    unittest.main()
