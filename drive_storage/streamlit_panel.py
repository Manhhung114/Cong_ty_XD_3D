"""Authenticated Streamlit admin uploader: no Google credentials in browser.

Requires Google OpenID Connect st.login() and an allowlisted admin email.
The Drive OAuth credential is independent and stays in server secrets.
"""
from __future__ import annotations

from .manager import FOLDER_CATEGORIES, from_streamlit_secrets


def display(st):
    try:
        drive = st.secrets.get("drive", {})
        auth_configured = bool(st.secrets.get("auth", {}))
    except Exception:
        auth_configured = False
    if not auth_configured or not drive.get("allowed_email"):
        return
    with st.sidebar.expander("Google Drive · Kho hồ sơ", expanded=False):
        if not st.user.is_logged_in:
            st.caption("Đăng nhập tài khoản được cấp phép để quản lý hồ sơ Google Drive.")
            if st.button("Đăng nhập", key="drive_login"):
                st.login()
            return
        identity = str(st.user.get("email", "")).strip().casefold()
        verified = st.user.get("email_verified", False)
        if identity != str(drive["allowed_email"]).strip().casefold() or verified is not True:
            st.error("Tài khoản không có quyền tải hồ sơ lên Google Drive.")
            return
        st.caption("Mỗi dự án được lưu trong một thư mục riêng. Mỗi lần tải lên tạo một revision mới.")
        code = st.text_input("Mã dự án", value="", key="drive_project_code")
        name = st.text_input("Tên dự án", value="", key="drive_project_name")
        category = st.selectbox("Nhóm hồ sơ", list(FOLDER_CATEGORIES), format_func=lambda c:" / ".join(FOLDER_CATEGORIES[c]), key="drive_category")
        file = st.file_uploader("Chọn tệp hồ sơ (tối đa 25 MB)",type=["pdf", "xlsx", "xls", "csv", "docx", "doc", "dwg", "dxf", "ifc", "rvt", "nwd", "png", "jpg", "jpeg", "txt", "json", "zip"], key="drive_upload")
        if st.button("Lưu lên Google Drive",type="primary",disabled=file is None or not code.strip() or not name.strip(),key="drive_upload_button"):
            try:
                service = from_streamlit_secrets(drive)
                info = service.upload(code=code,project_name=name,category=category,filename=file.name,data=file.getvalue())
                st.success("Đã lưu phiên bản: "+info["name"])
                if info.get("webViewLink"):
                    st.link_button("Mở tệp trên Drive",info["webViewLink"])
            except Exception as err:
                st.error("Không thể lưu lên Google Drive: "+str(err))
