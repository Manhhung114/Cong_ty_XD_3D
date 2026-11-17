"""Authenticated native dialogs for V5.9/V6.0 shared project management.

These are launched by controls *inside* the existing 3D project/task/review
sheets, not by separate navigation or an unauthenticated API endpoint.
"""
from __future__ import annotations

import re
import json
from datetime import date

from drive_storage.access_control import identity_for, can_admin, can_upload, allows_project
from drive_storage.manager import from_streamlit_secrets
from drive_storage.shared_workspace import SharedWorkspace, DEPARTMENTS

COMMANDS = {
    "projects": {"refresh", "select", "project_create", "project_import"},
    "tasks": {"refresh", "select", "task_create", "task_assign", "task_withdraw", "task_start", "task_submit"},
    "reviews": {"refresh", "select", "task_review"},
    "documents": {"refresh", "select", "document_inventory", "document_manage"},
    "activity": {"refresh", "select"},
    "agents": {"refresh", "select", "agent_run"},
    "company": {"refresh", "select", "handoff_create", "handoff_resolve", "ops_audit"},
    "monitor": {"refresh", "select"},
}
DEPARTMENT_NAMES = {
    "director": "Ban giám đốc", "electrical": "Điện", "hvac": "HVAC",
    "plumbing": "Cấp thoát nước", "fire": "PCCC", "bim": "BIM MEP",
    "qs": "BOQ MEP", "qa": "QA/QC MEP", "architecture": "Kiến trúc",
    "structure": "Kết cấu", "xd_bim": "BIM Xây dựng", "xd_qs": "BOQ Xây dựng",
    "xd_planning": "Kế hoạch", "xd_site": "Hiện trường",
    "xd_safety": "An toàn XD", "xd_material": "Vật tư",
}
INTERACTIVE = {"project_create", "project_import", "task_create", "task_assign", "task_withdraw", "task_submit",
               "task_review", "document_manage", "agent_run", "handoff_create",
               "handoff_resolve", "ops_audit"}


def service_for(st):
    """Credentials never leave the Streamlit server."""
    drive = dict(st.secrets.get("drive", {}))
    key = str(st.secrets.get("auth", {}).get("cookie_secret", ""))
    return SharedWorkspace(from_streamlit_secrets(drive), key)


def load_snapshot(st) -> dict:
    actor = identity_for(st)
    if not actor:
        raise PermissionError("Phiên đăng nhập không còn quyền truy cập")
    workspace = service_for(st)
    snapshot = workspace.snapshot(actor, include_monitor=True) if st.session_state.get("xd_current_sheet") == "monitor" else workspace.snapshot(actor)
    requested = str(st.session_state.get("xd_selected_cloud_project", ""))
    valid = {p["id"] for p in snapshot["projects"]}
    selected = requested if requested in valid else (snapshot["projects"][0]["id"] if snapshot["projects"] else "")
    st.session_state.xd_selected_cloud_project = selected
    snapshot.update({"enabled": True, "selectedProjectId": selected})
    if st.session_state.get("xd_current_sheet") == "monitor":
        from drive_storage.monitoring import ALL_DEPARTMENTS
        prefs = dict(st.session_state.get("xd_monitor_preferences") or {})
        snapshot["monitorPreferences"] = {
            "project": prefs.get("project") if prefs.get("project") in valid else "all",
            "system": prefs.get("system") if prefs.get("system") in
                {"all", "mep", "xd", "cross"} else "all",
            "period": prefs.get("period") if prefs.get("period") in
                {"hour", "today", "week"} else "today",
            "department": prefs.get("department") if prefs.get("department") in
                ALL_DEPARTMENTS else "all",
        }
    from drive_storage.company_agents import company_metrics, public_catalog
    from drive_storage.company_ui import ai_status
    snapshot["companyMetrics"] = company_metrics(snapshot)
    snapshot["agentsCatalog"] = public_catalog()
    snapshot["aiStatus"] = ai_status(st)
    # Keep the iframe payload bounded. Full signed history remains on Drive.
    snapshot["agentRuns"] = snapshot.get("agentRuns", [])[:18]
    snapshot["handoffs"] = snapshot.get("handoffs", [])[:100]
    if (st.session_state.get("xd_doc_inventory_requested")
            and st.session_state.get("xd_current_sheet") == "documents"
            and selected):
        from drive_storage.document_control import inventory
        verified = inventory(workspace, actor, selected, snapshot["documents"])
        # Keep the private iframe small; the native management dialog still
        # has the complete audited Drive inventory and full CSV export.
        public_keys = (
            "id", "code", "filename", "category", "revision", "status",
            "actor", "sizeBytes", "createdTime", "modifiedTime",
            "registeredAt", "description", "registered", "missing",
            "latest", "integrityWarning",
        )
        max_inline = 500
        snapshot["fileInventory"] = [
            {k: row[k] for k in public_keys} for row in verified["items"][:max_inline]
        ]
        snapshot["fileCounts"] = {
            **verified["counts"],
            "displayed": len(snapshot["fileInventory"]),
            "truncated": len(verified["items"]) > max_inline,
        }
    else:
        snapshot["fileInventory"] = None
        snapshot["fileCounts"] = {}
    return snapshot


def handle_workspace_action(st, action: dict):
    """Do not trust role, email or document data from the JS iframe."""
    section, op = action.get("section"), action.get("op")
    if section not in COMMANDS or op not in COMMANDS[section]:
        raise PermissionError("Thao tác không được phép")
    request_id = str(action.get("actionId") or "")
    if not re.fullmatch(r"[0-9a-f]{32}", request_id):
        raise ValueError("Mã giao dịch không hợp lệ")
    if st.session_state.get("xd_last_workspace_request") == request_id:
        return
    actor = identity_for(st)
    if not actor:
        raise PermissionError("Phiên đăng nhập không hợp lệ")
    st.session_state.xd_current_sheet = section
    if op in {"refresh", "document_inventory"}:
        if section == "monitor":
            from drive_storage.monitoring import ALL_DEPARTMENTS
            project = str(action.get("monitorProject") or "all")
            system = str(action.get("monitorSystem") or "all")
            period = str(action.get("monitorPeriod") or "today")
            department = str(action.get("monitorDepartment") or "all")
            # Never treat browser filter arguments as authorization. The
            # server snapshot and packet already filter by verified projects.
            st.session_state.xd_monitor_preferences = {
                "project": project if len(project) <= 160 else "all",
                "system": system if system in {"all", "mep", "xd", "cross"} else "all",
                "period": period if period in {"hour", "today", "week"} else "today",
                "department": department if department in ALL_DEPARTMENTS else "all",
            }
        if section == "documents":
            st.session_state.xd_doc_inventory_requested = True
        st.session_state.xd_last_workspace_request = request_id
        return
    current = load_snapshot(st)
    pid = str(action.get("projectId") or "")
    if op == "select":
        if pid not in {p["id"] for p in current["projects"]}:
            raise PermissionError("Dự án không thuộc phạm vi")
        st.session_state.xd_selected_cloud_project = pid
        st.session_state.xd_last_workspace_request = request_id
        return
    if op in {"project_create", "project_import"} and not can_admin(actor):
        raise PermissionError("Chỉ Admin được tạo dự án")
    if op in {"task_create", "task_assign", "task_withdraw", "task_start", "task_submit"} and not can_upload(actor):
        raise PermissionError("Tài khoản Chỉ đọc không được cập nhật công việc")
    if op in {"agent_run", "handoff_create", "handoff_resolve"} and not can_upload(actor):
        raise PermissionError("Chỉ đọc không được chạy Agent hoặc gửi phối hợp")
    if op == "ops_audit" and not can_admin(actor):
        raise PermissionError("Chỉ Admin được kiểm soát và sao lưu hệ thống")
    if op == "task_review" and not can_admin(actor):
        raise PermissionError("Chỉ Admin có quyền duyệt")
    if op not in {"project_create", "project_import", "ops_audit"} and pid not in {p["id"] for p in current["projects"]}:
        raise PermissionError("Dự án không thuộc phạm vi")
    task_id = str(action.get("taskId") or "")
    if op in {"task_assign", "task_withdraw", "task_start", "task_submit", "task_review", "agent_run"}:
        if not any(t["id"] == task_id and t["projectId"] == pid
                   for t in current["tasks"]):
            raise PermissionError("Nhiệm vụ không thuộc dự án")
    if op == "agent_run":
        from drive_storage.company_agents import agents
        profile = agents().get(str(action.get("agentId") or ""))
        task = next((t for t in current["tasks"]
                     if t["id"] == task_id and t["projectId"] == pid), None)
        if not profile or not task or (profile["department"] != task["dept"]
              and profile["id"] not in {"PM", "CEO", "DOC", "QAC"}):
            raise PermissionError("Agent không phù hợp với công việc hoặc bộ môn")
    if op == "handoff_resolve":
        handoff_id = str(action.get("handoffId") or "")
        if not any(h["id"] == handoff_id and h["projectId"] == pid
                   and h["status"] == "open" for h in current.get("handoffs", [])):
            raise PermissionError("Không có yêu cầu phối hợp đang mở")
    if op == "task_start":
        service_for(st).start_task(actor, project_id=pid, task_id=task_id,
                                   event_id=request_id)
        st.session_state.xd_last_workspace_request = request_id
        st.session_state.xd_workspace_feedback = "Đã bắt đầu công việc, dữ liệu đã lưu lên Drive."
        return
    if op == "document_manage":
        from drive_storage.document_control import inventory
        wanted = str(action.get("fileId") or "")
        files = current.get("fileInventory")
        if files is None:
            files = inventory(service_for(st), actor, pid)["items"]
        if wanted and not any(row["id"] == wanted for row in files):
            raise PermissionError("Tệp không nằm trong kho dự án được cấp quyền")
        st.session_state.xd_doc_inventory_requested = True
    if op not in INTERACTIVE:
        raise PermissionError("Lệnh không được phép")
    st.session_state.xd_workspace_dialog = {
        "op": op, "section": section, "projectId": pid,
        "taskId": task_id, "actionId": request_id,
        "fileId": str(action.get("fileId") or "")[:160],
        "agentId": str(action.get("agentId") or "")[:20],
        "handoffId": str(action.get("handoffId") or "")[:160],
    }
    st.session_state.xd_last_workspace_request = request_id


def workspace_dialog(st):
    action = st.session_state.get("xd_workspace_dialog")
    if not isinstance(action, dict) or action.get("op") not in INTERACTIVE:
        return
    if action.get("op") in {"agent_run", "handoff_create", "handoff_resolve", "ops_audit"}:
        from drive_storage.company_ui import company_dialog
        company_dialog(st, action)
        return
    if action.get("op") == "document_manage":
        from drive_storage.document_control_ui import document_control_dialog
        document_control_dialog(st, action)
        return
    titles = {
        "project_create": "V5.9 · Tạo dự án trên máy chủ",
        "project_import": "V5.9 · Nhập dữ liệu từ bản sao cục bộ",
        "task_create": "V5.9 · Giao công việc",
        "task_assign": "V6.7.6 · Gán người phụ trách và Agent",
        "task_withdraw": "Thu hồi / Hủy giao việc",
        "task_submit": "V6.0 · Trình báo cáo phê duyệt",
        "task_review": "V6.0 · Quyết định phê duyệt",
    }

    @st.dialog(titles[action["op"]], width="large",
               on_dismiss=lambda: st.session_state.pop("xd_workspace_dialog", None))
    def render():
        actor = identity_for(st)
        if not actor:
            st.error("Phiên đăng nhập không hợp lệ")
            return
        op = action["op"]
        if op in {"project_create", "project_import", "task_review"} and not can_admin(actor):
            st.error("Không có quyền quản trị/phê duyệt")
            return
        if op in {"task_create", "task_assign", "task_withdraw", "task_submit"} and not can_upload(actor):
            st.error("Không có quyền cập nhật")
            return
        if st.button("Đóng", key="xd_workspace_dialog_close"):
            st.session_state.xd_workspace_dialog = None
            st.rerun()

        try:
            current = load_snapshot(st)
            server = service_for(st)
            pid = action["projectId"]
            project = next((p for p in current["projects"] if p["id"] == pid), None)
            if op not in {"project_create", "project_import"} and not project:
                st.error("Dự án đã bị thu hồi quyền hoặc không tồn tại")
                return
            task = next((t for t in current["tasks"] if t["id"] == action["taskId"]
                         and t["projectId"] == pid), None)
            if op in {"task_assign", "task_withdraw", "task_submit", "task_review"} and not task:
                st.error("Nhiệm vụ không tồn tại")
                return
        except Exception:
            st.error("Không đọc được dữ liệu dùng chung. Thử lại sau khi kiểm tra Drive.")
            return

        if op == "project_create":
            with st.form("cloud_project_create"):
                code = st.text_input("Mã dự án", placeholder="DA001", max_chars=50)
                name = st.text_input("Tên dự án", max_chars=80)
                client = st.text_input("Chủ đầu tư", max_chars=160)
                location = st.text_input("Địa điểm", max_chars=160)
                division = st.selectbox("Phạm vi", ["all", "mep", "construction"],
                    format_func=lambda x: {"all": "Toàn công ty", "mep": "MEP",
                                           "construction": "Xây dựng"}[x])
                submitted = st.form_submit_button("Tạo dự án & thư mục Drive", type="primary")
            if submitted:
                try:
                    project_id = server.create_project(
                        actor, code=code, name=name, client=client, location=location,
                        division=division, event_id=action["actionId"],
                    )
                    st.session_state.xd_selected_cloud_project = project_id
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = "Đã tạo dự án và liên kết thư mục Google Drive."
                    st.rerun()
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không thể tạo dự án. Kiểm tra dữ liệu, mã trùng và quyền Drive.")

        elif op == "project_import":
            st.info(
                "Chỉ Admin được nhập metadata dự án/công việc cũ. Không xóa dữ liệu "
                "trên thiết bị hoặc tệp IndexedDB. Lịch sử duyệt cũ được giữ làm "
                "thông tin tham khảo, không chuyển thành quyết định xác thực."
            )
            with st.form("v59_legacy_import"):
                upload = st.file_uploader(
                    "Tệp JSON từ nút Sao lưu dữ liệu cũ",
                    type=["json"], max_upload_size=2,
                )
                confirmed = st.checkbox(
                    "Tôi đã kiểm tra bản sao và đồng ý nhập vào dữ liệu dùng chung"
                )
                submitted = st.form_submit_button(
                    "Nhập dữ liệu cũ", type="primary",

                )
            if submitted:
                try:
                    if not confirmed:
                        raise PermissionError("Cần xác nhận trước khi nhập dữ liệu")
                    if upload is None or not 0 < upload.size <= 1_000_000:
                        raise ValueError("Tệp JSON phải nhỏ hơn 1 MB")
                    raw = json.loads(upload.getvalue().decode("utf8"))
                    result = server.import_legacy_workspace(actor, raw)
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = (
                        f"Đã liên kết {result['projects']} dự án, "
                        f"nhập mới {result['newTasks']} công việc. "
                        "Bản sao cũ vẫn được giữ."
                    )
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error(
                        "Nhập chưa hoàn tất. Dữ liệu đã lưu vẫn còn trên Drive; "
                        "có thể nhập lại mà không tạo công việc trùng."
                    )

        elif op == "task_create":
            from drive_storage.company_agents import agents
            catalog = agents()
            with st.form("cloud_task_create"):
                st.caption("Dự án: " + project["code"] + " · " + project["name"])
                title = st.text_input("Tên công việc", max_chars=240)
                dept = st.selectbox("Bộ môn", sorted(DEPARTMENTS),
                                    format_func=lambda x: DEPARTMENT_NAMES.get(x, x))
                assignee = st.text_input("Người phụ trách (tên hoặc email)", max_chars=160)
                agent_id = st.selectbox(
                    "Agent được giao (tùy chọn; phải đúng bộ môn)",
                    ["", *catalog], format_func=lambda aid: "— Chưa giao Agent —"
                    if not aid else catalog[aid]["title"] + " · " + aid,
                )
                doc_code = st.text_input("Mã hồ sơ liên quan", max_chars=80)
                priority = st.selectbox("Mức độ ưu tiên", ["normal", "low", "high", "critical"],
                                        format_func=lambda p: {"normal": "Bình thường", "low": "Thấp",
                                                               "high": "Cao", "critical": "Khẩn cấp"}[p])
                deadline = st.date_input("Hạn hoàn thành", value=None, format="DD/MM/YYYY")
                submitted = st.form_submit_button("Giao công việc", type="primary")
            if submitted:
                try:
                    server.create_task(
                        actor, project_id=pid, title=title, dept=dept,
                        assignee=assignee, agent_id=agent_id, doc_code=doc_code,
                        priority=priority,
                        due_date=deadline.isoformat() if deadline else "",
                        event_id=action["actionId"],
                    )
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = "Đã tạo nhiệm vụ và lưu phân công. Agent chưa chạy cho đến khi bấm Chạy Agent."
                    st.rerun()
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không tạo được công việc. Kiểm tra kết nối Drive.")

        elif op == "task_assign":
            from drive_storage.company_agents import agents
            catalog = agents()
            candidates = [aid for aid, profile in catalog.items()
                          if profile["department"] == task["dept"] or
                          aid in {"CEO", "PM", "DOC", "QAC"}]
            with st.form("v676_task_assignment"):
                st.markdown("**" + task["code"] + " · " + task["title"] + "**")
                st.caption("Giao nhiệm vụ không tự chạy AI. Sau khi lưu, chọn Chạy Agent ngay trên thẻ công việc.")
                assignee = st.text_input(
                    "Kỹ sư/người phụ trách",
                    value=str(task.get("assignee") or ""), max_chars=160
                )
                old_agent = str(task.get("assignedAgentId") or "")
                options = ["", *candidates]
                agent_id = st.selectbox(
                    "Chuyên gia AI được giao",
                    options, index=options.index(old_agent) if old_agent in options else 0,
                    format_func=lambda aid: "— Chưa gán Agent —" if not aid
                    else catalog[aid]["title"] + " (" + aid + ")",
                )
                submitted = st.form_submit_button("Lưu phân công", type="primary")
            if submitted:
                try:
                    server.assign_task(
                        actor, project_id=pid, task_id=task_id,
                        assignee=assignee, agent_id=agent_id,
                        event_id=action["actionId"],
                    )
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = (
                        "Đã lưu người phụ trách và Agent vào dữ liệu dùng chung. "
                        "Để xử lý, bấm Chạy Agent trên thẻ công việc."
                    )
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không lưu được phân công. Dữ liệu cũ vẫn giữ nguyên.")

        elif op == "task_withdraw":
            st.markdown("**" + task["code"] + " · " + task["title"] + "**")
            st.caption("Mọi thao tác được ghi nhật ký có chữ ký; không xóa báo cáo "
                       "Agent, hồ sơ hay lịch sử đã có.")
            eligible = task["status"] in {"todo", "working"}
            cancellable = task["status"] in {"todo", "working", "review"}
            assigned = bool(task.get("assignee") or task.get("assignedAgentId"))
            choices = []
            if eligible and assigned:
                choices.append("withdraw")
            if can_admin(actor) and cancellable:
                choices.append("cancel")
            if not choices:
                st.warning("Không có thao tác thu hồi/hủy được phép cho nhiệm vụ này.")
                return
            with st.form("v677_task_withdraw"):
                choice = st.radio(
                    "Hình thức xử lý", choices, horizontal=False,
                    format_func=lambda value: (
                        "Thu hồi phân công — bỏ người phụ trách và Agent, đưa về Chờ xử lý"
                        if value == "withdraw" else
                        "Hủy công việc — chuyển sang Đã hủy, không thể giao/chạy lại"),
                )
                reason = st.text_area(
                    "Lý do (bắt buộc, ít nhất 5 ký tự)", max_chars=600,
                    placeholder="Ví dụ: điều chỉnh kế hoạch hoặc thay đổi phạm vi nhiệm vụ",
                )
                confirmed = st.checkbox(
                    "Tôi xác nhận thao tác trên đúng công việc; giữ nguyên lịch sử và hồ sơ."
                )
                submitted = st.form_submit_button(
                    "Xác nhận thu hồi / hủy giao việc", type="primary",
                )
            if submitted:
                try:
                    if not confirmed:
                        raise PermissionError("Cần xác nhận trước khi thu hồi/hủy")
                    if choice == "withdraw":
                        server.withdraw_task(
                            actor, project_id=pid, task_id=task["id"],
                            reason=reason, event_id=action["actionId"],
                        )
                        feedback = "Đã thu hồi phân công. Công việc trở lại Chờ xử lý."
                    elif choice == "cancel":
                        server.cancel_task(
                            actor, project_id=pid, task_id=task["id"],
                            reason=reason, event_id=action["actionId"],
                        )
                        feedback = "Đã hủy công việc; toàn bộ lịch sử và hồ sơ được giữ nguyên."
                    else:
                        raise ValueError("Hình thức xử lý không hợp lệ")
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = feedback
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không thu hồi/hủy được công việc; dữ liệu gốc vẫn giữ nguyên.")

        elif op == "task_submit":
            st.markdown("**Công việc:** " + task["title"])
            with st.form("cloud_task_submit"):
                summary = st.text_area("Báo cáo kết quả", max_chars=4000, height=180)
                findings = st.text_area("Phát hiện / kiến nghị", max_chars=2000, height=120)
                submitted = st.form_submit_button("Gửi trình phê duyệt", type="primary")
            if submitted:
                try:
                    server.submit_task(actor, project_id=pid, task_id=task["id"],
                                       summary=summary, findings=findings,
                                       event_id=action["actionId"])
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = "Đã trình báo cáo, chờ Admin phê duyệt."
                    st.rerun()
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không gửi được báo cáo.")

        elif op == "task_review":
            st.markdown("**Công việc:** " + task["title"])
            st.write("Báo cáo: " + task.get("report", ""))
            st.write("Phát hiện: " + task.get("findings", ""))
            with st.form("cloud_task_review"):
                decision = st.radio("Kết quả kiểm tra",
                                    ["approve", "reject"], horizontal=True,
                                    format_func=lambda x: "Phê duyệt" if x == "approve" else "Trả lại")
                comment = st.text_area("Nhận xét / lý do trả lại", max_chars=2000)
                confirmed = st.checkbox("Tôi xác nhận quyết định bằng tài khoản Admin hiện tại")
                submitted = st.form_submit_button("Lưu quyết định", type="primary",
)
            if submitted:
                try:
                    if not confirmed:
                        raise PermissionError("Cần xác nhận quyết định phê duyệt")
                    server.review_task(actor, project_id=pid, task_id=task["id"],
                                       decision=decision, comment=comment,
                                       event_id=action["actionId"])
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = "Đã lưu quyết định và nhật ký người duyệt."
                    st.rerun()
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không lưu được quyết định.")
    render()
