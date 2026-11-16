"""V6.4-V6.6 tested engineering parsers, formula findings and review chains."""
import importlib.util
import io
import hashlib
import json
import unittest

from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT, SECOND
from drive_storage.expert_tools import (
    MAX_BYTES, SUPPORTED, NOT_SUPPORTED, parse_bytes, extract_registered,
)
from drive_storage.expert_rules import (
    analyze, EXPERT_DOMAINS, _boq, _calculations,
)
from drive_storage.expert_orchestrator import run_expert
from drive_storage.company_agents import agents


class ExtractorTests(unittest.TestCase):
    def test_csv_boq_with_anchor_and_detection(self):
        source = b"Quantity,Unit Price,Amount\n2,100,250\n3,50,150\n"
        result = parse_bytes("MEP_R01.csv", source)
        self.assertEqual(result["type"], "csv")
        analysis = analyze("QSU", result, {"status": "draft"})
        self.assertTrue(any(f["rule"] == "BOQ_AMOUNT" and f["level"] == "mismatch"
                            for f in analysis["findings"]))
        sources = [r["source"] for r in result["records"]]
        self.assertIn("CSV:row2:col1", sources)
        self.assertEqual(analysis["standards_status"], "not_assessed")

    def test_explicit_engineering_formula_inputs(self):
        rows = [
            ["p_kw", "15"], ["v_ll_v", "400"], ["pf", "0.9"], ["efficiency", "0.95"],
            ["flow_m3h", "360"], ["room_volume_m3", "120"],
            ["pipe_diameter_mm", "50"], ["mass_kg", "10"],
        ]
        src = ("key,value\n" + "".join(",".join(row) + "\n" for row in rows)).encode()
        parsed = parse_bytes("input.csv", src)
        ele = _calculations("ELE", parsed)
        self.assertEqual(ele[0]["rule"], "ELE_THREE_PHASE_A")
        self.assertGreater(ele[0]["values"]["current_A"], 20)
        hva = _calculations("HVA", parsed)
        self.assertAlmostEqual(hva[0]["values"]["ACH_h-1"], 3)
        plu = _calculations("PLU", parsed)
        self.assertTrue(40 < plu[0]["values"]["velocity_m_s"] < 60)
        structure = _calculations("STR", parsed)
        self.assertEqual(structure[0]["values"]["force_N"], 98.067)

    def test_unsupported_and_size_rejected(self):
        for name in ("model.dwg", "model.rvt", "model.nwd", "old.xls"):
            with self.assertRaises(ValueError):
                parse_bytes(name, b"something")
        with self.assertRaises(ValueError):
            parse_bytes("too_big.csv", b"a" * (MAX_BYTES+1))
        with self.assertRaises(ValueError):
            parse_bytes("bad.exe", b"unknown")

    @unittest.skipUnless(importlib.util.find_spec("openpyxl"), "install openpyxl")
    def test_actual_excel_cells_and_boq(self):
        from openpyxl import Workbook
        wb=Workbook()
        ws=wb.active
        ws.title="BOQ"
        ws.append(["Khối lượng", "Đơn giá", "Thành tiền"])
        ws.append([2, 100, 250])
        buf=io.BytesIO()
        wb.save(buf)
        parsed=parse_bytes("boq.xlsx", buf.getvalue())
        self.assertEqual(parsed["type"], "xlsx")
        self.assertIn("XLSX:BOQ!A2", [x["source"] for x in parsed["records"]])
        findings=analyze("XQS", parsed)
        self.assertTrue(any(x["rule"]=="BOQ_AMOUNT" for x in findings["findings"]))

    @unittest.skipUnless(importlib.util.find_spec("pypdf"), "install pypdf")
    def test_actual_pdf_empty_page_warns_without_fabricating_text(self):
        from pypdf import PdfWriter
        writer=PdfWriter()
        writer.add_blank_page(width=200,height=200)
        buf=io.BytesIO()
        writer.write(buf)
        parsed=parse_bytes("empty.pdf",buf.getvalue())
        self.assertEqual(parsed["type"],"pdf")
        self.assertEqual(parsed["stats"]["pages"],1)
        self.assertFalse(parsed["records"])
        self.assertTrue(any("OCR" in x for x in parsed["warnings"]))

    @unittest.skipUnless(importlib.util.find_spec("ezdxf"), "install ezdxf")
    def test_actual_dxf_layer_and_handle(self):
        import ezdxf
        model=ezdxf.new(setup=True)
        model.modelspace().add_line((0,0),(1,1),dxfattribs={"layer":"MEP_E"})
        stream=io.StringIO()
        model.write(stream)
        parsed=parse_bytes("plan.dxf", stream.getvalue().encode())
        self.assertEqual(parsed["type"],"dxf")
        self.assertIn("MEP_E",parsed["stats"]["layers"])
        self.assertTrue(any(x["source"].startswith("DXF:handle:") for x in parsed["records"]))

    @unittest.skipUnless(importlib.util.find_spec("ifcopenshell"), "install IFC parser")
    def test_actual_ifc_product_and_globalid(self):
        import ifcopenshell
        model=ifcopenshell.file(schema="IFC4")
        gid=ifcopenshell.guid.new()
        model.create_entity("IfcWall",GlobalId=gid,Name="Demo wall")
        parsed=parse_bytes("model.ifc",model.to_string().encode())
        self.assertEqual(parsed["type"],"ifc")
        self.assertGreaterEqual(parsed["stats"]["products_total"],1)
        self.assertTrue(any(gid in x["source"] for x in parsed["records"]))
        self.assertTrue(any("clash" in w for w in parsed["warnings"]))


class ExpertWorkflowTests(CloudWorkflowTests):
    def setUp(self):
        super().setUp()
        self.blob=b"Quantity,Unit Price,Amount\n2,100,250\n3,50,150\n"
        self.fid="drive-file-123456789"
        self.storage.list_category_files=lambda *,project_id,category: (
            [{"id":self.fid,"name":"MEP_BOQ_R01.csv",
              "size":str(len(self.blob)),"md5Checksum":hashlib.md5(self.blob).hexdigest()}]
            if project_id==PROJECT and category=="boq_mep" else []
        )
        self.storage.download_small_file=lambda *,project_id,category,file_id,max_bytes: (
            self.blob if project_id==PROJECT and category=="boq_mep"
            and file_id==self.fid else b""
        )
        self.task_id=self.ws.create_task(
            self.editor, project_id=PROJECT,title="Thẩm tra BOQ MEP",
            dept="qs",assignee="Kỹ sư QS",doc_code="BOQ-TEST",
        )["id"]
        self.ws.register_document(
            self.editor,project_id=PROJECT,category="boq_mep",
            file_id=self.fid,code="BOQ-TEST",task_id=self.task_id,
        )

    def test_real_registered_drive_evidence_and_four_role_pipeline(self):
        result=run_expert(
            self.ws,self.editor,project_id=PROJECT,task_id=self.task_id,
            agent_id="QSU",file_id=self.fid,event_id="c"*32,
        )
        self.assertFalse(result["existing"])
        self.assertIn("BOQ_AMOUNT",result["draft"])
        self.assertEqual([x["expert"] for x in result["stages"]],
                         ["QSU","DOC","QAC","PM"])
        self.assertEqual(result["evidence"]["format"],"csv")
        self.assertEqual(result["evidence"]["provenance"]["fileId"],self.fid)
        self.assertEqual(len(result["evidence"]["provenance"]["sha256"]),64)
        record=self.ws.snapshot(self.reader)["agentRuns"][0]
        self.assertEqual(record["mode"],"expert")
        self.assertTrue(record["reviewRequired"])
        self.assertEqual(len(record["workflowStages"]),4)
        self.assertEqual(record["standardCheck"],"not_assessed")
        self.assertEqual(self.ws.snapshot(self.reader)["tasks"][0]["status"],"todo")
        second=run_expert(self.ws,self.editor,project_id=PROJECT,
                          task_id=self.task_id,agent_id="QSU",file_id=self.fid,
                          event_id="c"*32)
        self.assertTrue(second["existing"])
        self.assertEqual(len(self.ws.snapshot(self.reader)["agentRuns"]),1)

    def test_missing_signature_wrong_role_or_changed_file_rejected(self):
        with self.assertRaises(PermissionError):
            run_expert(self.ws,self.reader,project_id=PROJECT,task_id=self.task_id,
                       agent_id="QSU",file_id=self.fid)
        with self.assertRaises(PermissionError):
            run_expert(self.ws,self.editor,project_id=SECOND,task_id=self.task_id,
                       agent_id="QSU",file_id=self.fid)
        with self.assertRaises(PermissionError):
            run_expert(self.ws,self.editor,project_id=PROJECT,task_id=self.task_id,
                       agent_id="ELE",file_id=self.fid)
        self.blob=b"changed file bytes"
        with self.assertRaises(PermissionError):
            extract_registered(self.ws,self.editor,project_id=PROJECT,file_id=self.fid)

    def test_expert_llm_requires_explicit_consent(self):
        with self.assertRaises(PermissionError):
            run_expert(self.ws,self.editor,project_id=PROJECT,task_id=self.task_id,
                       agent_id="QSU",file_id=self.fid,mode="expert_llm",
                       ai_config={"provider":"openai","model":"gpt-4.1-mini","api_key":"foo"},
                       consent=False)

    def test_every_expert_has_domain_rules(self):
        self.assertEqual(set(EXPERT_DOMAINS),set(agents()))
        for key,skills in EXPERT_DOMAINS.items():
            self.assertGreaterEqual(len(skills),2)
            self.assertTrue(agents()[key]["quality_gate"])


if __name__=="__main__":
    unittest.main()
