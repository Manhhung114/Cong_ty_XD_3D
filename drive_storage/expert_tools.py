"""V6.4 bounded, read-only engineering file parsers and Drive evidence provenance.

NEVER read arbitrary Drive file IDs. Before bytes are downloaded validate
signed project ACL, registered document/category, Drive parent, size & checksum.
Never execute workbook macros, CAD scripts, IFC custom code or external links.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256, md5
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile
from pathlib import PurePath
from typing import Any
import csv
import re

from drive_storage.shared_workspace import _require_id

# Input-file limit, not the volume of content evaluated or an upload limit.
# Parsing remains sampled/bounded; high-complexity files may need a worker.
MAX_BYTES = 50 * 1024 * 1024
MAX_XLSX_UNCOMPRESSED = 160 * 1024 * 1024
MAX_XLSX_MEMBERS = 2500
MAX_XLSX_MEMBER = 80 * 1024 * 1024
STREAM_DXF_BYTES = 8 * 1024 * 1024
MAX_TEXT = 9000
MAX_RECORDS = 300
MAX_PDF_PAGES = 12
MAX_XLSX_SHEETS = 5
MAX_XLSX_ROWS = 350
MAX_DXF_ENTITIES = 1500
MAX_IFC_ELEMENTS = 1500
SUPPORTED = {".pdf", ".xlsx", ".csv", ".dxf", ".ifc"}
NOT_SUPPORTED = {
    ".dwg": "DWG cần bộ chuyển đổi có bản quyền sang DXF trước khi phân tích",
    ".rvt": "RVT cần xuất IFC hoặc API Revit/worker riêng",
    ".nwd": "NWD cần Navisworks API hoặc bản IFC tương đương",
    ".xls": "Excel .xls cũ cần chuyển thành .xlsx hoặc CSV",
}
_SAFE_CELL = (str, int, float, bool, type(None))


def _text(value: Any, limit: int = 200) -> str:
    if value is None:
        return ""
    val = str(value).replace("\x00", "").strip()
    return val[:limit]


def _digest(data: bytes):
    return {"sha256": sha256(data).hexdigest(), "md5": md5(data).hexdigest()}


def _row(source, kind, text, extra=None):
    return {"source": source, "kind": kind, "text": _text(text, 360),
            **(extra or {})}


def _pdf(data: bytes):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Chưa cài đặt pypdf trên máy chủ") from exc
    reader = PdfReader(BytesIO(data), strict=True)
    if reader.is_encrypted:
        raise ValueError("PDF có mật khẩu; cần cung cấp bản được phép đọc")
    if len(reader.pages) > 500:
        raise ValueError("PDF trên 500 trang: cần worker chuyên dụng")
    records, warnings = [], []
    for idx in range(min(len(reader.pages), MAX_PDF_PAGES)):
        page = reader.pages[idx]
        contents = page.get_contents()
        # pypdf warns compressed content can expand enormously when extracted.
        if contents:
            if not isinstance(contents, list):
                contents = [contents]
            size = sum(len(item.get_data()) for item in contents[:8])
            if size > 1_500_000:
                warnings.append(f"Trang {idx+1}: luồng PDF quá lớn, bỏ qua")
                continue
        text = (page.extract_text() or "")[:2800]
        if not text.strip():
            warnings.append(f"Trang {idx+1}: không có text; PDF scan cần OCR có kiểm soát")
            continue
        for line_no, line in enumerate(text.splitlines()[:95], 1):
            if line.strip():
                records.append(_row(f"PDF:p{idx+1}:line{line_no}", "text", line))
            if len(records) >= MAX_RECORDS:
                break
        if len(records) >= MAX_RECORDS:
            break
    if len(reader.pages) > MAX_PDF_PAGES:
        warnings.append(f"Chỉ đọc {MAX_PDF_PAGES}/{len(reader.pages)} trang đầu")
    return {"type": "pdf", "records": records, "warnings": warnings,
            "stats": {"pages": len(reader.pages), "pages_checked": min(MAX_PDF_PAGES, len(reader.pages))}}


def _spreadsheet(data: bytes):
    try:
        from openpyxl import load_workbook
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError("Chưa cài đặt openpyxl trên máy chủ") from exc
    # ZIP size metadata is checked before openpyxl expands XML in memory.
    # The 50 MiB input limit must not become an unlimited decompression budget.
    try:
        with ZipFile(BytesIO(data)) as archive:
            members = archive.infolist()
            if (len(members) > MAX_XLSX_MEMBERS
                    or any(item.file_size > MAX_XLSX_MEMBER for item in members)
                    or sum(item.file_size for item in members) > MAX_XLSX_UNCOMPRESSED):
                raise ValueError("XLSX có nội dung giải nén quá lớn; cần worker chuyên dụng")
    except BadZipFile as exc:
        raise ValueError("File Excel không phải XLSX hợp lệ") from exc
    wb = load_workbook(BytesIO(data), read_only=True, data_only=True, keep_links=False)
    records, warnings, numbers, header_tables = [], [], [], []
    try:
        for ws in wb.worksheets[:MAX_XLSX_SHEETS]:
            headers = []
            for row_idx, row in enumerate(ws.iter_rows(max_row=MAX_XLSX_ROWS, max_col=32, values_only=True), 1):
                cells = []
                for col_idx, val in enumerate(row, 1):
                    if val is None or not isinstance(val, _SAFE_CELL):
                        continue
                    if isinstance(val, str) and not val.strip():
                        continue
                    loc = f"XLSX:{ws.title}!{get_column_letter(col_idx)}{row_idx}"
                    text = _text(val, 140)
                    records.append(_row(loc, "cell", text, {"row": row_idx, "col": col_idx,
                                                             "sheet": ws.title}))
                    cells.append((col_idx, val))
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        numbers.append({"source": loc, "value": float(val)})
                    if len(records) >= MAX_RECORDS:
                        break
                if row_idx == 1:
                    headers = [_text(v, 80).lower() for v in row]
                if cells and len(header_tables) < 100:
                    # Preserve row-level pairs for deterministic BOQ validation.
                    header_tables.append({"sheet": ws.title, "row": row_idx,
                                          "cells": {str(k): _text(v, 120) for k, v in cells[:14]}})
                if len(records) >= MAX_RECORDS:
                    warnings.append("Giới hạn mẫu 300 ô, cần worker để quét toàn bộ Excel")
                    break
            if ws.max_row and ws.max_row > MAX_XLSX_ROWS:
                warnings.append(f"Sheet {ws.title}: chỉ xét {MAX_XLSX_ROWS} dòng đầu")
            if len(records) >= MAX_RECORDS:
                break
        if len(wb.worksheets) > MAX_XLSX_SHEETS:
            warnings.append("Không đọc hết các sheet; cần worker để quét file lớn")
    finally:
        wb.close()
    return {"type": "xlsx", "records": records, "warnings": warnings,
            "stats": {"sheets_checked": min(len(wb.sheetnames), MAX_XLSX_SHEETS),
                      "sheet_names": wb.sheetnames[:MAX_XLSX_SHEETS],
                      "numeric_cells": numbers[:120],
                      "table_rows": header_tables[:100]}}


def _csv(data: bytes):
    try:
        decoded = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = data.decode("cp1258", errors="replace")
    reader = csv.reader(StringIO(decoded[:1_000_000]))
    records, tables = [], []
    complete = len(decoded) <= 1_000_000
    for row_id, row in enumerate(reader, 1):
        if row_id > MAX_XLSX_ROWS or len(records) >= MAX_RECORDS:
            complete = False
            break
        if len(row) > 32:
            complete = False
        tbl = {}
        for col_id, val in enumerate(row[:32], 1):
            if not str(val).strip():
                continue
            source=f"CSV:row{row_id}:col{col_id}"
            records.append(_row(source, "cell", val, {"row": row_id, "col": col_id}))
            tbl[str(col_id)] = _text(val, 120)
            if len(records) >= MAX_RECORDS:
                complete = False
                break
        if len(tables) < 100:
            tables.append({"sheet": "CSV", "row": row_id, "cells": tbl})
        else:
            complete = False
    return {"type": "csv", "records": records, "warnings": [
        "Chỉ đọc tối đa 350 dòng / 300 ô"
    ], "stats": {"table_rows": tables, "table_complete": complete}}


def _dxf(data: bytes):
    try:
        import ezdxf
    except ImportError as exc:
        raise RuntimeError("Chưa cài đặt ezdxf trên máy chủ") from exc
    if b"AutoCAD Binary DXF" in data[:50]:
        raise ValueError("DXF nhị phân: cần chuyển sang ASCII DXF trên worker")
    # ezdxf.read(StringIO(...)) creates a full in-memory CAD DOM. Stream large
    # ASCII DXF by entity instead, bounded to a verified sample of modelspace.
    # This is read-only and writes only a temporary file, never to Drive.
    if len(data) >= STREAM_DXF_BYTES:
        from ezdxf.addons import iterdxf
        with TemporaryDirectory(prefix="xd_mep_dxf_") as folder:
            path = Path(folder) / "source.dxf"
            path.write_bytes(data)
            drawing = iterdxf.opendxf(path)
            try:
                return _dxf_entities(drawing.modelspace(), streaming=True)
            finally:
                drawing.close()
    decoded = data.decode("utf-8-sig", errors="replace")
    drawing = ezdxf.read(StringIO(decoded))
    return _dxf_entities(drawing.modelspace(), streaming=False)


def _dxf_entities(entities, *, streaming: bool):
    counter, layers, records = Counter(), Counter(), []
    limit_reached = False
    for index, entity in enumerate(entities):
        if index >= MAX_DXF_ENTITIES:
            limit_reached = True
            break
        kind = entity.dxftype()
        layer = _text(entity.dxf.get("layer", "0"), 80)
        handle = _text(entity.dxf.get("handle", ""), 40)
        counter[kind] += 1
        layers[layer] += 1
        desc = f"{kind} layer={layer}"
        if kind in {"TEXT", "MTEXT"}:
            desc += " value=" + _text(entity.dxf.get("text", ""), 160)
        elif kind == "INSERT":
            desc += " block=" + _text(entity.dxf.get("name", ""), 80)
        elif kind in {"LINE", "CIRCLE", "ARC"}:
            desc += " geometry-present"
        records.append(_row(f"DXF:handle:{handle or index}", "entity", desc,
                            {"entity": kind, "layer": layer, "handle": handle}))
    total = sum(counter.values())
    warnings = [
        "DXF chỉ kiểm kê đối tượng / layer; chưa chứng minh xung đột hoặc độ chính xác hình học"
    ]
    if streaming:
        warnings.append("DXF lớn: đọc modelspace theo luồng, chỉ kiểm tra mẫu đối tượng")
    if limit_reached:
        warnings.append(f"Chỉ kiểm tra tối đa {MAX_DXF_ENTITIES} đối tượng đầu, không quét toàn bản vẽ")
    return {"type": "dxf", "records": records[:MAX_RECORDS], "warnings": warnings,
            "stats": {"entities_checked": total, "types": dict(counter.most_common(30)),
                      "layers": dict(layers.most_common(30)),
                      "sample_limited": limit_reached}}



def _ifc(data: bytes):
    try:
        import ifcopenshell
    except ImportError as exc:
        raise RuntimeError("Thiếu IfcOpenShell. Cần cài đúng wheel trên worker/server") from exc
    model = ifcopenshell.file.from_string(data.decode("utf-8", errors="replace"))
    elements = model.by_type("IfcProduct")
    if len(elements) > 100_000:
        raise ValueError("Mô hình IFC quá lớn cho Streamlit; cần worker riêng")
    records, counts, guid_seen, duplicated, comparison = [], Counter(), set(), [], []
    for element in elements[:MAX_IFC_ELEMENTS]:
        typ = element.is_a()
        ident = str(getattr(element, "GlobalId", "") or "")
        counts[typ] += 1
        if ident in guid_seen and ident:
            duplicated.append(ident)
        guid_seen.add(ident)
        properties = [typ, *(str(getattr(element, name, None) or "") for name in
                            ("Name", "ObjectType", "PredefinedType", "Tag"))]
        comparison.append((ident, sha256(json.dumps(properties, ensure_ascii=False)
                                      .encode("utf8")).hexdigest()))
        records.append(_row(f"IFC:GlobalId:{ident or element.id()}", "element",
                            f"{typ}: {_text(getattr(element, 'Name', ''), 140)}",
                            {"ifcType": typ, "globalId": ident}))
    return {"type": "ifc", "records": records[:MAX_RECORDS],
            "warnings": ["IFC: đã đọc đối tượng sản phẩm; hình học 3D/clash cần worker",
                         "Chỉ kiểm tra tối đa 1500 phần tử đầu"],
            "stats": {"products_total": len(elements), "products_checked": min(len(elements), MAX_IFC_ELEMENTS),
                      "ifc_types": dict(counts.most_common(30)),
                      "duplicate_global_ids": duplicated[:15],
                      "ifc_schema": model.schema, "comparison_products": comparison}}


PARSERS = {".pdf": _pdf, ".xlsx": _spreadsheet,
           ".csv": _csv, ".dxf": _dxf, ".ifc": _ifc}


def parse_bytes(filename: str, data: bytes):
    """Used by CI with generated fixtures, no network or OAuth required."""
    ext = PurePath(filename).suffix.lower()
    if ext in NOT_SUPPORTED:
        raise ValueError(NOT_SUPPORTED[ext])
    if ext not in SUPPORTED:
        raise ValueError("Định dạng chưa có bộ đọc kỹ thuật có kiểm chứng")
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Chỉ xử lý file đầu vào từ 1 byte đến tối đa 50 MB; file lớn hơn cần worker")
    parsed = PARSERS[ext](data)
    parsed["extension"] = ext
    parsed["hashes"] = _digest(data)
    parsed["recordCount"] = len(parsed["records"])
    # Refs are bounded before any signed event or LLM context is created.
    parsed["records"] = parsed["records"][:MAX_RECORDS]
    return parsed


def extract_registered(workspace, identity, *, project_id: str, file_id: str):
    """Server-side: ACL + signed registration + parent + checksum, then bytes."""
    pid = workspace._check_project(identity, project_id)
    fid = _require_id(file_id, "Tệp kỹ thuật")
    registered = next((d for d in workspace.snapshot(identity)["documents"]
                       if d["id"] == fid and d["projectId"] == pid), None)
    if not registered:
        raise PermissionError("File chưa ghi sổ vào đúng dự án; đăng ký trong Kho tài liệu trước")
    category = registered["category"]
    matching = next((r for r in workspace.storage.list_category_files(
        project_id=pid, category=category) if r.get("id") == fid), None)
    if matching is None:
        raise PermissionError("File không còn trong thư mục Drive của dự án")
    size = int(matching.get("size") or 0)
    if size > MAX_BYTES:
        raise ValueError("File lớn hơn 50 MB: cần worker xử lý chuyên dụng, không tải vào Streamlit")
    original_md5 = str(registered.get("md5Checksum") or "")
    current_md5 = str(matching.get("md5Checksum") or "")
    if original_md5 and current_md5 and original_md5.lower() != current_md5.lower():
        raise PermissionError("Checksum khác bản đã lập sổ, không thực hiện phân tích")
    if registered.get("sizeBytes") and int(registered["sizeBytes"]) != size:
        raise PermissionError("Dung lượng file khác lần ghi sổ")
    blob = workspace.storage.download_small_file(
        project_id=pid, category=category, file_id=fid, max_bytes=MAX_BYTES,
    )
    actual = _digest(blob)
    if current_md5 and actual["md5"].lower() != current_md5.lower():
        raise PermissionError("Nội dung tải từ Drive không khớp MD5 công bố")
    filename = str(matching["name"])
    parsed = parse_bytes(filename, blob)
    parsed["provenance"] = {
        "projectId": pid, "fileId": fid, "filename": filename,
        "category": category, "revision": registered.get("revision", ""),
        "registeredStatus": registered.get("status", ""),
        "md5": actual["md5"], "sha256": actual["sha256"],
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }
    return parsed


def concise_evidence(parsed: dict):
    """Evidence references are stable & short enough for signed event journal."""
    stats = dict(parsed.get("stats") or {})
    stats.pop("numeric_cells", None)
    stats.pop("table_rows", None)
    stats.pop("comparison_products", None)
    return {
        "format": parsed["type"],
        "provenance": parsed.get("provenance", {}),
        "stats": stats,
        "recordCount": parsed["recordCount"],
        "sampleSources": [r["source"] for r in parsed.get("records", [])[:10]],
        "warnings": parsed.get("warnings", [])[:8],
    }
