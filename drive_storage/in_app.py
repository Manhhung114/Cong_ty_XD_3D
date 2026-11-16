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


def _verified_email(st) -> str:
    """Only accept a Google-verified identity, never a browser-provided email."""
    if not getattr(st.user, "is_logged_in", False):
        return ""
    verified = st.user.get("email_verified", False)
    if verified is not True:
        return ""
    return str(st.user.get("email", "")).strip().casefold()


def access_role(st) -> str | None:
    """Admin is exact allowlisted owner; additional employees must be allowlisted."""
    try:
        drive = st.secrets.get("drive", {})
        access = st.secrets.get("access", {})
        owner = str(drive.get("allowed_email", "")).strip().casefold()
        members = access.get("members", [])
        if not isinstance(members, (list, tuple)):
            members = []
    except Exception:
        return None
    email = _verified_email(st)
    if not email or not owner:
        return None
    if email == owner:
        return "admin"
    if email in {str(x).strip().casefold() for x in members}:
        return "member"
    return None


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
            if (!["upload","browse"].includes(d.kind) || !allowed.has(d.section)) return;
            if (event.source === window) return;
            // The iframe's origin can be "null" for srcdoc on some browsers.
            if (event.origin !== window.location.origin && event.origin !== "null") return;
            setTriggerValue("action", {
              kind: d.kind, section: d.section,
              projectCode: String(d.projectCode || "").slice(0, 50)
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
    if action.get("section") not in SECTIONS or action.get("kind") not in {"upload", "browse"}:
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
        if not access_role(st):
            st.error("Phiên đăng nhập không còn hợp lệ.")
            return
        if st.button("Đóng", key="drive_dialog_close"):
            st.session_state.drive_in_app_action = None
            st.rerun()

        try:
            storage = from_streamlit_secrets(dict(st.secrets.get("drive", {})))
            projects = storage.list_projects()
        except Exception:
            st.error("Không kết nối được Google Drive. Kiểm tra quyền và cấu hình OAuth.")
            return
        if not projects:
            st.info("Drive chưa có dự án. Admin tạo dự án trong Google Drive theo cấu trúc đã thiết lập.")
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
                if result.get("webViewLink"):
                    st.link_button("Mở tệp vừa lưu", result["webViewLink"])
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Không thể tải lên. Kiểm tra mạng, bộ nhớ máy chủ và quyền Drive.")
    render()
