"""Streamlit Community Cloud launcher for XD & MEP AI 3D.

The static HTML uses embedded, versioned JS/CSS so that the browser does not
need Streamlit to serve ES modules with a JavaScript MIME type.
"""
from hashlib import sha256
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from scripts.build_streamlit_inline import build

st.set_page_config(
    page_title="Công ty Xây dựng & MEP AI 3D",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    static = Path(__file__).resolve().parent / "static"
    page = build(static)
    fingerprint = sha256(page.read_bytes()).hexdigest()[:12]
except Exception as exc:
    st.error("Không thể khởi tạo giao diện 3D. Vui lòng kiểm tra mục Manage app → Logs.")
    st.exception(exc)
    st.stop()

url = f"app/static/{page.name}?v={fingerprint}"
st.markdown(f"""
<style>
[data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none; }}
[data-testid="stAppViewContainer"] {{ background: #07131f; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 0.4rem; padding-bottom: 0; max-width: none; }}
[data-testid="stVerticalBlock"] {{ gap: 0.4rem; }}
.streamlit-open {{ display:block; padding: 0.8rem 1rem; margin: 0 0 0.3rem; border-radius: 0.8rem; text-decoration:none !important; color:#052331 !important; background:linear-gradient(90deg,#66d9ce,#8ddfec); font-weight:700; text-align:center; }}
</style>
<a class="streamlit-open" href="./{url}" target="_blank" rel="noopener noreferrer">
Mở văn phòng 3D toàn màn hình · Open full screen
</a>
""", unsafe_allow_html=True)
components.iframe(url, height=980, scrolling=True)
