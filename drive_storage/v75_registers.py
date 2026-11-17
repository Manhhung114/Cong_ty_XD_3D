"""Review structured project registers and IFC inventory revisions."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re


HEADERS = {
    "boq_acceptance_register": (
        "item_code", "boq_unit", "accepted_unit", "boq_quantity", "accepted_quantity", "acceptance_ref",
    ),
    "jsa_ptw_register": (
        "work_package", "jsa_ref", "ptw_ref", "issuer", "valid_from", "valid_until", "status",
    ),
    "material_certificate_register": (
        "material_code", "batch_id", "submittal_ref", "co_ref", "cq_ref", "required_on", "delivery_on",
    ),
    "bim_issue_register": (
        "bcf_topic_guid", "ifc_global_id", "model_revision", "assignee", "due_date", "status",
    ),
}
REGISTER_TOOLS = {
    "BIM": "bim_issue_register", "XBI": "bim_issue_register",
    "QSU": "boq_acceptance_register", "XQS": "boq_acceptance_register",
    "HSE": "jsa_ptw_register", "MAT": "material_certificate_register",
}
IFC_AGENTS = {"BIM", "XBI"}
_IFC_ID = re.compile(r"[0-3][0-9A-Za-z_$]{21}")
_GUID = re.compile(r"[A-Fa-f0-9]{8}(?:-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12}")


def _rows(rows, headers):
    matches = []
    for index, row in enumerate(rows):
        keys = [str(value).strip().casefold() for value in row["cells"].values()]
        if set(headers).issubset(keys):
            if any(keys.count(key) != 1 for key in headers):
                return []
            matches.append((index, dict(zip(keys, row["cells"]))))
    if len(matches) != 1:
        return []
    index, columns = matches[0]
    sheet = rows[index]["sheet"]
    result = []
    for row in rows[index + 1:]:
        if row["sheet"] != sheet:
            break
        values = [str(row["cells"].get(columns[key], "")).strip() for key in headers]
        if any(values):
            source = f"{sheet}!row{row['row']}:cols" + ",".join(columns[key] for key in headers)
            result.append((values, source))
    return result


def _iso_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError
    return date.fromisoformat(value)


def _quantity(value):
    if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,6})?", value):
        raise ValueError
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError from exc


def _boq(row, _today):
    item, unit, accepted_unit, planned, accepted, source = row
    if not all(row):
        return "insufficient", "Thiếu mã, đơn vị, khối lượng hoặc tham chiếu biên bản nghiệm thu.", {}
    if unit != accepted_unit:
        return "invalid_input", "Đơn vị BOQ và nghiệm thu khác nhau. Cần xác minh quy đổi.", {}
    planned_qty, accepted_qty = _quantity(planned), _quantity(accepted)
    difference = accepted_qty - planned_qty
    values = {"unit": unit, "boq": str(planned_qty), "accepted": str(accepted_qty), "delta": str(difference)}
    if difference > 0:
        return "mismatch", "Khối lượng theo biên bản vượt BOQ. Cần QS kiểm tra phát sinh và phê duyệt.", values
    return "calculated", "Đã đối chiếu khối lượng từng dòng có đơn vị và mã biên bản.", values


def _safety(row, today):
    work, jsa, ptw, issuer, start, end, status = row
    if not all(row):
        return "insufficient", "Thiếu JSA, PTW, người cấp, thời hạn hoặc trạng thái.", {}
    first, last = _iso_date(start), _iso_date(end)
    if last < first:
        raise ValueError
    state = status.casefold()
    if state not in {"draft", "issued", "suspended", "closed", "revoked"}:
        raise ValueError
    if state != "issued" or not first <= today <= last:
        return "mismatch", "Trạng thái hoặc thời hạn PTW cần HSE xem xét trước khi làm việc.", {}
    return "sampled", "Sổ có tham chiếu JSA/PTW và thời hạn phù hợp ngày kiểm tra. HSE phải xác nhận giấy phép gốc.", {}


def _materials(row, _today):
    material, batch, submittal, co, cq, required, delivery = row
    if not all(row):
        return "insufficient", "Thiếu mã vật tư/lô, submittal, CO/CQ hoặc ngày đối chiếu giao hàng.", {}
    delta = (_iso_date(delivery) - _iso_date(required)).days
    if delta > 0:
        return "mismatch", "Ngày giao ghi trong sổ vượt ngày cần vật tư. Cần đối chiếu hồ sơ giao nhận.", {"late_days": delta}
    return "calculated", "Đã đối chiếu ngày giao và mã chứng từ của lô. Cần kiểm chứng CO/CQ gốc.", {"late_days": 0}


def _bim_issue(row, today):
    topic, element, revision, owner, due, status = row
    if not all(row):
        return "insufficient", "Thiếu mã BCF, GlobalId, revision, người xử lý, hạn hoặc trạng thái.", {}
    if not _GUID.fullmatch(topic) or not _IFC_ID.fullmatch(element) or not re.fullmatch(r"R\d{2,4}", revision):
        raise ValueError
    state = status.casefold()
    if state not in {"open", "in_progress", "resolved", "closed"}:
        raise ValueError
    if _iso_date(due) < today and state in {"open", "in_progress"}:
        return "mismatch", "Issue BCF quá hạn theo bảng theo dõi.", {}
    return "sampled", "Issue có đủ trường theo dõi trong bảng BCF xuất ra.", {}


_RULES = {
    "boq_acceptance_register": _boq,
    "jsa_ptw_register": _safety,
    "material_certificate_register": _materials,
    "bim_issue_register": _bim_issue,
}


def check_register(tool, rows, finding, today):
    headers = HEADERS[tool]
    examples = _rows(rows, headers)
    if not examples:
        yield finding(tool, "insufficient", "Cần bảng duy nhất có các cột " + ", ".join(headers))
        return
    seen = set()
    for entry, source in examples[:12]:
        key_fields = entry[:2] if tool == "material_certificate_register" else entry[:1]
        key = tuple(part.casefold() for part in key_fields)
        if key in seen:
            yield finding(tool, "invalid_input", "Khóa nghiệp vụ trùng trong mẫu. Cần xác minh dòng gốc.", [source])
            continue
        seen.add(key)
        try:
            level, message, values = _RULES[tool](entry, today)
        except (TypeError, ValueError):
            level, message, values = "invalid_input", "Sai kiểu số, ngày ISO, mã định danh hoặc trạng thái.", {}
        yield finding(tool, level, message, [source], values)


def compare_inventory(older, newer):
    """Compare only a complete bounded set of IFC products and stable attributes."""
    from drive_storage.v75_checks import _finding

    def mapping(parsed):
        rows = parsed["stats"]["comparison_products"]
        if parsed["stats"]["products_total"] != len(rows):
            raise ValueError("Phiên bản IFC vượt số phần tử hỗ trợ đối chiếu đầy đủ")
        result = {}
        for guid, properties in rows:
            if not _IFC_ID.fullmatch(guid) or guid in result:
                raise ValueError("IFC có GlobalId thiếu, sai hoặc trùng")
            result[guid] = properties
        return result

    if older["stats"]["ifc_schema"] != newer["stats"]["ifc_schema"]:
        raise ValueError("Hai phiên bản IFC khác schema; cần xác minh chuyển đổi trước khi đối chiếu")
    previous, current = mapping(older), mapping(newer)
    if not previous or not current:
        raise ValueError("Cần hai mô hình IFC có phần tử để đối chiếu")
    added = current.keys() - previous.keys()
    removed = previous.keys() - current.keys()
    changed = {guid for guid in current.keys() & previous.keys() if current[guid] != previous[guid]}
    comparisons = (("added", "Mới", added), ("removed", "Không còn", removed), ("changed", "Đổi thuộc tính", changed))
    summary = {key: len(ids) for key, _, ids in comparisons}
    yield _finding("ifc_revision_delta", "calculated", "Đối chiếu GlobalId, lớp IFC và thuộc tính định danh.",
                   [older["provenance"]["revision"], newer["provenance"]["revision"]], summary)
    for key, label, ids in comparisons:
        if ids:
            yield _finding("ifc_revision_delta", "sampled", label + " theo GlobalId.",
                           [f"IFC:GlobalId:{guid}" for guid in sorted(ids)[:8]], {"kind": key, "count": len(ids)})
