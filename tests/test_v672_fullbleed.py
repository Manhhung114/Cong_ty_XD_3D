"""Full-bleed Streamlit viewport and actual user-approved art regression."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class FullBleedTests(unittest.TestCase):
    def test_streamlit_no_default_six_rem_side_padding(self):
        src=(ROOT/"streamlit_app.py").read_text(encoding="utf8")
        self.assertIn('layout="wide"',src)
        self.assertIn('st.container(key="xd_fullwidth_workspace")',src)
        self.assertIn('width="stretch"',src)
        self.assertIn('width:100%!important;max-width:none!important',src)
        self.assertIn('padding:0!important;margin:0!important',src)
        self.assertIn('height:calc(100dvh - 44px)!important',src)
        self.assertLess(src.index("role = require_login(st)"),src.index("st.iframe(page"))

    def test_image_assets_are_exact_small_webp_files(self):
        for name in ("header","sidebar","foyer"):
            path=ROOT/"static"/"assets"/f"user_reference_{name}_v672.webp"
            self.assertTrue(path.is_file(),str(path))
            data=path.read_bytes()
            self.assertTrue(data.startswith(b"RIFF"))
            self.assertEqual(data[8:12],b"WEBP")
            self.assertGreater(len(data),1000)
            self.assertLess(len(data),25000)
        self.assertIn(
            "user_reference_sidebar_v672.webp",
            (ROOT/"src"/"core"/"command_shell.js").read_text(encoding="utf8"),
        )

    def test_full_bleed_styles_apply_to_all_sheets(self):
        css=(ROOT/"src"/"polish.css").read_text(encoding="utf8")
        for text in (
            "#app{min-height:100dvh!important",
            ".main{\n width:calc(100% - 226px)!important",
            ".content{\n box-sizing:border-box;width:100%!important;max-width:none!important",
            "background-image:linear-gradient(90deg",
            "var(--xd-approved-header)",
            "var(--xd-approved-sidebar)",
            "var(--xd-approved-foyer)",
            "@media(max-width:750px)",
            ".main{width:100%!important;max-width:100vw!important}",
        ):
            self.assertIn(text,css)
        self.assertEqual(css,(ROOT/"static"/"src"/"polish.css").read_text(encoding="utf8"))

    def test_inline_bundle_includes_private_built_art_not_external_urls(self):
        from scripts.build_streamlit_runtime_v2 import build
        page=build(ROOT/"static",role="member",nonce="")
        self.assertIn("data:image/webp;base64,",page)
        self.assertIn("--xd-approved-header",page)
        self.assertIn("--xd-approved-sidebar",page)
        self.assertIn("--xd-approved-foyer",page)
        self.assertNotIn('<script type="module" src=',page)
        self.assertNotIn('https://raw.githubusercontent.com/',page)

if __name__=="__main__":
    unittest.main()
