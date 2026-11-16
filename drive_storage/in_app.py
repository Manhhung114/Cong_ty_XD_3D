"""Authenticated in-app Google Drive actions for the XD & MEP Streamlit portal.

The UI is invoked by buttons inside the corresponding 3D application sheets;
all Drive operations are verified again on the server. Google OAuth credentials
never reach the browser component.
"""
from __future__ import annotations
import re
import secrets
from pathlib import PurePath

from drive_storage.manager import ALLOWED_EXTENSIONS, FOLDER_CATEGORIES, MAX_FILE_SIZE, from_streamlit_secrets
from drive_storage.document_control import base_code
from drive_storage.access_control import (
    ROLE_NAMES, identity_for, read_policy,
    legacy_policy, write_policy, set_user, revoke_user, clean_email,
    allows_project, can_upload, can_admin,
)

SECTIONS = {
    "documents": tuple(FOLDER_CATEGORIES),
    "boq": ("boq_mep", "boq_xd"),
    "bim": ("bim_mep", "bim_xd"),
    "tasks": ("tasks", "reports_mep", "reports_xd", "reports_management"),
    "reviews": ("approvals", "reports_mep", "reports_xd", "reports_management"),
    "projects": ("info", "contracts", "legal", "schedule", "photos", "audit"),
}
LABELS = {
    "documents": "Kho tài liệu", "boq": "BOQ / Dự toán",
    "bim": "BIM / Mô hình", "tasks": "Công việc",
    "reviews": "Chờ phê duyệt", "projects": "Quản lý dự án",
}
DOWNLOAD_BUFFER_LIMIT = 40 * 1024 * 1024


def access_role(st) -> str | None:
    """Return verified server-side role; not a user-controlled iframe value."""
    identity = identity_for(st)
    return identity["role"] if identity else None


def require_login(st) -> str:
    """Fail closed before ever rendering the 3D UI or registering the Drive bridge."""
    try:
        auth = st.secrets.get("auth", {})
        admin = st.secrets.get("drive", {}).get("allowed_email", "")
    except Exception:
        auth, admin = {}, ""
    if not auth or not admin:
        st.error("Chưa thiết lập đăng nhập quản trị. Kiểm tra [auth] và [drive].allowed_email trong Streamlit Secrets.")
        st.stop()
    if not getattr(st.user, "is_logged_in", False):
        st.title("Công ty Xây dựng & MEP AI 3D")
        st.info("Đăng nhập bằng Google để truy cập công ty và hồ sơ dự án.")
        if st.button("Đăng nhập với Google", type="primary"):
            st.login()
        st.stop()
    role = access_role(st)
    if role is None:
        st.error("Tài khoản chưa được cấp quyền truy cập ứng dụng hoặc email Google chưa được xác minh.")
        st.button("Đăng xuất", on_click=st.logout)
        st.stop()
    return role


def mount_bridge(st) -> dict | None:
    """Small Streamlit v2 bridge. Messages only request the opening of a dialog."""
    if "drive_bridge_nonce" not in st.session_state:
        st.session_state.drive_bridge_nonce = secrets.token_urlsafe(32)
    bridge = st.components.v2.component(
        name="xd_mep_drive_actions_v1",
        html="<span hidden aria-hidden='true'></span>",
        js="""export default function(component) {
          const {data, setTriggerValue} = component;
          const allowed = new Set(["documents","boq","bim","tasks","reviews","projects"]);
          function onMessage(event) {
            const d = event.data;
            if (!d || d.channel !== "XD_MEP_DRIVE_V1" || d.nonce !== data.nonce) return;
            const userGrant = d.kind === "access" && d.section === "settings";
            const driveAction = ["upload","browse"].includes(d.kind) && allowed.has(d.section);
            const workSections = new Set(["projects","tasks","reviews","documents","activity"]);
            const workspaceAction = d.kind === "workspace" && workSections.has(d.section);
            if (!userGrant && !driveAction && !workspaceAction) return;
            if (event.source === window) return;
            // The iframe's origin can be "null" for srcdoc on some browsers.
            if (event.origin !== window.location.origin && event.origin !== "null") return;
            setTriggerValue("action", {
              kind: d.kind, section: d.section,
              projectCode: String(d.projectCode || "").slice(0, 50),
              op: workspaceAction ? String(d.op || "").slice(0, 32) : "",
              projectId: workspaceAction ? String(d.projectId || "").slice(0, 160) : "",
              taskId: workspaceAction ? String(d.taskId || "").slice(0, 160) : "",
              fileId: workspaceAction ? String(d.fileId || "").slice(0, 160) : "",
              actionId: workspaceAction ? String(d.actionId || "").slice(0, 32) : ""
            });
          }
          window.addEventListener("message", onMessage);
          return () => window.removeEventListener("message", onMessage);
        }""",
    )
    result = bridge(
        key="xd_mep_drive_actions_bridge",
        data={"nonce": st.session_state.drive_bridge_nonce},
        on_action_change=lambda: None,
    )
    action = getattr(result, "action", None)
    if not isinstance(action, dict):
        return None
    if action.get("kind") == "workspace":
        from drive_storage.workspace_ui import COMMANDS
        section, op = action.get("section"), action.get("op")
        if section not in COMMANDS or op not in COMMANDS[section]:
            return None
        return {
            "kind": "workspace", "section": section, "op": op,
            "projectId": str(action.get("projectId") or "")[:160],
            "taskId": str(action.get("taskId") or "")[:160],
            "fileId": str(action.get("fileId") or "")[:160],
            "actionId": str(action.get("actionId") or "")[:32],
        }
    if action.get("section") == "settings" and action.get("kind") == "access":
        if not can_admin(identity_for(st)):
            return None
    elif action.get("section") not in SECTIONS or action.get("kind") not in {"upload", "browse"}:
        return None
    return {
        "section": action["section"],
        "kind": action["kind"],
        "projectCode": re.sub(r"[^A-Z0-9_-]", "", str(action.get("projectCode", "")).upper())[:50],
    }


def drive_dialog(st) -> None:
    """Open the native Streamlit upload/download dialog above the current sheet."""
    action = st.session_state.get("drive_in_app_action")
    if not isinstance(action, dict) or action.get("section") not in SECTIONS:
        return

    @st.dialog("Google Drive · " + LABELS[action["section"]], width="large")
    def render() -> None:
        # A dialog invocation is not an authorization. Check again each rerun.
        identity = identity_for(st)
        if not identity:
            st.error("Phiên đăng nhập không còn hợp lệ.")
            return
        if action["kind"] == "upload" and not can_upload(identity):
            st.error("Tài khoản chỉ có quyền xem. Không được tải tệp lên.")
            return
        if st.button("Đóng", key="drive_dialog_close"):
            st.session_state.drive_in_app_action = None
            st.rerun()

        try:
            storage = from_streamlit_secrets(dict(st.secrets.get("drive", {})))
            projects = [p for p in storage.list_projects() if allows_project(identity, p["id"])]
        except Exception:
            st.error("Không kết nối được Google Drive. Kiểm tra quyền và cấu hình OAuth.")
            return
        if not projects:
            st.info("Không có dự án được cấp quyền hoặc chưa có dự án trên Drive.")
            return

        codes = {p["id"]: p["name"].split("_", 1)[0].upper() for p in projects}
        hint = str(action.get("projectCode") or "")
        initial = next((i for i, p in enumerate(projects) if codes[p["id"]] == hint), 0)
        project = st.selectbox(
            "Dự án", projects,
            index=initial,
            format_func=lambda p: p["name"],
            key="drive_sheet_project_" + action["section"],
        )
        options = SECTIONS[action["section"]]
        category = st.selectbox(
            "Mục lưu trữ", options,
            format_func=lambda c: " / ".join(FOLDER_CATEGORIES[c]),
            key="drive_sheet_category_" + action["section"],
        )
        try:
            files = storage.list_category_files(project_id=project["id"], category=category)
        except Exception:
            st.error("Không đọc được thư mục hồ sơ trong dự án đã chọn.")
            return

        st.markdown(f"**Hồ sơ trên Drive ({len(files)})**")
        if files:
            for f in files[:100]:
                title = str(f.get("name", "Tệp không tên"))
                size = int(f.get("size") or 0)
                with st.container(border=True):
                    st.write(f"**{title}** · {size / 1048576:.1f} MB")
                    if f.get("webViewLink"):
                        st.link_button("Mở trên Google Drive", f["webViewLink"])
                    # Native downloads work for users who have Streamlit access
                    # even when they don't have direct Google Drive share access.
                    if size <= DOWNLOAD_BUFFER_LIMIT and size > 0:
                        key = "dload_" + f["id"]
                        if st.button("Chuẩn bị tải xuống", key="prepare_" + key):
                            try:
                                st.session_state[key] = storage.download_small_file(
                                    project_id=project["id"], category=category, file_id=f["id"]
                                )
                            except Exception:
                                st.error("Không tải được tệp. Kiểm tra quyền và đường dẫn.")
                        if key in st.session_state:
                            st.download_button(
                                "⬇ Tải xuống", data=st.session_state[key],
                                file_name=title, key="download_widget_" + f["id"],
                            )
                    elif size > DOWNLOAD_BUFFER_LIMIT:
                        st.caption("Tệp lớn: tải trực tiếp tại Google Drive, cần có quyền với thư mục.")
        else:
            st.caption("Chưa có hồ sơ trong mục này.")
        # V6.0: register *existing* files in the server-side document register.
        # A document can only be attached to tasks in the same verified project.
        if files and can_upload(identity):
            with st.expander("📒 Ghi hồ sơ hiện có vào sổ V6.0", expanded=False):
                from drive_storage.workspace_ui import service_for
                from drive_storage.shared_workspace import SharedWorkspace
                selected = st.selectbox(
                    "Tệp Drive", files[:100],
                    format_func=lambda item: str(item.get("name", "")),
                    key="v60_index_file_" + action["section"] + project["id"] + category,
                )
                doc_code = st.text_input(
                    "Mã hồ sơ", value=base_code(selected["name"]),
                    key="v60_index_code_" + selected["id"],
                )
                note = st.text_input(
                    "Mô tả / lần thay đổi", max_chars=600,
                    key="v60_index_note_" + selected["id"],
                )
                try:
                    shared = service_for(st).snapshot(identity)
                    task_choices = [t for t in shared["tasks"] if t["projectId"] == project["id"]]
                except Exception:
                    st.error("Không lấy được danh sách công việc đã phân quyền.")
                    return
                selected_task = st.selectbox(
                    "Gắn với công việc (tùy chọn)",
                    [None] + task_choices,
                    format_func=lambda t: "— Không gắn công việc —" if t is None else
                    t["code"] + " · " + t["title"],
                    key="v60_index_task_" + selected["id"],
                )
                if st.button("Ghi vào sổ hồ sơ", key="v60_register_" + selected["id"]):
                    try:
                        service_for(st).register_document(
                            identity, project_id=project["id"], category=category,
                            file_id=selected["id"], code=doc_code, description=note,
                            task_id=selected_task["id"] if selected_task else "",
                        )
                        st.success("Đã ghi vào sổ hồ sơ dùng chung.")
                    except (ValueError, PermissionError) as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Không ghi được vào sổ; tệp gốc vẫn nguyên vẹn trên Drive.")

        if action["kind"] == "browse":
            return

        st.divider()
        st.markdown("**Tải tệp lên đúng dự án**")
        upload = st.file_uploader(
            "Chọn tệp, tối đa 500 MB/tệp",
            type=sorted(ext.lstrip(".") for ext in ALLOWED_EXTENSIONS),
            max_upload_size=500,
            accept_multiple_files=False,
            key="upload_" + action["section"] + "_" + project["id"] + "_" + category,
        )
        if upload is not None:
            st.caption(f"{upload.name} · {upload.size / 1048576:.1f} MB")
        upload_code = st.text_input("Mã hồ sơ V6.0", key="v60_upload_code_" + action["section"] + project["id"] + category, max_chars=80)
        upload_note = st.text_input("Mô tả phiên bản", key="v60_upload_note_" + action["section"] + project["id"] + category, max_chars=600)
        try:
            from drive_storage.workspace_ui import service_for
            current_tasks = [t for t in service_for(st).snapshot(identity)["tasks"] if t["projectId"] == project["id"]]
        except Exception:
            current_tasks = []
        upload_task = st.selectbox(
            "Đính kèm công việc (tùy chọn)",
            [None] + current_tasks, key="v60_upload_task_" + action["section"] + project["id"],
            format_func=lambda t: "— Không gắn công việc —" if t is None else t["code"] + " · " + t["title"],
        )
        if st.button("Lưu lên Google Drive", type="primary",
                     disabled=upload is None, key="drive_sheet_submit"):
            if upload is None or not 0 < upload.size <= MAX_FILE_SIZE:
                st.error("Chỉ nhận tệp tối đa 500 MB.")
                return
            bar = st.progress(0.0, text="Đang tải tệp lên Google Drive")
            try:
                result = storage.upload_stream_to_project(
                    project_id=project["id"],
                    category=category,
                    filename=upload.name,
                    stream=upload,
                    size=upload.size,
                    progress=lambda v: bar.progress(v, text=f"Đã tải {v:.0%}"),
                )
                st.success("Đã lưu trên Google Drive: " + result["name"])
                try:
                    service_for(st).register_document(
                        identity, project_id=project["id"], category=category,
                        file_id=result["id"], code=upload_code or base_code(result["name"]),
                        description=upload_note,
                        task_id=upload_task["id"] if upload_task else "",
                    )
                    st.success("Đã ghi mã hồ sơ và phiên bản vào sổ V6.0.")
                except Exception:
                    st.warning("Tệp đã lưu trên Drive nhưng chưa vào sổ V6.0. Mở 'Xem hồ sơ / Tải xuống' để ghi vào sổ.")
                if result.get("webViewLink"):
                    st.link_button("Mở tệp vừa lưu", result["webViewLink"])
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Không thể tải lên. Kiểm tra mạng, bộ nhớ máy chủ và quyền Drive.")
    render()

def access_management_dialog(st) -> None:
    """Admin-only management UI launched from Settings, never from a public route."""
    action = st.session_state.get("drive_in_app_action")
    if not isinstance(action, dict) or action.get("section") != "settings" or action.get("kind") != "access":
        return

    @st.dialog("🔐 Cài đặt · Quản lý người dùng & phân quyền", width="large")
    def render() -> None:
        actor = identity_for(st)
        if not can_admin(actor):
            st.error("Chỉ Admin được quản lý tài khoản.")
            return
        if st.button("Đóng", key="access_close"):
            st.session_state.drive_in_app_action = None
            st.rerun()

        try:
            config = dict(st.secrets.get("drive", {}))
            owner = clean_email(config.get("allowed_email"))
            store = from_streamlit_secrets(config)
            signature_key = str(st.secrets.get("auth", {}).get("cookie_secret", ""))
            file_id, managed = read_policy(store, signature_key)
            policy = managed if managed is not None else legacy_policy(st.secrets.get("access", {}).get("members", []))
            projects = store.list_projects()
        except Exception:
            st.error("Không tải được danh sách quyền từ Google Drive. Không thay đổi dữ liệu.")
            return

        st.caption(
            "Phân quyền giống QLDA: Chỉ đọc = xem/tải hồ sơ; Cập nhật = xem và tải lên; "
            "Admin = quản lý người dùng. Đăng nhập vẫn bằng Google, không cần mật khẩu mới."
        )
        users = policy["users"]
        table = [{
            "Họ tên": "Chủ hệ thống", "Email": owner,
            "Quyền": "Admin (gốc)", "Dự án": "Tất cả",
            "Trạng thái": "Hoạt động",
        }]
        for email, row in sorted(users.items()):
            table.append({
                "Họ tên": row["name"], "Email": email,
                "Quyền": ROLE_NAMES[row["role"]],
                "Dự án": "Tất cả" if "*" in row["projects"] else f'{len(row["projects"])} dự án',
                "Trạng thái": "Hoạt động" if row["active"] else "Tạm khóa",
            })
        st.dataframe(table, hide_index=True, use_container_width=True)
        if managed is None:
            st.info("Đang dùng danh sách [access].members cũ. Lần lưu đầu tiên sẽ chuyển sang quản lý quyền trực tiếp trên Google Drive.")

        mode = st.radio(
            "Thao tác", ("Thêm người dùng mới", "Cập nhật người dùng"),
            horizontal=True, key="access_manage_mode"
        )
        selected_email = ""
        if mode == "Cập nhật người dùng" and users:
            selected_email = st.selectbox(
                "Người dùng", sorted(users), key="access_existing_email",
                format_func=lambda email: f'{users[email]["name"] or "Nhân viên"} · {email}'
            )
        selected = users.get(selected_email, {})
        role = selected.get("role", "update")
        scopes = selected.get("projects", ["*"])
        project_ids = [p["id"] for p in projects]
        project_names = {p["id"]: p["name"] for p in projects}

        with st.form("access_edit_form_" + (selected_email.replace("@", "_").replace(".", "_") or "new")):
            col_a, col_b = st.columns(2)
            email = col_a.text_input("Email Google", value=selected_email, disabled=bool(selected_email))
            name = col_b.text_input("Họ tên", value=selected.get("name", ""), max_chars=160)
            new_role = col_a.selectbox(
                "Quyền hệ thống", ("read", "update", "admin"),
                index=("read", "update", "admin").index(role),
                format_func=lambda x: ROLE_NAMES[x],
            )
            active = col_b.checkbox("Tài khoản đang hoạt động", value=selected.get("active", True))
            all_projects = st.checkbox("Được truy cập tất cả dự án", value=("*" in scopes))
            chosen = st.multiselect(
                "Chỉ các dự án được chọn (khi không chọn Tất cả)",
                project_ids,
                default=[p for p in scopes if p in project_ids],
                format_func=lambda p: project_names[p],
            )
            save = st.form_submit_button("💾 Lưu quyền người dùng", type="primary")

        if save:
            try:
                updated = set_user(
                    policy, email=email, name=name, role=new_role,
                    projects=["*"] if all_projects else chosen, active=active,
                    actor=actor["email"], owner=owner,
                )
                write_policy(store, updated, file_id, signature_key)
                st.success("Đã lưu phân quyền trên Google Drive. Tài khoản được áp dụng từ lần tải lại tiếp theo.")
                st.rerun()
            except (ValueError, PermissionError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("Không lưu được quyền. Kiểm tra kết nối Drive và thử lại.")

        removable = [email for email in sorted(users) if email != actor["email"] and email != owner]
        if removable:
            st.divider()
            with st.expander("🗑 Thu hồi quyền người dùng", expanded=False):
                target = st.selectbox("Chọn tài khoản cần thu hồi", removable, key="access_revoke_target")
                confirmed = st.checkbox("Tôi xác nhận thu hồi quyền đăng nhập của tài khoản này", key="access_revoke_confirm")
                if st.button("Thu hồi quyền", disabled=not confirmed, key="access_revoke_button"):
                    try:
                        updated = revoke_user(policy, email=target, actor=actor["email"], owner=owner)
                        write_policy(store, updated, file_id, signature_key)
                        st.success("Đã thu hồi quyền tài khoản.")
                        st.rerun()
                    except (ValueError, PermissionError) as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Không thu hồi được quyền. Kiểm tra kết nối Drive.")
        st.caption("Admin gốc không thể bị xóa. Lịch sử thao tác phân quyền được giữ trong cấu hình Drive.")

    render()
