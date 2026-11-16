"""Streamlit Community Cloud launcher for XD & MEP AI 3D (V5.7.9).

Render trusted bundled HTML directly in Streamlit's JavaScript-enabled iframe.
Avoid serving JS modules or data: module imports from the static endpoint.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from scripts.build_streamlit_runtime_v2 import build
from drive_storage.streamlit_panel import display as render_google_drive_storage

st.set_page_config(
    page_title="Công ty Xây dựng & MEP AI 3D",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def render_page() -> str:
    # Rebuild on every run: Streamlit source-code caching may retain outdated JS after GitHub updates.
    return build(Path(__file__).resolve().parent / "static")

# Google OAuth is handled at the top-level Streamlit page, never in the embedded 3D iframe.
# This private screen is linked from Cài đặt → Google Drive in the 3D UI.
if st.query_params.get("drive") == "settings":
    st.markdown("## Google Drive · Cài đặt kho hồ sơ")
    st.link_button("← Trở về Văn phòng 3D", "https://congtyxd.streamlit.app/")
    render_google_drive_storage(st, expanded=True)
    st.stop()


try:
    page = render_page()
except Exception as exc:
    st.error("Không thể khởi tạo giao diện 3D. Kiểm tra Manage app → Logs.")
    st.exception(exc)
    st.stop()

st.markdown("""
<style>
[data-testid="stHeader"], [data-testid="stToolbar"] { display:none; }
[data-testid="stAppViewContainer"] { background:#07131f; }
[data-testid="stMainBlockContainer"] { padding-top:0.3rem; padding-bottom:0; max-width:none; }
[data-testid="stVerticalBlock"] { gap:0.25rem; }
.streamlit-open { display:block; padding:0.8rem 1rem; margin:0 0 0.25rem; border-radius:0.8rem; text-decoration:none !important; color:#052331 !important; background:linear-gradient(90deg,#66d9ce,#8ddfec); font-weight:700; text-align:center; }
</style>
<a class="streamlit-open" href="/?embed=true" target="_blank" rel="noopener noreferrer">
  Mở giao diện rộng trên điện thoại · Open wide view
</a>
""", unsafe_allow_html=True)

# Streamlit 1.63+ supports st.iframe with trusted HTML strings.
# Older installations can still use the Streamlit component iframe.
if hasattr(st, "iframe"):
    st.iframe(page, height=1050, width="stretch")
else:
    components.html(page, height=1050, scrolling=True)
