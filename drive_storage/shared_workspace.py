"""V5.9/V6.0 shared project, task, approval and document ledger on Google Drive.

The current production host runs Streamlit only (no PostgreSQL service). This
append-only, HMAC-signed ledger provides durable cross-device metadata without
writing to ephemeral Streamlit disks or changing existing project documents.
It is an interim backend; a database-backed implementation can replace it.
"""
from __future__ import annotations

import hashlib
import hmac
import io
import json
import re
import uuid
from datetime import datetime, timezone

from drive_storage.access_control import allows_project, can_admin, can_upload, clean_email
from drive_storage.manager import FOLDER_CATEGORIES, validated_project_folder

LEDGER_FOLDER = "_XD_MEP_WORKSPACE_EVENTS_V59"
MAX_EVENTS = 2500
MAX_EVENT_BYTES = 24 * 1024
ALLOWED_DIVISIONS = {"all", "mep", "construction"}
DEPARTMENTS = {
    "director", "electrical", "hvac", "plumbing", "fire", "bim", "qs", "qa",
    "architecture", "structure", "xd_bim", "xd_qs", "xd_planning",
    "xd_site", "xd_safety", "xd_material",
}
ACTIONS = {
    "project.created", "task.created", "task.started",
    "task.submitted", "task.approved", "task.returned", "document.registered",
    "document.metadata_updated", "document.submitted", "document.approved",
    "document.returned", "document.archived",
    "agent.completed", "handoff.requested", "handoff.resolved",
}
ID = re.compile(r"^[A-Za-z0-9_-]{12,160}$")
EVENT_ID = re.compile(r"^[0-9a-f]{32}$")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _serial(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")


def _clean_text(value, limit=300, required=False):
    val = str(value or "").strip()
    if len(val) > limit or (required and not val):
        raise ValueError("Nội dung thiếu hoặc vượt giới hạn ký tự")
    return val


def _require_id(value, label="ID"):
    if not ID.fullmatch(str(value or "")):
        raise ValueError(label + " không hợp lệ")
    return str(value)


def _event_signature(event, key):
    if not isinstance(key, str) or len(key) < 32:
        raise RuntimeError("Thiếu khóa ký dữ liệu dùng chung trong [auth].cookie_secret")
    return hmac.new(key.encode("utf8"), _serial(event), hashlib.sha256).hexdigest()


class SharedWorkspace:
    def __init__(self, storage, signing_key: str):
        self.storage = storage
        self.key = signing_key
        if len(signing_key or "") < 32:
            raise RuntimeError("Chưa có khóa bảo mật dữ liệu dùng chung")

    def _ledger_id(self, create=False):
        items = self.storage._folders_named(self.storage.root_id, LEDGER_FOLDER)
        if len(items) > 1:
            raise RuntimeError("Có nhiều thư mục dữ liệu dùng chung trùng tên")
        if items:
            return items[0]["id"]
        return self.storage.folder(self.storage.root_id, LEDGER_FOLDER) if create else None

    def _records(self):
        parent = self._ledger_id(create=False)
        if not parent:
            return []
        q = f"'{parent}' in parents and trashed = false"
        items, token = [], None
        while True:
            response = self.storage.service.files().list(
                q=q, pageSize=1000, pageToken=token,
                fields="nextPageToken,files(id,name,size,mimeType,parents)",
            ).execute()
            for row in response.get("files", []):
                name = str(row.get("name") or "")
                if (parent not in row.get("parents", [])
                        or row.get("mimeType") != "application/json"
                        or not re.fullmatch(r"ev_[0-9a-f]{32}\.json", name)
                        or int(row.get("size") or 0) > MAX_EVENT_BYTES):
                    raise RuntimeError("Tệp nhật ký dự án không hợp lệ; từ chối tải dữ liệu")
                items.append(row)
                if len(items) > MAX_EVENTS:
                    raise RuntimeError("Kho nhật ký quá giới hạn. Cần lưu trữ theo lô trước khi tiếp tục")
            token = response.get("nextPageToken")
            if not token:
                break
        return sorted(items, key=lambda x: x["name"])

    def events(self):
        result = []
        for row in self._records():
            raw = self.storage.service.files().get_media(fileId=row["id"]).execute()
            if not isinstance(raw, bytes) or len(raw) > MAX_EVENT_BYTES:
                raise RuntimeError("Không đọc được nhật ký từ Google Drive")
            payload = json.loads(raw.decode("utf8"))
            if not isinstance(payload, dict):
                raise RuntimeError("Nhật ký không hợp lệ")
            signature = payload.pop("_signature", "")
            if not hmac.compare_digest(str(signature), _event_signature(payload, self.key)):
                raise PermissionError("Nhật ký bị sửa đổi ngoài hệ thống")
            if (payload.get("version") != 1
                    or payload.get("action") not in ACTIONS
                    or not EVENT_ID.fullmatch(str(payload.get("id") or ""))
                    or row["name"] != "ev_" + payload["id"] + ".json"
                    or not isinstance(payload.get("data"), dict)
                    or not ID.fullmatch(str(payload.get("project_id") or ""))):
                raise ValueError("Sự kiện nghiệp vụ không hợp lệ")
            result.append(payload)
        return sorted(result, key=lambda x: (x.get("at", ""), x["id"]))

    def _append(self, *, identity, project_id, action, data, event_id=None):
        if not can_upload(identity) or action not in ACTIONS:
            raise PermissionError("Không có quyền cập nhật nghiệp vụ")
        project_id = _require_id(project_id, "Dự án")
        if not allows_project(identity, project_id):
            raise PermissionError("Ngoài phạm vi dự án")
        eid = str(event_id or uuid.uuid4().hex).lower()
        if not EVENT_ID.fullmatch(eid):
            raise ValueError("Mã thao tác không hợp lệ")
        # Idempotency: a repeated UI event does not create another action.
        parent = self._ledger_id(create=True)
        name = "ev_" + eid + ".json"
        q = f"'{parent}' in parents and name = '{name}' and trashed = false"
        known = self.storage.service.files().list(
            q=q, fields="files(id)", pageSize=2,
        ).execute().get("files", [])
        if known:
            if len(known) != 1:
                raise RuntimeError("Sự kiện có mã trùng")
            return {"id": eid, "existing": True}
        evt = {
            "version": 1, "id": eid, "at": _now(),
            "actor": clean_email(identity["email"]),
            "project_id": project_id, "action": action, "data": data,
        }
        encoded = _serial({**evt, "_signature": _event_signature(evt, self.key)})
        if len(encoded) > MAX_EVENT_BYTES:
            raise ValueError("Nội dung thao tác vượt giới hạn")
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(io.BytesIO(encoded), mimetype="application/json", resumable=False)
        created = self.storage.service.files().create(
            body={"name": name, "parents": [parent], "mimeType": "application/json",
                  "description": "XD MEP immutable workspace event"},
            media_body=media, fields="id,name,parents",
        ).execute()
        if parent not in created.get("parents", []) or created.get("name") != name:
            raise RuntimeError("Google Drive không xác nhận vị trí nhật ký")
        return {"id": eid, "existing": False}

    def _projects(self, identity):
        items = self.storage.list_projects()
        return [
            {"id": p["id"], "code": p["name"].split("_", 1)[0],
             "name": p["name"].split("_", 1)[1].replace("_", " ") if "_" in p["name"] else p["name"],
             "driveName": p["name"], "client": "", "location": "", "division": "all"}
            for p in items if allows_project(identity, p["id"])
        ]

    def snapshot(self, identity):
        if not identity or identity.get("role") not in {"read", "update", "admin"}:
            raise PermissionError("Chưa được cấp quyền")
        projects = self._projects(identity)
        allowed = {p["id"] for p in projects}
        task_map, documents, audit, handoff_map, agent_runs = {}, {}, [], {}, []
        for event in self.events():
            pid = event["project_id"]
            if pid not in allowed:
                continue
            action, data = event["action"], event["data"]
            entry = {"id": event["id"], "at": event["at"], "actor": event["actor"],
                     "projectId": pid, "action": action}
            if action == "project.created":
                project = next(p for p in projects if p["id"] == pid)
                project.update({k: data.get(k, "") for k in ("client", "location", "division")})
                project["name"] = data.get("name", project["name"])
            elif action == "task.created":
                tid = event["id"]
                task_map[tid] = {
                    "id": tid, "projectId": pid, "code": "CV-" + tid[:8].upper(),
                    "title": data["title"], "dept": data["dept"],
                    "assignee": data.get("assignee", ""), "docCode": data.get("docCode", ""),
                    "dueDate": data.get("dueDate", ""), "status": "todo",
                    "report": "", "findings": "", "reviewHistory": [],
                    "createdBy": event["actor"], "createdAt": event["at"],
                    "legacy": data.get("legacy", {}),
                }
            elif action.startswith("task."):
                task = task_map.get(data.get("task_id"))
                if task is None or task["projectId"] != pid:
                    raise ValueError("Nhật ký có nhiệm vụ không hợp lệ")
                if action == "task.started":
                    if task["status"] == "todo":
                        task["status"] = "working"
                elif action == "task.submitted":
                    if task["status"] in {"todo", "working"}:
                        task.update({"status": "review", "report": data["summary"],
                                     "findings": data.get("findings", "")})
                        task["reviewHistory"].append({"at": event["at"], "actor": event["actor"],
                                                      "decision": "submitted", "note": data["summary"]})
                elif action in {"task.approved", "task.returned"} and task["status"] == "review":
                    task["status"] = "done" if action == "task.approved" else "working"
                    task["reviewHistory"].append({"at": event["at"], "actor": event["actor"],
                                                  "decision": "approve" if action == "task.approved" else "reject",
                                                  "note": data.get("comment", "")})
            elif action == "handoff.requested":
                task_id = data.get("task_id")
                task = task_map.get(task_id)
                if task is None or task["projectId"] != pid:
                    raise ValueError("Luồng phối hợp tham chiếu nhiệm vụ không thuộc dự án")
                from drive_storage.company_agents import agents
                target = data.get("target_dept")
                if (target not in {p["department"] for p in agents().values()}
                        or target == task["dept"]):
                    raise ValueError("Phòng nhận phối hợp không hợp lệ")
                handoff_map[event["id"]] = {
                    "id": event["id"], "projectId": pid, "taskId": task_id,
                    "title": task["title"], "sourceDept": task["dept"],
                    "targetDept": target, "status": "open",
                    "reason": data["reason"], "response": "",
                    "actor": event["actor"], "createdAt": event["at"],
                    "resolvedBy": "", "resolvedAt": "",
                }
            elif action == "handoff.resolved":
                handoff = handoff_map.get(data.get("handoff_id"))
                if handoff is None or handoff["projectId"] != pid:
                    raise ValueError("Luồng phối hợp không tồn tại")
                if handoff["status"] != "open":
                    raise ValueError("Luồng phối hợp đã được đóng")
                handoff.update({
                    "status": "resolved", "response": data["response"],
                    "resolvedAt": event["at"], "resolvedBy": event["actor"],
                })
            elif action == "agent.completed":
                from drive_storage.company_agents import agents
                task_id, agent_id = data.get("task_id"), data.get("agent_id")
                task = task_map.get(task_id)
                profile = agents().get(agent_id)
                if not task or task["projectId"] != pid or not profile:
                    raise ValueError("Báo cáo Agent không gắn với công việc hoặc Agent hợp lệ")
                if (profile["department"] != task["dept"]
                        and agent_id not in {"PM", "CEO", "DOC", "QAC"}):
                    raise ValueError("Agent không thuộc bộ môn nhiệm vụ")
                if not data.get("reviewRequired") or data.get("mode") not in {"llm", "preflight"}:
                    raise ValueError("Kết quả Agent không có kiểm duyệt")
                agent_runs.append({
                    "id": event["id"], "projectId": pid,
                    "taskId": task_id, "agentId": agent_id,
                    "agentTitle": profile["title"],
                    "actor": event["actor"], "at": event["at"],
                    "mode": data["mode"], "provider": data.get("provider", "none"),
                    "model": data.get("model", ""),
                    "result": data["result"], "missing": data.get("missing", []),
                    "risks": data.get("risks", []), "evidence": data.get("evidence", []),
                    "reviewRequired": True,
                })
            elif action == "document.registered":
                did = data["file_id"]
                history_entry = {
                    "at": event["at"], "actor": event["actor"],
                    "action": "document.registered", "note": data.get("description", ""),
                }
                if did in documents:
                    # V6.0 allowed registering the same Drive file repeatedly.
                    # Preserve those historical events and do NOT reset an
                    # already approved/archived status or lose its audit trail.
                    old = documents[did]
                    if old["projectId"] != pid or old["category"] != data["category"]:
                        raise ValueError("Tệp được ghi sổ dưới nhiều dự án/nhóm hồ sơ")
                    old.update({
                        "code": data["code"],
                        "description": data.get("description", ""),
                        "taskId": data.get("task_id", ""),
                        "updatedAt": event["at"],
                    })
                    old["history"].append(history_entry)
                else:
                    documents[did] = {
                        "id": did, "projectId": pid, "code": data["code"],
                        "filename": data["filename"], "category": data["category"],
                        "revision": data.get("revision", ""),
                        "description": data.get("description", ""),
                        "taskId": data.get("task_id", ""),
                        "sizeBytes": data.get("size_bytes", 0),
                        "md5Checksum": data.get("md5_checksum", ""),
                        "registeredAt": event["at"], "updatedAt": event["at"],
                        "actor": event["actor"], "status": "draft",
                        "history": [history_entry],
                    }
            elif action.startswith("document."):
                did = data.get("file_id")
                doc = documents.get(did)
                if not doc or doc["projectId"] != pid:
                    raise ValueError("Nhật ký hồ sơ tham chiếu tệp chưa đăng ký hoặc sai dự án")
                status = doc["status"]
                if action == "document.metadata_updated":
                    if status not in {"draft", "returned"}:
                        raise ValueError("Hồ sơ đã trình duyệt hoặc phê duyệt không thể sửa metadata")
                    for key in ("code", "description", "taskId"):
                        doc[key] = data[key]
                elif action == "document.submitted":
                    if status not in {"draft", "returned"}:
                        raise ValueError("Trạng thái trình hồ sơ không hợp lệ")
                    doc["status"] = "pending"
                elif action == "document.approved":
                    if status != "pending":
                        raise ValueError("Hồ sơ không ở trạng thái chờ duyệt")
                    doc["status"] = "approved"
                elif action == "document.returned":
                    if status != "pending":
                        raise ValueError("Hồ sơ không ở trạng thái chờ duyệt")
                    doc["status"] = "returned"
                elif action == "document.archived":
                    if status == "archived":
                        raise ValueError("Hồ sơ đã lưu trữ")
                    doc["status"] = "archived"
                doc["updatedAt"] = event["at"]
                doc["history"].append({
                    "at": event["at"], "actor": event["actor"],
                    "action": action, "note": data.get("comment", data.get("description", "")),
                })
            audit.append({**entry, "detail": _clean_text(data.get("title", data.get("code", "")), 160)})
        tasks = sorted(task_map.values(), key=lambda x: x["createdAt"], reverse=True)
        return {"version": 63, "projects": projects, "tasks": tasks,
                "documents": list(documents.values()), "events": audit[-200:],
                "handoffs": sorted(handoff_map.values(), key=lambda h: h["createdAt"], reverse=True),
                "agentRuns": sorted(agent_runs, key=lambda r: r["at"], reverse=True)[:200],
                "role": identity["role"], "actor": identity["email"]}

    def _check_project(self, identity, project_id, write=False):
        pid = _require_id(project_id, "Mã dự án")
        if not allows_project(identity, pid):
            raise PermissionError("Không có quyền xem dự án")
        if write and not can_upload(identity):
            raise PermissionError("Chỉ đọc không được cập nhật")
        self.storage.project_by_id(pid)
        return pid

    def create_project(self, identity, *, code, name, client="", location="", division="all", event_id=None):
        if not can_admin(identity):
            raise PermissionError("Chỉ Admin được tạo dự án")
        name = _clean_text(name, 80, True)
        folder_name = validated_project_folder(code, name)
        code = code.strip().upper()
        # Reject duplicate project codes unless already created by this operation.
        known = self.storage.list_projects()
        if any(p["name"].upper().startswith(code + "_") for p in known):
            raise ValueError("Mã dự án đã tồn tại trên Google Drive")
        project_id = self.storage.ensure_project_tree(code, name)
        self._append(
            identity=identity, project_id=project_id, action="project.created",
            data={"name": name, "client": _clean_text(client, 160),
                  "location": _clean_text(location, 160),
                  "division": division if division in ALLOWED_DIVISIONS else "all",
                  "folder": folder_name}, event_id=event_id,
        )
        return project_id

    def create_task(self, identity, *, project_id, title, dept, assignee="",
                    doc_code="", due_date="", event_id=None):
        pid = self._check_project(identity, project_id, True)
        if dept not in DEPARTMENTS:
            raise ValueError("Bộ môn không hợp lệ")
        if due_date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", due_date):
            raise ValueError("Ngày hạn không hợp lệ")
        return self._append(
            identity=identity, project_id=pid, action="task.created",
            data={"title": _clean_text(title, 240, True), "dept": dept,
                  "assignee": _clean_text(assignee, 160), "docCode": _clean_text(doc_code, 80),
                  "dueDate": due_date}, event_id=event_id,
        )

    def _current_task(self, identity, project_id, task_id):
        pid = self._check_project(identity, project_id, True)
        task = next((x for x in self.snapshot(identity)["tasks"]
                     if x["id"] == task_id and x["projectId"] == pid), None)
        if task is None:
            raise ValueError("Không tìm thấy nhiệm vụ trong dự án")
        return pid, task

    def start_task(self, identity, *, project_id, task_id, event_id=None):
        pid, task = self._current_task(identity, project_id, task_id)
        if task["status"] != "todo":
            raise ValueError("Nhiệm vụ không ở trạng thái chờ")
        return self._append(identity=identity, project_id=pid, action="task.started",
                            data={"task_id": task_id}, event_id=event_id)

    def submit_task(self, identity, *, project_id, task_id, summary, findings="", event_id=None):
        pid, task = self._current_task(identity, project_id, task_id)
        if task["status"] not in {"todo", "working"}:
            raise ValueError("Nhiệm vụ không ở trạng thái thực hiện")
        summary = _clean_text(summary, 4000, True)
        if len(summary) < 12:
            raise ValueError("Báo cáo phải có ít nhất 12 ký tự")
        return self._append(identity=identity, project_id=pid, action="task.submitted",
                            data={"task_id": task_id, "summary": summary,
                                  "findings": _clean_text(findings, 2000)}, event_id=event_id)

    def review_task(self, identity, *, project_id, task_id, decision, comment="", event_id=None):
        if not can_admin(identity):
            raise PermissionError("Chỉ Admin được phê duyệt hoặc trả lại")
        pid, task = self._current_task(identity, project_id, task_id)
        if task["status"] != "review":
            raise ValueError("Nhiệm vụ không ở trạng thái chờ duyệt")
        if decision not in {"approve", "reject"}:
            raise ValueError("Quyết định không hợp lệ")
        comment = _clean_text(comment, 2000, decision == "reject")
        if decision == "reject" and len(comment) < 5:
            raise ValueError("Phải ghi rõ lý do trả lại")
        action = "task.approved" if decision == "approve" else "task.returned"
        return self._append(identity=identity, project_id=pid, action=action,
                            data={"task_id": task_id, "comment": comment}, event_id=event_id)

    def import_legacy_workspace(self, identity, source: dict):
        """Explicit, idempotent metadata import; original local backup remains intact.

        Old approval/review data is retained as an *unverified note*, never
        promoted to a signed decision from an authenticated reviewer.
        """
        if not can_admin(identity):
            raise PermissionError("Chỉ Admin được chuyển dữ liệu cũ")
        if not isinstance(source, dict):
            raise ValueError("Bản sao dữ liệu phải là JSON object")
        raw = source.get("workspace", source)
        if not isinstance(raw, dict):
            raise ValueError("Không có dữ liệu dự án trong file")
        projects, tasks = raw.get("projects"), raw.get("tasks")
        if (not isinstance(projects, list) or not isinstance(tasks, list)
                or len(projects) > 50 or len(tasks) > 500):
            raise ValueError("Bản sao vượt giới hạn 50 dự án/500 công việc")
        source_projects = {}
        for p in projects:
            if not isinstance(p, dict):
                raise ValueError("Dự án cục bộ không hợp lệ")
            code = _clean_text(p.get("code"), 50, True).upper()
            name = _clean_text(p.get("name"), 80, True)
            folder = validated_project_folder(code, name)
            local_id = _clean_text(p.get("id"), 160, True)
            if local_id in source_projects:
                raise ValueError("Dự án cũ bị trùng mã nội bộ")
            source_projects[local_id] = {
                "code": code, "name": name, "folder": folder,
                "client": _clean_text(p.get("client"), 160),
                "location": _clean_text(p.get("location"), 160),
            }
        prepared = []
        for t in tasks:
            if not isinstance(t, dict) or t.get("projectId") not in source_projects:
                raise ValueError("Công việc cũ không có dự án hợp lệ")
            dept = str(t.get("dept") or "")
            if dept not in DEPARTMENTS:
                raise ValueError("Bộ môn của công việc cũ không hợp lệ")
            title = _clean_text(t.get("title"), 240, True)
            local_task_id = _clean_text(t.get("id") or t.get("code"), 160, True)
            legacy = {
                "status": _clean_text(t.get("status"), 24),
                "report": _clean_text(t.get("report"), 4000),
                "note": "Dữ liệu cũ chưa xác thực danh tính người phê duyệt",
            }
            prepared.append((source_projects[t["projectId"]], {
                "title": title, "dept": dept,
                "assignee": _clean_text(t.get("assignee"), 160),
                "docCode": _clean_text(t.get("docCode"), 80),
                "dueDate": "",
                "legacy": legacy,
            }, local_task_id))

        # Check for project code collisions before any mutation.
        existing = self.storage.list_projects()
        mapped = {}
        for p in source_projects.values():
            same_code = [d for d in existing if
                         d["name"].upper().startswith(p["code"] + "_")]
            if len(same_code) > 1 or (same_code and
                    same_code[0]["name"].casefold() != p["folder"].casefold()):
                raise ValueError("Mã dự án đã tồn tại với tên khác trên Drive: " + p["code"])
            if p["code"] in mapped and mapped[p["code"]]["folder"] != p["folder"]:
                raise ValueError("Mã dự án trùng trong dữ liệu cũ")
            mapped[p["code"]] = p

        linked = {}
        for old_id, p in source_projects.items():
            matching = next((d for d in existing if
                             d["name"].casefold() == p["folder"].casefold()), None)
            pid = matching["id"] if matching else self.storage.ensure_project_tree(
                p["code"], p["name"]
            )
            event_id = hashlib.sha256(("xd-import-project:" + p["code"]).encode("utf8")).hexdigest()[:32]
            self._append(identity=identity, project_id=pid, action="project.created",
                         data={"name": p["name"], "client": p["client"],
                               "location": p["location"], "division": "all",
                               "folder": p["folder"]}, event_id=event_id)
            linked[old_id] = pid
        count = 0
        for p, data, old_task_id in prepared:
            digest = hashlib.sha256(
                ("xd-import-task:" + p["code"] + ":" + old_task_id).encode("utf8")
            ).hexdigest()[:32]
            project_id = next(linked[old_id] for old_id, v in source_projects.items()
                              if v is p)
            result = self._append(identity=identity, project_id=project_id,
                                  action="task.created", data=data, event_id=digest)
            count += 0 if result["existing"] else 1
        return {"projects": len(linked), "newTasks": count,
                "message": "Giữ bản sao gốc để đối chiếu và tải riêng các tệp IndexedDB"}

    def register_document(self, identity, *, project_id, category, file_id,
                          code="", description="", task_id="", event_id=None):
        pid = self._check_project(identity, project_id, True)
        if category not in FOLDER_CATEGORIES:
            raise ValueError("Loại hồ sơ không hợp lệ")
        fid = _require_id(file_id, "Tệp Drive")
        matching = next((f for f in self.storage.list_category_files(project_id=pid, category=category)
                         if f["id"] == fid), None)
        if not matching:
            raise PermissionError("Tệp không thuộc dự án/mục hồ sơ đã chọn")
        if task_id:
            if not any(t["id"] == task_id and t["projectId"] == pid
                       for t in self.snapshot(identity)["tasks"]):
                raise PermissionError("Nhiệm vụ đính kèm không thuộc dự án")
        if any(doc["id"] == fid and doc["projectId"] == pid
               for doc in self.snapshot(identity)["documents"]):
            raise ValueError("Tệp đã ghi sổ; hãy dùng Quản lý hồ sơ để chỉnh thông tin hoặc trình duyệt")
        filename = _clean_text(matching["name"], 180, True)
        match = re.search(r"_R(\d{2,4})\.", filename, flags=re.I)
        revision = "R" + match.group(1) if match else ""
        return self._append(identity=identity, project_id=pid, action="document.registered",
                            data={"file_id": fid, "filename": filename, "category": category,
                                  "revision": revision, "code": _clean_text(code, 80) or
                                  re.sub(r"_R\d{2,4}$", "", filename.rsplit(".", 1)[0], flags=re.I),
                                  "description": _clean_text(description, 600), "task_id": task_id,
                                  "size_bytes": int(matching.get("size") or 0),
                                  "md5_checksum": str(matching.get("md5Checksum") or "")[:64]},
                            event_id=event_id)
