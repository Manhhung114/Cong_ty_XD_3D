"""Authenticated native dialogs for V5.9/V6.0 shared project management.

These are launched by controls *inside* the existing 3D project/task/review
sheets, not by separate navigation or an unauthenticated API endpoint.
"""
from __future__ import annotations

import re
from datetime import date

from drive_storage.access_control import identity_for, can_admin, can_upload, allows_project
from drive_storage.manager import from_streamlit_secrets
from drive_storage.shared_workspace import SharedWorkspace, DEPARTMENTS

COMMANDS = {
    "projects": {"refresh", "select", "project_create"},
    "tasks": {"refresh", "select", "task_create", "task_start", "task_submit"},
    "reviews": {"refresh", "select", "task_review"},
    "documents": {"refresh", "select"},
    "activity": {"refresh", "select"},
}
DEPARTMENT_NAMES = {
    "director": "Ban giám đốc", "electrical": "Điện", "hvac": "HVAC",
    "plumbing": "Cấp thoát nước", "fire": "PCCC", "bim": "BIM MEP",
    "qs": "BOQ MEP", "qa": "QA/QC MEP", "architecture": "Kiến trúc",
    "structure": "Kết cấu", "xd_bim": "BIM Xây dựng", "xd_qs": "BOQ Xây dựng",
    "xd_planning": "Kế hoạch", "xd_site": "Hiện trường",
    "xd_safety": "An toàn XD", "xd_material": "Vật tư",
}
INTERACTIVE = {"project_create", "task_create", "task_submit", "task_review"}


def service_for(st):
    """Credentials never leave the Streamlit server."""
    drive = dict(st.secrets.get("drive", {}))
    key = str(st.secrets.get("auth", {}).get("cookie_secret", ""))
    return SharedWorkspace(from_streamlit_secrets(drive), key)


def load_snapshot(st) -> dict:
    actor = identity_for(st)
    if not actor:
        raise PermissionError("Phiên đăng nhập không còn quyền truy cập")
    snapshot = service_for(st).snapshot(actor)
    requested = str(st.session_state.get("xd_selected_cloud_project", ""))
    valid = {p["id"] for p in snapshot["projects"]}
    selected = requested if requested in valid else (snapshot["projects"][0]["id"] if snapshot["projects"] else "")
    st.session_state.xd_selected_cloud_project = selected
    snapshot.update({"enabled": True, "selectedProjectId": selected})
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
    if op == "refresh":
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
    if op == "project_create" and not can_admin(actor):
        raise PermissionError("Chỉ Admin được tạo dự án")
    if op in {"task_create", "task_start", "task_submit"} and not can_upload(actor):
        raise PermissionError("Tài khoản Chỉ đọc không được cập nhật công việc")
    if op == "task_review" and not can_admin(actor):
        raise PermissionError("Chỉ Admin có quyền duyệt")
    if op != "project_create" and pid not in {p["id"] for p in current["projects"]}:
        raise PermissionError("Dự án không thuộc phạm vi")
    task_id = str(action.get("taskId") or "")
    if op in {"task_start", "task_submit", "task_review"}:
        if not any(t["id"] == task_id and t["projectId"] == pid
                   for t in current["tasks"]):
            raise PermissionError("Nhiệm vụ không thuộc dự án")
    if op == "task_start":
        service_for(st).start_task(actor, project_id=pid, task_id=task_id,
                                   event_id=request_id)
        st.session_state.xd_last_workspace_request = request_id
        st.session_state.xd_workspace_feedback = "Đã bắt đầu công việc, dữ liệu đã lưu lên Drive."
        return
    if op not in INTERACTIVE:
        raise PermissionError("Lệnh không được phép")
    st.session_state.xd_workspace_dialog = {
        "op": op, "section": section, "projectId": pid,
        "taskId": task_id, "actionId": request_id,
    }
    st.session_state.xd_last_workspace_request = request_id


def workspace_dialog(st):
    action = st.session_state.get("xd_workspace_dialog")
    if not isinstance(action, dict) or action.get("op") not in INTERACTIVE:
        return
    titles = {
        "project_create": "V5.9 · Tạo dự án trên máy chủ",
        "task_create": "V5.9 · Giao công việc",
        "task_submit": "V6.0 · Trình báo cáo phê duyệt",
        "task_review": "V6.0 · Quyết định phê duyệt",
    }

    @st.dialog(titles[action["op"]], width="large")
    def render():
        actor = identity_for(st)
        if not actor:
            st.error("Phiên đăng nhập không hợp lệ")
            return
        op = action["op"]
        if op in {"project_create", "task_review"} and not can_admin(actor):
            st.error("Không có quyền quản trị/phê duyệt")
            return
        if op in {"task_create", "task_submit"} and not can_upload(actor):
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
            if op != "project_create" and not project:
                st.error("Dự án đã bị thu hồi quyền hoặc không tồn tại")
                return
            task = next((t for t in current["tasks"] if t["id"] == action["taskId"]
                         and t["projectId"] == pid), None)
            if op in {"task_submit", "task_review"} and not task:
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

        elif op == "task_create":
            with st.form("cloud_task_create"):
                st.caption("Dự án: " + project["code"] + " · " + project["name"])
                title = st.text_input("Tên công việc", max_chars=240)
                dept = st.selectbox("Bộ môn", sorted(DEPARTMENTS),
                                    format_func=lambda x: DEPARTMENT_NAMES.get(x, x))
                assignee = st.text_input("Người phụ trách (tên hoặc email)", max_chars=160)
                doc_code = st.text_input("Mã hồ sơ liên quan", max_chars=80)
                deadline = st.date_input("Hạn hoàn thành", value=None, format="DD/MM/YYYY")
                submitted = st.form_submit_button("Giao công việc", type="primary")
            if submitted:
                try:
                    server.create_task(
                        actor, project_id=pid, title=title, dept=dept,
                        assignee=assignee, doc_code=doc_code,
                        due_date=deadline.isoformat() if deadline else "",
                        event_id=action["actionId"],
                    )
                    st.session_state.xd_workspace_dialog = None
                    st.session_state.xd_workspace_feedback = "Đã giao công việc lên dữ liệu tập trung."
                    st.rerun()
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không tạo được công việc. Kiểm tra kết nối Drive.")

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
                                                  disabled=not confirmed)
            if submitted:
                try:
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
