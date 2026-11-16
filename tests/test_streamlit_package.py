from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"

class StaticStreamlitTests(unittest.TestCase):
    def test_site_files(self):
        for path in ("index.html", "src/app.js", "src/core/tvpl_sources.js", "src/polish.css", "assets/office_xd_mep_isometric_v5_7.webp", "data/legal/MEP_XD_official_catalog.json", "data/legal/MEP_XD_tvpl_candidates.json"):
            self.assertTrue((STATIC / path).is_file(), path)

    def test_no_private_files(self):
        for name in ("backend", ".env", "node_modules", "private_key.p12", "docs", "tests"):
            self.assertFalse((STATIC / name).exists(), name)

    def test_html_paths(self):
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        for path in re.findall(r'(?:href|src)="\\./([^"]+)"', html):
            self.assertTrue((STATIC / path).exists(), path)

    def test_streamlit_config(self):
        cfg = tomllib.loads((ROOT / ".streamlit/config.toml").read_text(encoding="utf-8"))
        self.assertTrue(cfg["server"]["enableStaticServing"])
        self.assertIn('components.iframe("app/static/index.html"', (ROOT / "streamlit_app.py").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
