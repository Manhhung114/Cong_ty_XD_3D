"""V6.7.4 scalable premium header & isolated Streamlit frontend regression."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from scripts.build_streamlit_runtime_v2 import build

BASE = Path(__file__).resolve().parents[1]
STATIC = BASE / "static"


class PremiumHeaderTests(unittest.TestCase):
    def test_new_vector_art_is_4k_ready_without_pixelated_small_crop(self):
        for filename, min_width in [
            ("premium_skyline_v674.svg", 3200),
            ("premium_emblem_v674.svg", 512),
        ]:
            path = STATIC / "assets" / filename
            root = ET.fromstring(path.read_text(encoding="utf-8"))
            self.assertTrue(root.tag.endswith("svg"))
            self.assertGreaterEqual(int(root.attrib["width"]), min_width)
            self.assertIn("viewBox", root.attrib)
            self.assertNotIn("<script", path.read_text(encoding="utf-8").lower())
            self.assertNotIn("https://", path.read_text(encoding="utf-8").lower())
        skyline = (STATIC/"assets/premium_skyline_v674.svg").read_text(encoding="utf-8")
        self.assertGreater(skyline.count("<rect "), 250)
        self.assertIn("preserveAspectRatio", skyline)

    def test_authenticated_inline_bundle_includes_both_scalable_assets(self):
        page = build(STATIC, role="member", nonce="a"*32, initial_section="overview")
        self.assertIn("data:image/svg+xml;base64,", page)
        self.assertIn("--xd-premium-skyline", page)
        self.assertIn("--xd-premium-emblem", page)
        self.assertIn("Premium Header", page)
        self.assertNotIn('<script type="module" src=', page)
        self.assertIn('window.__xdAuthRole = "member"', page)

    def test_production_css_matches_source_and_no_pixel_stretching(self):
        source = (BASE / "src/polish.css").read_text(encoding="utf-8")
        mirror = (STATIC / "src/polish.css").read_text(encoding="utf-8")
        self.assertEqual(source, mirror)
        premium = source[source.index("/* V6.7.4 Premium Header"):]
        self.assertIn("background-size:100% 100%,cover!important", premium)
        self.assertIn("var(--xd-premium-skyline)", premium)
        self.assertIn("background-position:center center,center 45%", premium)
        self.assertIn("image-rendering:auto", premium)
        self.assertIn("@media(max-width:750px)", premium)
        self.assertNotIn("background-size:100% 100%,100% 100%", premium)
        self.assertIn("background-size:100% 100%,100% 100%", source,
                      "preserve historical stylesheet so other layout tests remain stable")

    def test_google_oauth_and_settings_gate_are_unmodified(self):
        source = (BASE / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertLess(source.index("role = require_login(st)"),
                        source.index("st.iframe(page"))
        self.assertIn("st.logout()", source)
        js = (BASE / "src/app.js").read_text(encoding="utf-8")
        self.assertIn("n.id==='settings'", js)


if __name__ == "__main__":
    unittest.main()
