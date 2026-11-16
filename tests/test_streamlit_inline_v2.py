"""Regression tests for the direct-iframe Streamlit Web 3D build."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_streamlit_runtime_v2 import build

class StreamlitV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=build(ROOT/"static")

    def test_embedded_script_and_styles(self):
        self.assertIn('<script>\n(function(){',self.html)
        self.assertIn('<base href="/app/static/">',self.html)
        self.assertGreaterEqual(self.html.count("<style>"),3)

    def test_no_module_url_dependencies(self):
        self.assertNotIn("data:text/javascript",self.html)
        self.assertNotIn('<script type="module"',self.html)
        self.assertNotIn('<script src="./src/',self.html)

    def test_app_is_present(self):
        self.assertIn('__require("src/app.js")',self.html)
        self.assertIn('id="nav"',self.html)
        self.assertIn('id="metrics"',self.html)

    def test_launcher_uses_html_instead_of_static_url(self):
        src=(ROOT/"streamlit_app.py").read_text(encoding="utf8")
        self.assertIn('st.iframe(page,',src)
        self.assertIn('components.html(page,',src)
        self.assertNotIn('components.iframe(url',src)
        self.assertIn('href="/?embed=true"',src)

    def test_public_files_only(self):
        for path in ("src/app.js","src/core/tvpl_sources.js","data/legal/MEP_XD_official_catalog.json"):
            self.assertTrue((ROOT/"static"/path).is_file(),path)
        for name in ("backend",".env","private_key.p12"):
            self.assertFalse((ROOT/"static"/name).exists(),name)

if __name__=="__main__":
    unittest.main()