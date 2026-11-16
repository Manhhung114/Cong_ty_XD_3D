from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class StreamlitLegalRecoveryTests(unittest.TestCase):
    def test_launcher_does_not_cache_bundled_old_javascript(self):
        src=(ROOT/'streamlit_app.py').read_text(encoding='utf8')
        self.assertNotIn('@st.cache_data',src)
        self.assertIn('page = build(',src)

    def test_legal_has_self_contained_recovery(self):
        src=(ROOT/'static/src/app.js').read_text(encoding='utf8')
        self.assertIn('function legalRecoveryPage(error)',src)
        self.assertIn("if(tab==='legal')",src)
        self.assertIn('id="legalTVPLUpdate"',src)
        self.assertIn('legalStatistics(validLegalRecords)',src)

if __name__=='__main__':
    unittest.main()
