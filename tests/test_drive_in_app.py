import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class TestInAppDrive(unittest.TestCase):
    def test_allowed_sections(self):
        from drive_storage.in_app import SECTIONS
        from drive_storage.manager import FOLDER_CATEGORIES
        self.assertEqual(set(SECTIONS), {"documents","boq","bim","tasks","reviews","projects"})
        self.assertTrue(set().union(*[set(v) for v in SECTIONS.values()]) <= set(FOLDER_CATEGORIES))
    def test_auth_login_before_app(self):
        text=(ROOT/"drive_storage/in_app.py").read_text(encoding="utf8")
        self.assertIn("st.login()", text)
        self.assertIn("st.stop()", text)
        self.assertIn("st.user.get(\"email_verified\"",text)
    def test_bridge_no_secrets(self):
        text=(ROOT/"drive_storage/in_app.py").read_text(encoding="utf8")
        self.assertIn("XD_MEP_DRIVE_V1",text)
        self.assertNotIn("client_secret",text)
        self.assertNotIn("refresh_token",text)
    def test_resumable_upload_500mb(self):
        from drive_storage.manager import MAX_FILE_SIZE
        self.assertEqual(MAX_FILE_SIZE,500*1024*1024)
        text=(ROOT/"drive_storage/manager.py").read_text(encoding="utf8")
        self.assertIn("MediaIoBaseUpload(",text)
        self.assertIn("next_chunk(num_retries=3)",text)

if __name__=="__main__": unittest.main()
