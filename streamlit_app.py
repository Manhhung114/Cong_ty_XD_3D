"""Private, Google-authenticated Construction & MEP AI 3D Streamlit app.

Only logged-in, allowlisted users can see the 3D app. The Settings sheet is
admin-only; uploads/downloads are native dialogs on the existing sheets.
The Google Drive refresh token never reaches the iframe/browser.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as legacy_components

from scripts.build_streamlit_runtime_v2 import build
from drive_storage.in_app import require_login, mount_bridge, drive_dialog, access_management_dialog

st.set_page_config(
    page_title="Công ty Xây dựng & MEP AI 3D", page_icon="🏗️",
    layout="wide", initial_sidebar_state="collapsed",
)
st.markdown("""<style>
[data-testid="stHeader"],[data-testid="stToolbar"]{display:none}
[data-testid="stAppViewContainer"]{background:#07131f}
[data-testid="stMainBlockContainer"]{padding-top:.3rem;padding-bottom:0;max-width:none}
[data-testid="stVerticalBlock"]{gap:.2rem}
</style>""", unsafe_allow_html=True)

# The login gate precedes the iframe, bridge and all Google Drive operations.
role = require_login(st)
left, right = st.columns([7, 1], vertical_alignment="center")
with left:
    st.caption("XD & MEP AI 3D · " + {"admin": "Admin", "update": "Cập nhật", "read": "Chỉ đọc"}.get(role, "Nhân viên"))
with right:
    if st.button("Đăng xuất", key="logout_from_app", help="Đăng xuất tài khoản Google"):
        st.logout()

# Bridge listening for in-sheet actions ("Tải lên" and "Tải xuống").
action = mount_bridge(st)
if action:
    st.session_state.drive_in_app_action = action
    st.session_state.xd_current_sheet = action['section']

try:
    page = build(
        Path(__file__).resolve().parent / "static",
        role=role,
        nonce=st.session_state.drive_bridge_nonce,
        initial_section=st.session_state.get('xd_current_sheet', 'overview'),
        account_email=str(st.user.get('email', '')) if role == 'admin' else '',
        drive_configured=all(bool(st.secrets.get('drive', {}).get(k)) for k in ('root_folder_id','refresh_token','client_id','client_secret')),
    )
except Exception:
    st.error("Không thể khởi tạo Văn phòng 3D. Xem Manage app → Logs.")
    st.stop()

if hasattr(st, "iframe"):
    st.iframe(page, height=1100, width="stretch")
else:
    legacy_components.html(page, height=1100, scrolling=True)

# Native file controls are shown as a dialog over the selected app sheet,
# not a separate uploader page.
if st.session_state.get("drive_in_app_action"):
    current_action = st.session_state["drive_in_app_action"]
    if current_action.get("kind") == "access" and current_action.get("section") == "settings":
        access_management_dialog(st)
    else:
        drive_dialog(st)
