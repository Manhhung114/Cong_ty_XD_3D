"""V7.3 bounded engineering tools: no DWG claims and no overwrite of originals."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

ALLOWED_REVIEW_LAYERS = {"AI_REVIEW_NOTES"}
MAX_SOURCE_BYTES = 50*1024*1024
MAX_NOTES = 80


def annotate_dxf_copy(src: str | Path, dest: str | Path,
                      notes: list[dict], *, human_authorized=False) -> dict:
    """Write a SEPARATE copy of an ASCII DXF with review notes.

    Requires human authorization; does not validate engineering compliance,
    perform clashes or modify any source DWG/RVT. Caller controls upload to
    Drive after review, with a new revision and ACL.
    """
    if human_authorized is not True:
        raise PermissionError("Cần kỹ sư xác nhận trước khi tạo bản sửa DXF")
    source, output=Path(src).resolve(),Path(dest).resolve()
    if source==output or source.suffix.lower()!=".dxf" or output.suffix.lower()!=".dxf":
        raise ValueError("Chỉ hỗ trợ tạo bản DXF mới, không ghi đè nguồn")
    if not source.is_file() or not 0<source.stat().st_size<=MAX_SOURCE_BYTES:
        raise ValueError("File nguồn phải là DXF hợp lệ tối đa 50 MiB")
    if not isinstance(notes,list) or len(notes)>MAX_NOTES:
        raise ValueError("Tối đa 80 ghi chú review trong một bản DXF")
    import ezdxf
    document=ezdxf.readfile(str(source))
    model=document.modelspace()
    if "AI_REVIEW_NOTES" not in document.layers:
        document.layers.new("AI_REVIEW_NOTES")
    for item in notes:
        if not isinstance(item,dict):
            raise ValueError("Ghi chú không hợp lệ")
        label=str(item.get("note") or "")
        x,y=item.get("x"),item.get("y")
        if not label or len(label)>160 or any(ord(c)<32 for c in label):
            raise ValueError("Nội dung ghi chú không hợp lệ")
        if not all(isinstance(v,(int,float)) and abs(v)<1e7 for v in (x,y)):
            raise ValueError("Tọa độ ghi chú không hợp lệ")
        model.add_text(label, dxfattribs={"layer":"AI_REVIEW_NOTES",
                       "height":2.5,"insert":(float(x),float(y))})
    output.parent.mkdir(parents=True,exist_ok=True)
    with NamedTemporaryFile(dir=output.parent,suffix=".dxf",delete=False) as tmp:
        temp=Path(tmp.name)
    try:
        document.saveas(str(temp))
        if output.exists():
            raise FileExistsError("Bản DXF đích đã có; cần đặt revision mới")
        os.replace(temp,output)
    finally:
        temp.unlink(missing_ok=True)
    return {"sourceSha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "outputSha256":hashlib.sha256(output.read_bytes()).hexdigest(),
            "outputPath":str(output),"notesAdded":len(notes),
            "humanReviewRequired":True,"complianceVerified":False}


def extract_pdf_tables(filepath: str | Path, *, max_pages=8, max_rows=150):
    """Optional pdfplumber bounded table extraction; no OCR/compliance claim."""
    file=Path(filepath)
    if file.suffix.lower()!=".pdf" or not file.is_file() or file.stat().st_size>MAX_SOURCE_BYTES:
        raise ValueError("Chỉ hỗ trợ PDF dưới 50 MiB")
    import pdfplumber
    result=[]
    with pdfplumber.open(str(file)) as pdf:
        for i,page in enumerate(pdf.pages[:max_pages]):
            for table in page.extract_tables() or []:
                for rowno,row in enumerate(table[:max_rows]):
                    result.append({"source":f"PDF:p{i+1}:r{rowno+1}",
                                   "cells":[str(x or "")[:160] for x in row[:20]]})
                    if len(result)>=max_rows:
                        return result
    return result
