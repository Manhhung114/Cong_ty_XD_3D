"""Regression tests for Streamlit static content rendered as self-contained HTML."""
from pathlib import Path
from scripts.build_streamlit_inline import build

ROOT = Path(__file__).resolve().parents[1]


def test_static_page_has_executable_inline_module():
    html = build(ROOT / "static").read_text(encoding="utf-8")
    assert '<script type="module" src="data:text/javascript;base64,' in html
    assert 'rel="stylesheet" href="./src/' not in html
    assert '<script type="module" src="./src/' not in html
    assert '<style>' in html
    assert '__previewData' not in html
    assert '__localStore' not in html
    assert '<nav id="nav"' in html


def test_does_not_include_secrets_or_backend():
    html = build(ROOT / "static").read_text(encoding="utf-8")
    for token in ['PRIVATE_SETUP_AND_PASSWORDS', 'XD_MEP_STORE_PASSWORD', 'backend/main.py']:
        assert token not in html
