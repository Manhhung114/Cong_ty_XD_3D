"""Visible, authenticated Streamlit uploader for a private Google Drive.

Authentication: Streamlit st.login (Google OIDC) + verified allowlisted email.
Authorization: Google Drive refresh token only in server-side Streamlit Secrets.
The public XD & MEP HTML iframe never receives the Drive credential.
"""
from __future__ import annotations

from .manager import FOLDER_CATEGORIES, from_streamlit_secrets

DOCS_URL = "https://github.com/Manhhung114/Cong_ty_XD_3D/blob/main/docs/GOOGLE_DRIVE_STORAGE.md"
REQUIRED_DRIVE_KEYS = ("allowed_email", "root_folder_id", "client_id", "client_secret", "refresh_token")


def _config(st):
    try:
        auth = dict(st.secrets.get("auth", {}))
        drive = dict(st.secrets.get("drive", {}))
    except Exception:
        return {}, {}
    return auth, drive


def display(st):
    """Render the uploader on the main page (not the hidden Streamlit sidebar)."""
    with st.expander("☁️ Google Drive · Kho hồ sơ dự án", expanded=False):
        auth, drive = _config(st)
        if not auth or any(not drive.get(k) for k in REQUIRED_DRIVE_KEYS):
            st.info("Google Drive chưa được kết nối với website. Cần cấu hình tài khoản Google và Streamlit Secrets một lần.")
            st.link_button("Hướng dẫn kết nối Google Drive", DOCS_URL)
            return

        if not getattr(st.user, "is_logged_in", False):
            st.warning("Đăng nhập tài khoản quản trị để tải hồ sơ; người xem website không có quyền ghi lên Drive.")
            st.button("Đăng nhập với Google", on_click=st.login, key="drive_admin_login")
            return

        actual_email = str(st.user.get("email", "")).strip().casefold()
        allowlisted = str(drive.get("allowed_email", "")).strip().casefold()
        if actual_email != allowlisted or st.user.get("email_verified") is not True:
            st.error("Tài khoản Google không có quyền quản trị kho hồ sơ này.")
            st.button("Đăng xuất", on_click=st.logout, key="drive_admin_logout_denied")
            return

        st.caption("Chỉ tài khoản đã xác thực được tạo dự án và tải tệp. Mỗi dự án và mỗi loại hồ sơ có thư mục riêng.")
        if st.button("Đăng xuất Google", key="drive_admin_logout"):
            st.logout()
            return

        try:
            service = from_streamlit_secrets(drive)
        except Exception:
            st.error("Chưa xác thực được quyền Google Drive. Kiểm tra các giá trị trong Streamlit Secrets.")
            return

        try:
            info = service.verify_connection()
            if info["email"].strip().casefold() != actual_email:
                st.error("Tài khoản cấp quyền Google Drive không khớp tài khoản đang đăng nhập.")
                return
        except Exception:
            st.error("Không truy cập được Google Drive. Kiểm tra API, quyền thư mục và refresh token.")
            return
        if st.button("Kiểm tra kết nối Drive", key="drive_check_connection"):
            st.success("Đã kết nối: " + info["root_name"])

        try:
            projects = service.list_projects()
        except Exception:
            st.error("Không đọc được danh sách dự án trên Drive. Kiểm tra quyền và mã thư mục gốc trong Secrets.")
            return

        with st.expander("Tạo dự án mới (tạo đủ 13 thư mục)", expanded=False):
            with st.form("drive_new_project_form", clear_on_submit=True):
                new_code = st.text_input("Mã dự án", placeholder="DA-001")
                new_name = st.text_input("Tên dự án", placeholder="TEN_DU_AN")
                submit_new = st.form_submit_button("Tạo thư mục dự án")
            if submit_new:
                try:
                    new_folder = service.ensure_project_tree(new_code, new_name)
                    st.session_state["drive_selected_project_id"] = new_folder
                    st.success("Đã tạo các thư mục cho dự án mới.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không tạo được thư mục. Kiểm tra mã dự án, tên trùng và quyền Google Drive.")

        if not projects:
            st.info("Chưa có dự án. Chọn 'Tạo dự án mới' để bắt đầu.")
            return

        project_ids = [p["id"] for p in projects]
        selected = st.session_state.get("drive_selected_project_id")
        if selected not in project_ids:
            st.session_state["drive_selected_project_id"] = project_ids[0]
        labels = {p["id"]: p["name"] for p in projects}
        project_id = st.selectbox("Dự án lưu hồ sơ", project_ids,
                                  format_func=lambda x: labels[x],
                                  key="drive_selected_project_id")
        st.link_button("Mở thư mục dự án trên Drive",
                       "https://drive.google.com/drive/folders/" + project_id)
        category = st.selectbox("Mục hồ sơ", options=list(FOLDER_CATEGORIES),
                                format_func=lambda k: " / ".join(FOLDER_CATEGORIES[k]),
                                key="drive_category")
        upload = st.file_uploader(
            "Chọn tệp bản vẽ, BOQ, BIM, PCCC hoặc báo cáo (tối đa 25 MB)",
            type=["pdf", "xlsx", "xls", "csv", "docx", "doc", "dwg", "dxf", "ifc",
                  "rvt", "nwd", "png", "jpg", "jpeg", "txt", "json", "zip"],
            key="drive_new_file")
        if st.button("Lưu tệp lên Google Drive", type="primary", disabled=upload is None,
                     key="drive_confirm_upload"):
            try:
                record = service.upload_to_project(project_id=project_id, category=category,
                                                   filename=upload.name, data=upload.getvalue())
                st.success("Đã tải lên: " + record["name"])
                if record.get("webViewLink"):
                    st.link_button("Mở tệp vừa lưu", record["webViewLink"])
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Không tải được tệp lên Drive. Kiểm tra quyền, dung lượng hoặc trạng thái kết nối.")
