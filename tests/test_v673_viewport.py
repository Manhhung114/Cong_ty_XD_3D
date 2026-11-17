"""V6.7.3 viewport regression: no outer scrolling below authenticated app."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ResponsiveViewportRegression(unittest.TestCase):
    def test_private_frame_owns_scroll_without_streamlit_outer_blank(self):
        source = (ROOT/"streamlit_app.py").read_text(encoding="utf8")
        self.assertLess(source.index("role = require_login(st)"), source.index("st.iframe(page"))
        self.assertIn("with st.container(key=\"xd_fullwidth_workspace\")", source)
        self.assertIn('height:100dvh!important;max-height:100dvh!important', source)
        self.assertIn('overflow-y:hidden!important', source)
        self.assertIn('height:calc(100dvh - var(--xd-auth-height))!important', source)
        self.assertIn('width:100vw!important;max-width:100vw!important', source)
        self.assertIn('flex:1 1 auto!important;min-height:0!important', source)
        self.assertIn("st.logout()", source)
        self.assertIn('load_snapshot(st)', source)
        self.assertNotIn("role = 'admin'", source)

    def test_banner_fills_entire_header_and_overview_expands_below(self):
        css = (ROOT/"src/polish.css").read_text(encoding="utf8")
        for marker in (
            "/* V6.7.3 — fill the device viewport",
            "background-size:100% 100%,100% 100%!important",
            "width:100vw!important;max-width:100vw!important",
            "#body:has(.overview-grid)>.overview-grid",
            "height:clamp(490px,62dvh,830px)!important",
            "#body:has(.overview-grid)>.lower-grid",
            "min-height:clamp(275px,34dvh,520px)",
            ".main>.content",
            "min-height:calc(100dvh - 64px - 72px)!important",
            "grid-template-columns:minmax(0,1fr) clamp(278px,24vw,380px)",
        ):
            self.assertIn(marker, css)
        self.assertEqual(css,(ROOT/"static/src/polish.css").read_text(encoding="utf8"))

    def test_mobile_breakpoint_preserves_navigation_and_imagery(self):
        css=(ROOT/"src/polish.css").read_text(encoding="utf8")
        self.assertRegex(css, r'@media\(max-width:750px\)[\s\S]*?\.main\{width:100%!important')
        self.assertIn('var(--xd-approved-header)',css)
        self.assertIn('var(--xd-approved-sidebar)',css)
        self.assertIn('var(--xd-approved-foyer)',css)
        index=(ROOT/"static/index.html").read_text(encoding="utf8")
        self.assertIn('class="sidebar-visual"',index)
        self.assertIn('id="commandTitle"',index)
        self.assertIn('id="languageSelect"',index)

if __name__ == "__main__":
    unittest.main()
