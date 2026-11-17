"""V6.7.5: prevent a tall skyline from being roof-only cropped in 64px header."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from scripts.build_streamlit_runtime_v2 import build

BASE=Path(__file__).resolve().parents[1]
ART=BASE/"static/assets/premium_header_visible_v675.svg"


class HeaderVisibilityFixTests(unittest.TestCase):
    def test_panoramic_art_matches_header_and_keeps_complete_facade(self):
        root=ET.fromstring(ART.read_text(encoding="utf8"))
        self.assertEqual(root.attrib["width"],"3200")
        self.assertEqual(root.attrib["height"],"120")
        self.assertEqual(root.attrib["viewBox"],"0 0 3200 120")
        self.assertEqual(root.attrib["preserveAspectRatio"],"xMidYMid meet")
        raw=ART.read_text(encoding="utf8")
        self.assertIn('x="1278" y="54" width="870" height="48"',raw)
        self.assertIn('x="1616" y="66" width="180" height="35"',raw)
        self.assertIn("Full building: complete roof, glass front, door",raw)
        self.assertNotIn("<script",raw.lower())
        # Cover crop must retain roof (y=22) through floor (y=108)
        # at a wide desktop viewport. Tall 3200x420 art fails this.
        scale=max(1910/3200,64/120)
        visible_height=64/scale
        y0=(120-visible_height)/2
        self.assertLess(y0,22)
        self.assertGreater(y0+visible_height,108)
        # At 1366px screen, center-building x range remains visible.
        scale=max(1366/3200,64/120)
        left=(3200-1366/scale)/2
        self.assertLess(left,1278)
        self.assertGreater(left+1366/scale,2148)

    def test_css_loads_asset_at_full_visibility_without_distortion(self):
        css=(BASE/"src/polish.css").read_text(encoding="utf8")
        self.assertEqual(css,(BASE/"static/src/polish.css").read_text(encoding="utf8"))
        fix=css.split("/* V6.7.5 Header Visibility Fix")[-1]
        self.assertIn("var(--xd-visible-header)!important",fix)
        self.assertIn("background-size:100% 100%,cover!important",fix)
        self.assertIn("background-position:center center,center 50%",fix)
        self.assertIn("rgba(4,23,44,.08)",fix)
        self.assertNotIn("var(--xd-premium-skyline)!important",fix)
        self.assertIn("@media(max-width:750px)",fix)

    def test_private_bundler_embeds_new_asset_and_preserves_oauth(self):
        html=build(BASE/"static",role="member",nonce="a"*32,initial_section="overview")
        self.assertIn("--xd-visible-header",html)
        self.assertIn("data:image/svg+xml;base64,",html)
        self.assertNotIn('./assets/premium_header_visible_v675.svg',html)
        self.assertIn("V6.7.5",html)
        app=(BASE/"streamlit_app.py").read_text(encoding="utf8")
        self.assertLess(app.index("role = require_login(st)"),app.index("st.iframe(page"))
        js=(BASE/"src/app.js").read_text(encoding="utf8")
        self.assertIn("n.id==='settings'",js)


if __name__=="__main__":
    unittest.main()
