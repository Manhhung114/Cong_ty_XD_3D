"""V6.5 reproducible engineering checks, never invented code compliance.

Rules compute mathematical sanity checks from explicit input units and
table cells. They do not determine design suitability, safety or compliance
with any TCVN/QCVN without a verified versioned normative dataset.
"""
from __future__ import annotations

from collections import Counter
from math import isfinite, pi, sqrt
import re

# Each expert has a real, *scoped* capability contract. Unimplemented
# discipline calculations are blocked, not delegated to hallucinating LLMs.
EXPERT_DOMAINS = {
    "CEO": ("project_portfolio", "overdue_and_unassigned"),
    "PM": ("project_schedule", "handoff_dependencies"),
    "ELE": ("three_phase_current", "boq_arithmetic"),
    "HVA": ("air_changes_per_hour", "boq_arithmetic"),
    "PLU": ("pipe_velocity", "boq_arithmetic"),
    "FIR": ("pipe_velocity", "source_completeness"),
    "BIM": ("ifc_product_inventory", "dxf_layer_inventory"),
    "QSU": ("boq_arithmetic", "currency_audit"),
    "QAC": ("evidence_completeness", "revision_trace"),
    "DOC": ("revision_trace", "document_identity"),
    "ARC": ("ifc_product_inventory", "dxf_layer_inventory"),
    "STR": ("ifc_product_inventory", "gravity_load_example"),
    "XBI": ("ifc_product_inventory", "dxf_layer_inventory"),
    "XQS": ("boq_arithmetic", "currency_audit"),
    "PLN": ("project_schedule", "handoff_dependencies"),
    "SIT": ("field_reports", "source_completeness"),
    "HSE": ("field_reports", "source_completeness"),
    "MAT": ("boq_arithmetic", "material_tracking"),
}
V75_EXPERT_DOMAINS = {**EXPERT_DOMAINS, "QCX": ("itp_register_sample",), "LEG": ()}
EXPERT_REQUIREMENTS = {
    "QCX": ["ITP và kết quả thí nghiệm đối chiếu theo revision", "Kỹ sư QC độc lập"],
    "LEG": ["Quyền đọc từng hồ sơ hợp đồng và nguồn được phê chuẩn"],
    "ELE": ["Bản vẽ và danh mục phụ tải điện", "Điện áp 3 pha, PF, hiệu suất có đơn vị nếu tính dòng"],
    "HVA": ["Thông số lưu lượng và thể tích không gian", "Biểu mẫu thiết kế / điều kiện vận hành"],
    "PLU": ["Lưu lượng, đường kính ống", "Hệ số tổn thất / bản vẽ mạng ống nếu kiểm tra thủy lực"],
    "FIR": ["Sơ đồ PCCC và hồ sơ nguồn", "Tiêu chuẩn áp dụng cùng năm phiên bản được kỹ sư kiểm tra"],
    "BIM": ["IFC/DXF gốc và GlobalId / handle", "Báo cáo clash cần worker hình học"],
    "QSU": ["BOQ có số lượng và đơn giá", "Nguồn giá và phạm vi hạng mục"],
    "QAC": ["Biên bản kiểm tra", "Chứng cứ nghiệm thu có người duyệt"],
    "DOC": ["Mã hồ sơ, revision, trạng thái và nhật ký", "Tệp gốc còn trên Drive"],
    "ARC": ["Hồ sơ kiến trúc và bản vẽ DXF/IFC", "Các quy chuẩn áp dụng đã thẩm tra"],
    "STR": ["Tải trọng, sơ đồ kết cấu, vật liệu", "Bộ giải kết cấu có kiểm chứng"],
    "XBI": ["IFC kiến trúc kết cấu", "Báo cáo clash hình học cần worker"],
    "XQS": ["BOQ XD và chứng cứ khối lượng", "Nguồn đơn giá / định mức"],
    "PLN": ["Công việc và tiến độ cập nhật", "Mốc hợp đồng do PM xác nhận"],
    "SIT": ["Nhật ký hiện trường và ảnh có nguồn", "Sự kiện phát sinh có xác nhận"],
    "HSE": ["Biện pháp thi công, checklist HSE", "Quy định hiện hành đã kiểm chứng"],
    "MAT": ["Phiếu đề nghị, nguồn cung và bảng vật tư", "Kiểm tra chứng từ và tiêu chuẩn mẫu"],
    "PM": ["Tiến độ và trách nhiệm từng phòng", "Dự án có thể phân quyền và theo dõi"],
    "CEO": ["Báo cáo điều hành đa dự án", "Ngưỡng cảnh báo được công ty xác nhận"],
}
CATEGORIES = {
    "mechanical": {"HVA", "PLU", "FIR"},
    "quantity_survey": {"QSU", "XQS", "MAT"},
    "engineering": {"ELE", "HVA", "PLU", "FIR", "STR"},
}


def _n(value):
    try:
        if isinstance(value, bool):
            return None
        number = float(str(value).strip().replace(",", ""))
        return number if isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _record(rule, level, detail, sources, values=None):
    return {"rule": rule, "level": level, "message": detail,
            "sources": list(sources)[:8], "values": values or {},
            "standardCheck": "not_assessed"}


def _parameters(parsed):
    """Only numeric values in explicit engineering parameter key/value rows."""
    result = {}
    rows = (parsed.get("stats") or {}).get("table_rows", [])
    allowed = {"p_kw", "v_ll_v", "pf", "efficiency", "flow_m3h",
               "room_volume_m3", "pipe_diameter_mm", "mass_kg"}
    for row in rows:
        cells = row.get("cells", {})
        key = str(cells.get("1", "")).strip().lower().replace(" ", "_")
        if key not in allowed:
            continue
        value = _n(cells.get("2"))
        if value is not None:
            result[key] = (value, f'{row["sheet"]}!row{row["row"]}:col1-col2')
    return result


def _calculations(agent_id, parsed):
    params = _parameters(parsed)
    checks = []
    if agent_id == "ELE":
        need = {"p_kw", "v_ll_v", "pf"}
        if need <= params.keys():
            p, v, pf = (params[k][0] for k in ("p_kw", "v_ll_v", "pf"))
            eff = params.get("efficiency", (1.0, ""))[0]
            if p >= 0 and v > 0 and 0 < pf <= 1 and 0 < eff <= 1:
                amps = p * 1000 / (sqrt(3) * v * pf * eff)
                checks.append(_record("ELE_THREE_PHASE_A", "calculated",
                    "Dòng 3 pha ước tính từ P[kW], V_LL[V], PF, hiệu suất; KHÔNG kiểm tra tiết diện/bảo vệ.",
                    [params[k][1] for k in need] + ([params["efficiency"][1]] if "efficiency" in params else []),
                    {"current_A": round(amps, 4), "power_kW": p, "voltage_V": v, "pf": pf, "eff": eff}))
            else:
                checks.append(_record("ELE_THREE_PHASE_A", "invalid_input",
                                      "P, điện áp, PF hoặc hiệu suất ngoài miền vật lý", [params[k][1] for k in need]))
    if agent_id == "HVA":
        need = {"flow_m3h", "room_volume_m3"}
        if need <= params.keys():
            q, vol = (params[k][0] for k in ("flow_m3h", "room_volume_m3"))
            if q >= 0 and vol > 0:
                checks.append(_record("HVA_ACH", "calculated",
                    "ACH=Q[m³/h]/V[m³]; chỉ tính tỷ lệ trao đổi khí, KHÔNG so với quy chuẩn.",
                    [params[k][1] for k in need], {"ACH_h-1": round(q / vol, 4)}))
            else:
                checks.append(_record("HVA_ACH", "invalid_input",
                                      "Lưu lượng hoặc thể tích không hợp lệ", [params[k][1] for k in need]))
    if agent_id in {"PLU", "FIR"}:
        need = {"flow_m3h", "pipe_diameter_mm"}
        if need <= params.keys():
            q, diameter = (params[k][0] for k in ("flow_m3h", "pipe_diameter_mm"))
            if q >= 0 and diameter > 0:
                velocity = (q / 3600) / (pi * (diameter / 1000)**2 / 4)
                checks.append(_record("PIPE_VELOCITY", "calculated",
                    "v=Q/A cho ống tròn; chưa tính tổn thất áp lực, vật liệu và tiêu chuẩn PCCC.",
                    [params[k][1] for k in need], {"velocity_m_s": round(velocity, 4)}))
            else:
                checks.append(_record("PIPE_VELOCITY", "invalid_input",
                                      "Lưu lượng hoặc đường kính không hợp lệ", [params[k][1] for k in need]))
    if agent_id == "STR" and "mass_kg" in params:
        mass, src = params["mass_kg"]
        if mass >= 0:
            checks.append(_record("GRAVITY_FORCE", "calculated",
                "F=m×9.80665 m/s², minh họa lực trọng trường; không phải thiết kế kết cấu.",
                [src], {"force_N": round(mass * 9.80665, 3)}))
    return checks


def _boq(parsed):
    tables = (parsed.get("stats") or {}).get("table_rows", [])
    headers = {"quantity": {"qty", "quantity", "khối lượng", "so luong", "số lượng"},
               "price": {"unit price", "đơn giá", "don gia", "unit_price"},
               "amount": {"amount", "thành tiền", "thanh tien", "total"}}
    columns = {}
    header_row = -1
    for index, row in enumerate(tables[:12]):
        text = {key: str(value).strip().lower() for key, value in row.get("cells", {}).items()}
        matches = {}
        for col in headers:
            found = next((k for k, v in text.items() if v in headers[col]), None)
            if found:
                matches[col] = found
        if all(k in matches for k in ("quantity", "price", "amount")):
            columns = matches
            header_row = index
            break
    if not columns:
        return []
    diffs, tested, total = [], 0, 0.0
    sheet = tables[header_row]["sheet"]
    for row in tables[header_row + 1:]:
        if row.get("sheet") != sheet:
            break
        cells = row.get("cells", {})
        qty = _n(cells.get(columns["quantity"]))
        price = _n(cells.get(columns["price"]))
        amount = _n(cells.get(columns["amount"]))
        if None in (qty, price, amount):
            continue
        if qty < 0 or price < 0:
            diffs.append(_record("BOQ_NONNEGATIVE", "invalid_input",
                                 "Đơn giá hoặc số lượng âm, cần kỹ sư QS kiểm tra",
                                 [f'{sheet}!row{row["row"]}']))
            continue
        calc = qty * price
        tested += 1
        total += calc
        if abs(calc - amount) > max(1, 0.001 * abs(calc)):
            diffs.append(_record("BOQ_AMOUNT", "mismatch",
                "Thành tiền khác số lượng × đơn giá, chưa tính chiết khấu/thuế/làm tròn đặc thù",
                [f'{sheet}!row{row["row"]}'],
                {"quantity": qty, "unit_price": price, "declared": amount,
                 "recomputed": round(calc, 3)}))
        if len(diffs) >= 15:
            break
    if tested:
        diffs.append(_record("BOQ_SAMPLE", "sampled",
            "Đã so sánh các dòng trong mẫu đọc, không xác nhận toàn bộ dự toán.",
            [f'{sheet}!row{tables[header_row]["row"]}'],
            {"rows_checked": tested, "sample_subtotal": round(total, 3)}))
    return diffs


def analyze(agent_id: str, parsed: dict, registered: dict | None = None, *, v75=False):
    domains = V75_EXPERT_DOMAINS if v75 else EXPERT_DOMAINS
    if agent_id not in domains or agent_id == "LEG":
        raise ValueError("Không tồn tại chuyên gia bộ môn")
    warnings = list(parsed.get("warnings") or [])
    findings = []
    stats = parsed.get("stats") or {}
    if parsed["type"] in {"xlsx", "csv"} and agent_id in {"QSU", "XQS", "MAT", "ELE", "HVA", "PLU", "FIR"}:
        findings.extend(_boq(parsed))
        findings.extend(_calculations(agent_id, parsed))
    if parsed["type"] == "ifc":
        duplicate = stats.get("duplicate_global_ids", [])
        if duplicate:
            findings.append(_record("IFC_GLOBALID_UNIQUE", "mismatch",
                                    "GlobalId bị trùng trong mẫu IFC", [f"IFC:GlobalId:{x}" for x in duplicate]))
        findings.append(_record("IFC_PRODUCTS", "sampled",
                    "Đã đếm phần tử IFC, chưa chạy geometry engine hoặc clash detection.",
                    [r["source"] for r in parsed["records"][:3]],
                    {"count": stats.get("products_total", 0), "types": stats.get("ifc_types", {})}))
    if parsed["type"] == "dxf":
        findings.append(_record("DXF_LAYERS", "sampled",
             "Đã kiểm kê layer/đối tượng DXF, chưa xác minh tỷ lệ đơn vị, giao cắt hay clearance.",
             [r["source"] for r in parsed["records"][:3]],
             {"layers": stats.get("layers", {}), "types": stats.get("types", {})}))
    if v75:
        from drive_storage.v75_checks import checks
        findings[0:0] = list(checks(agent_id, parsed))
    if not findings:
        findings.append(_record("EVIDENCE_INVENTORY", "insufficient",
           "Đã đọc mẫu file nhưng chưa đủ trường dữ liệu chuẩn hóa để thực hiện phép tính chuyên ngành.",
           [r["source"] for r in parsed["records"][:5]]))
    if registered and registered.get("status") != "approved":
        warnings.append("Bản hồ sơ chưa được duyệt; không dùng làm đầu vào phát hành thiết kế")
    if v75 and agent_id == "ELE":
        warnings.insert(0, "Cô lập nguồn, LOTO và xác minh hết điện theo quy trình trước thao tác hiện trường")
    warnings.append("Chưa thực hiện kiểm định phù hợp TCVN/QCVN; phải xác minh bản tiêu chuẩn có hiệu lực")
    return {
        "agent": agent_id, "capabilities": list(domains[agent_id]),
        "requirements": EXPERT_REQUIREMENTS[agent_id],
        "findings": findings[:20], "warnings": warnings[:12],
        "gate": "requires_engineer_verification",
        "standards_status": "not_assessed",
        "coverage": "sampled_not_full_file" if parsed.get("warnings") else "bounded_sample",
    }
