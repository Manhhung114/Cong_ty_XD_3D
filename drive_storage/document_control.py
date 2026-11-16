"""Server-side Google Drive file reconciliation and signed document workflow.

Every file is enumerated from the *authorized project's actual category folders*,
including files uploaded before V6.0. No Drive owner email is presented as the
uploader: that Google identity is the server OAuth account, not the operator.
"""
from __future__ import annotations

import re
from pathlib import PurePath
from urllib.parse import urlparse

from drive_storage.access_control import can_admin, can_upload
from drive_storage.manager import FOLDER_CATEGORIES
from drive_storage.shared_workspace import _clean_text, _require_id

STATUS_LABELS = {
    "unregistered": "Chưa lập sổ", "draft": "Mới lập sổ",
    "pending": "Chờ duyệt", "approved": "Đã duyệt",
    "returned": "Yêu cầu sửa", "archived": "Lưu trữ",
    "missing": "Không tìm thấy trên Drive",
}
MAX_INVENTORY = 3000


def base_code(filename: str) -> str:
    """A_R01.pdf, A_R02.pdf → A (same family, separate immutable files)."""
    name = PurePath(str(filename or "")).name
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return re.sub(r"_R\d{2,4}$", "", name, flags=re.I)[:80]


def revision(filename: str, props=None) -> str:
    props = props or {}
    raw = str(props.get("revision") or "")
    if raw.isdigit():
        return f"R{int(raw):02d}"
    match = re.search(r"_R(\d{2,4})(?=\.)", str(filename or ""), flags=re.I)
    return "R" + match.group(1) if match else ""


def allowed_drive_link(url) -> str:
    uri = str(url or "")
    parsed = urlparse(uri)
    if parsed.scheme == "https" and parsed.hostname in {
        "drive.google.com", "docs.google.com"
    } and not parsed.username and not parsed.password:
        return uri
    return ""


def inventory(workspace, identity, project_id: str, registered_documents=None) -> dict:
    pid = workspace._check_project(identity, project_id)
    registered = {
        d["id"]: d for d in (registered_documents if registered_documents is not None else workspace.snapshot(identity)["documents"])
        if d["projectId"] == pid
    }
    items, found_ids = [], set()
    for category in FOLDER_CATEGORIES:
        for row in workspace.storage.list_category_files(project_id=pid, category=category):
            fid = _require_id(row.get("id"), "Tệp Drive")
            if fid in found_ids:
                raise RuntimeError("Một tệp nằm trong nhiều nhóm hồ sơ; cần kiểm tra Drive")
            found_ids.add(fid)
            doc = registered.get(fid, {})
            name = _clean_text(row.get("name"), 180, True)
            mtype = str(row.get("mimeType") or "")
            size = int(row.get("size") or 0)
            md5 = str(row.get("md5Checksum") or "")
            stored_md5 = str(doc.get("md5Checksum") or "")
            recorded_size = int(doc.get("sizeBytes") or 0)
            changed = bool(
                (stored_md5 and md5 and stored_md5.lower() != md5.lower())
                or (recorded_size and recorded_size != size)
            )
            items.append({
                "id": fid, "projectId": pid,
                "code": str(doc.get("code") or base_code(name)),
                "filename": name, "category": category,
                "revision": str(doc.get("revision") or revision(name, row.get("appProperties"))),
                "status": str(doc.get("status") or "unregistered"),
                "registered": bool(doc), "missing": False,
                "sizeBytes": size, "mimeType": mtype,
                "createdTime": str(row.get("createdTime") or ""),
                "modifiedTime": str(row.get("modifiedTime") or ""),
                "md5Checksum": md5,
                "integrityWarning": changed,
                "webViewLink": allowed_drive_link(row.get("webViewLink")),
                "actor": str(doc.get("actor") or ""),
                "registeredAt": str(doc.get("registeredAt") or ""),
                "updatedAt": str(doc.get("updatedAt") or ""),
                "description": str(doc.get("description") or ""),
                "taskId": str(doc.get("taskId") or ""),
                "history": doc.get("history", []),
            })
            if len(items) > MAX_INVENTORY:
                raise RuntimeError("Kho có hơn 3.000 tệp; cần phân trang/đưa sang backend SQL")
    # A deleted/moved Drive file must not disappear from the controlled ledger.
    for fid, doc in registered.items():
        if fid not in found_ids:
            items.append({
                "id": fid, "projectId": pid,
                "code": doc["code"], "filename": doc["filename"],
                "category": doc["category"], "revision": doc.get("revision", ""),
                "status": "missing", "lastKnownStatus": doc.get("status", ""),
                "registered": True, "missing": True, "integrityWarning": False,
                "sizeBytes": int(doc.get("sizeBytes") or 0),
                "mimeType": "", "createdTime": "",
                "modifiedTime": "", "md5Checksum": "",
                "webViewLink": "", "actor": doc["actor"],
                "registeredAt": doc["registeredAt"],
                "updatedAt": doc.get("updatedAt", ""),
                "description": doc.get("description", ""),
                "taskId": doc.get("taskId", ""),
                "history": doc.get("history", []),
            })
    # Group by code, discipline and category. The active revision is the
    # latest physically available file, never a missing file or deleted copy.
    groups: dict[tuple[str, str], list] = {}
    for item in items:
        family = (item["category"], base_code(item["code"]).casefold())
        item["group"] = item["category"] + "/" + base_code(item["code"])
        groups.setdefault(family, []).append(item)
    for siblings in groups.values():
        available = [d for d in siblings if not d["missing"]]
        if not available:
            continue
        def score(d):
            digits = re.search(r"\d+", d["revision"])
            return (int(digits.group()) if digits else 0, d["createdTime"], d["id"])
        latest = max(available, key=score)
        for d in siblings:
            d["latest"] = d is latest
            d["revisionCount"] = len(siblings)
    for item in items:
        item.setdefault("latest", False)
        item.setdefault("revisionCount", 1)
    items.sort(key=lambda d: (
        d["missing"], d["modifiedTime"] or d["registeredAt"], d["filename"]
    ), reverse=True)
    counts = {
        "total": len(items),
        "registered": sum(d["registered"] for d in items),
        "unregistered": sum(d["status"] == "unregistered" for d in items),
        "pending": sum(d["status"] == "pending" for d in items),
        "approved": sum(d["status"] == "approved" for d in items),
        "missing": sum(d["missing"] for d in items),
        "modified": sum(d["integrityWarning"] for d in items),
    }
    return {"items": items, "counts": counts, "projectId": pid}


def _registered_document(workspace, identity, project_id, file_id):
    pid = workspace._check_project(identity, project_id, True)
    fid = _require_id(file_id, "Tệp hồ sơ")
    record = next(
        (d for d in workspace.snapshot(identity)["documents"]
         if d["id"] == fid and d["projectId"] == pid), None
    )
    if not record:
        raise ValueError("Tệp chưa ghi sổ hoặc không thuộc dự án được cấp quyền")
    # Check file still physically lives under its signed project/category.
    matches = workspace.storage.list_category_files(project_id=pid, category=record["category"])
    if not any(f["id"] == fid for f in matches):
        raise PermissionError("Tệp không còn ở đúng thư mục Drive; tạm dừng cập nhật")
    return pid, record


def update_metadata(workspace, identity, *, project_id, file_id, code, description="",
                    task_id="", event_id=None):
    if not can_upload(identity):
        raise PermissionError("Chỉ đọc không được sửa hồ sơ")
    pid, doc = _registered_document(workspace, identity, project_id, file_id)
    if doc["status"] not in {"draft", "returned"}:
        raise ValueError("Hồ sơ đang xét duyệt/đã duyệt/lưu trữ không được sửa; hãy tạo revision mới")
    code = _clean_text(code, 80, True)
    description = _clean_text(description, 600)
    if task_id and not any(
        t["id"] == task_id and t["projectId"] == pid
        for t in workspace.snapshot(identity)["tasks"]
    ):
        raise PermissionError("Công việc đính kèm không thuộc dự án")
    return workspace._append(
        identity=identity, project_id=pid, action="document.metadata_updated",
        data={"file_id": doc["id"], "code": code, "description": description,
              "taskId": task_id}, event_id=event_id,
    )


def submit_document(workspace, identity, *, project_id, file_id, comment="", event_id=None):
    if not can_upload(identity):
        raise PermissionError("Chỉ đọc không được trình hồ sơ")
    pid, doc = _registered_document(workspace, identity, project_id, file_id)
    if doc["status"] not in {"draft", "returned"}:
        raise ValueError("Hồ sơ đã trình hoặc phê duyệt; không thể trình lại")
    return workspace._append(
        identity=identity, project_id=pid, action="document.submitted",
        data={"file_id": doc["id"], "comment": _clean_text(comment, 1000)},
        event_id=event_id,
    )


def review_document(workspace, identity, *, project_id, file_id, decision, comment="", event_id=None):
    if not can_admin(identity):
        raise PermissionError("Chỉ Admin được duyệt hoặc trả lại hồ sơ")
    pid, doc = _registered_document(workspace, identity, project_id, file_id)
    if doc["status"] != "pending":
        raise ValueError("Chỉ được duyệt hồ sơ đang chờ")
    if decision not in {"approve", "return"}:
        raise ValueError("Kết quả duyệt không hợp lệ")
    note = _clean_text(comment, 2000, required=(decision == "return"))
    if decision == "return" and len(note) < 5:
        raise ValueError("Phải ghi rõ lý do trả lại ít nhất 5 ký tự")
    return workspace._append(
        identity=identity, project_id=pid,
        action="document.approved" if decision == "approve" else "document.returned",
        data={"file_id": doc["id"], "comment": note}, event_id=event_id,
    )


def archive_document(workspace, identity, *, project_id, file_id, comment, event_id=None):
    if not can_admin(identity):
        raise PermissionError("Chỉ Admin được chuyển hồ sơ vào trạng thái lưu trữ")
    pid, doc = _registered_document(workspace, identity, project_id, file_id)
    if doc["status"] == "archived":
        raise ValueError("Hồ sơ đã được lưu trữ")
    note = _clean_text(comment, 500, required=True)
    if len(note) < 5:
        raise ValueError("Cần nêu lý do lưu trữ ít nhất 5 ký tự")
    return workspace._append(
        identity=identity, project_id=pid, action="document.archived",
        data={"file_id": doc["id"], "comment": note}, event_id=event_id,
    )
