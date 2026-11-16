"""Streamlit Community Cloud launcher for the XD & MEP AI 3D application.

The existing JavaScript app is served as a same-origin static page.
No project data or API keys are handled by this Python launcher.
"""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Công ty Xây dựng & MEP AI 3D",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stHeader"], [data-testid="stToolbar"] { display: none; }
[data-testid="stAppViewContainer"] { background: #07131f; }
[data-testid="stMainBlockContainer"] { padding-top: 0.45rem; padding-bottom: 0; max-width: none; }
[data-testid="stVerticalBlock"] { gap: 0.5rem; }
.streamlit-open { display:block; padding: 0.78rem 1rem; margin: 0 0 0.35rem; border-radius: 0.75rem; text-decoration:none !important; color:#052331 !important; background:linear-gradient(90deg,#66d9ce,#8ddfec); font-weight:700; text-align:center; }
.streamlit-tip { color:#9eb8c4; font-size:0.83rem; margin:0 0 0.4rem; }
</style>
<a class="streamlit-open" href="./app/static/index.html" target="_blank" rel="noopener noreferrer">
  Mở văn phòng 3D toàn màn hình · Open full screen
</a>
<div class="streamlit-tip">Trên điện thoại, chọn mở toàn màn hình để có trải nghiệm tốt nhất.</div>
""", unsafe_allow_html=True)
components.iframe("app/static/index.html", height=980, scrolling=True)
