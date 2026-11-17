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
from drive_storage.workspace_ui import load_snapshot, handle_workspace_action, workspace_dialog
from drive_storage.ai_settings_ui import ai_settings_dialog, ai_connection_dialog
from drive_storage.v75_rollout import BUILD_LABEL

st.set_page_config(
    page_title="Công ty Xây dựng & MEP AI 3D", page_icon="🏗️",
    layout="wide", initial_sidebar_state="collapsed",
)
st.markdown("""<style>
[data-testid="stHeader"],[data-testid="stToolbar"]{display:none}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{
    width:100%!important;max-width:100%!important;margin:0!important;
    overflow-x:clip!important;background:#041427!important;
}
[data-testid="stMain"],[data-testid="stAppViewContainer"]>section.main{
    width:100%!important;max-width:100%!important;margin:0!important;
    padding:0!important;min-width:0!important;
}
[data-testid="stMainBlockContainer"],.block-container{
    box-sizing:border-box!important;width:100%!important;max-width:none!important;
    padding:0!important;margin:0!important;min-width:0!important;
}
[data-testid="stMainBlockContainer"]>div,
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]{
    width:100%!important;max-width:none!important;min-width:0!important;
}
[data-testid="stVerticalBlock"]{gap:0!important}
[data-testid="stHorizontalBlock"]{margin:0 8px!important;gap:.5rem!important}
.st-key-xd_fullwidth_workspace,
.st-key-xd_fullwidth_workspace>div{
    width:100%!important;max-width:100%!important;min-width:0!important;
    margin:0!important;padding:0!important;
}
.st-key-xd_fullwidth_workspace iframe{
    display:block!important;width:100%!important;max-width:100vw!important;
    height:calc(100dvh - 44px)!important;min-height:440px!important;
    border:0!important;margin:0!important;padding:0!important;
}
@media(max-width:750px){
 [data-testid="stHorizontalBlock"]{margin:0 4px!important}
 .st-key-xd_fullwidth_workspace iframe{height:calc(100dvh - 48px)!important}
}
/* V6.7.3: no secondary Streamlit-page scrolling below the application.
   The authenticated iframe is the scroll owner for all in-app sheets. */
:root{--xd-auth-height:46px}
[data-testid="stAppViewContainer"]:has(.st-key-xd_fullwidth_workspace){
    height:100dvh!important;min-height:0!important;overflow-y:hidden!important;
}
[data-testid="stAppViewContainer"]:has(.st-key-xd_fullwidth_workspace)
  [data-testid="stMain"]{
    height:100dvh!important;max-height:100dvh!important;min-height:0!important;
    overflow-y:hidden!important;
}
[data-testid="stMainBlockContainer"]:has(.st-key-xd_fullwidth_workspace){
    height:100dvh!important;max-height:100dvh!important;min-height:0!important;
    width:100%!important;max-width:100%!important;
    display:flex!important;flex-direction:column!important;overflow:hidden!important;
}
[data-testid="stMainBlockContainer"]:has(.st-key-xd_fullwidth_workspace)
  [data-testid="stVerticalBlock"]:has(.st-key-xd_fullwidth_workspace){
    width:100%!important;max-width:100%!important;min-width:0!important;
    flex:1 1 auto!important;min-height:0!important;
}
.st-key-xd_fullwidth_workspace{
    flex:1 1 auto!important;min-height:0!important;
    width:100vw!important;max-width:100vw!important;min-width:0!important;
    position:relative!important;left:50%!important;
    transform:translateX(-50%)!important;
    overflow:hidden!important;
}
.st-key-xd_fullwidth_workspace,
.st-key-xd_fullwidth_workspace > div,
.st-key-xd_fullwidth_workspace [data-testid="stIframe"],
.st-key-xd_fullwidth_workspace [data-testid="stElementContainer"]{
    width:100%!important;max-width:none!important;min-width:0!important;
    box-sizing:border-box!important;margin:0!important;padding:0!important;
}
.st-key-xd_fullwidth_workspace iframe{
    display:block!important;width:100%!important;max-width:none!important;
    height:calc(100dvh - var(--xd-auth-height))!important;
    min-height:0!important;border:0!important;
    margin:0!important;padding:0!important;
}
@media(max-width:750px){
 :root{--xd-auth-height:50px}
 .st-key-xd_fullwidth_workspace{left:50%!important;max-width:100vw!important}
}

</style>""", unsafe_allow_html=True)

# The login gate precedes the iframe, bridge and all Google Drive operations.
role = require_login(st)
left, right = st.columns([7, 1], vertical_alignment="center")
with left:
    st.caption(f"XD & MEP AI 3D · {BUILD_LABEL} · " + {"admin": "Admin", "update": "Cập nhật", "read": "Chỉ đọc"}.get(role, "Nhân viên"))
with right:
    if st.button("Đăng xuất", key="logout_from_app", help="Đăng xuất tài khoản Google"):
        st.logout()

# Bridge listening for in-sheet actions ("Tải lên" and "Tải xuống").
action = mount_bridge(st)
if action:
    # Never display a successful *previous* action as feedback for a new one.
    st.session_state.pop("xd_last_action_notice", None)
    if action.get("kind") == "workspace":
        # A previously dismissed Settings dialog must not reopen on task click.
        # Streamlit native dialogs are controlled by session state, not by
        # the iframe page currently visible.
        st.session_state.drive_in_app_action = None
        st.session_state.pop("v677_api_probe_pending", None)
        st.session_state.pop("v677_api_probe_result", None)
        try:
            handle_workspace_action(st, action)
        except (PermissionError, ValueError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("Không thể lưu thao tác dùng chung. Dữ liệu cũ trên Drive được giữ nguyên.")
    else:
        # A new settings/Drive dialog supersedes any old task dialog.
        st.session_state.xd_workspace_dialog = None
        st.session_state.drive_in_app_action = action
        st.session_state.xd_current_sheet = action['section']
        if action.get("kind") == "ai_check":
            st.session_state.v677_api_probe_pending = True
            st.session_state.v677_api_probe_result = None

feedback = st.session_state.pop("xd_workspace_feedback", "")
if feedback:
    st.session_state.xd_last_action_notice = feedback
    st.toast(feedback)

notice = str(st.session_state.get("xd_last_action_notice") or "")[:500]
if notice:
    with st.container():
        col_msg, col_close = st.columns([9, 1], vertical_alignment="center")
        with col_msg:
            st.success("✓ " + notice)
        with col_close:
            if st.button("Ẩn", key="xd_dismiss_action_success"):
                st.session_state.pop("xd_last_action_notice", None)
                st.rerun()
try:
    shared_state = load_snapshot(st)
    shared_state["lastActionNotice"] = notice
except Exception:
    st.error("Không đọc được dữ liệu dự án dùng chung từ Drive. Ứng dụng tạm chặn thao tác để bảo vệ dữ liệu. Kiểm tra Manage app → Logs và kết nối Drive.")
    st.stop()

try:
    page = build(
        Path(__file__).resolve().parent / "static",
        role=role,
        nonce=st.session_state.drive_bridge_nonce,
        initial_section=st.session_state.get('xd_current_sheet', 'overview'),
        account_email=str(st.user.get('email', '')) if role == 'admin' else '',
        drive_configured=all(bool(st.secrets.get('drive', {}).get(k)) for k in ('root_folder_id','refresh_token','client_id','client_secret')),
        cloud_snapshot=shared_state,
    )
except Exception:
    st.error("Không thể khởi tạo Văn phòng 3D. Xem Manage app → Logs.")
    st.stop()

# Own the iframe's wrapper so its viewport size can follow each device, not
# Streamlit's default centered block width / 6-rem horizontal padding.
with st.container(key="xd_fullwidth_workspace"):
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
    elif current_action.get("kind") == "ai_config" and current_action.get("section") == "settings":
        ai_settings_dialog(st)
    elif current_action.get("kind") == "ai_check" and current_action.get("section") == "settings":
        ai_connection_dialog(st)
    else:
        drive_dialog(st)

# Only one native dialog may be opened per Streamlit script run.
# The two action namespaces are mutually exclusive after dispatch above.
# Server-side workflows with verified Google identity (V5.9/V6.0).
if not st.session_state.get("drive_in_app_action") and st.session_state.get('xd_workspace_dialog'):
    workspace_dialog(st)
