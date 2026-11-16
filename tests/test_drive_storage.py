import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from drive_storage.manager import DriveStorage,FOLDER_CATEGORIES,validated_project_folder,safe_filename
class TestDriveStorage(unittest.TestCase):
    def test_project_folder(self):
        self.assertEqual(validated_project_folder('S234','SUNSHINE SKY CITY'),'S234_SUNSHINE_SKY_CITY')
        self.assertEqual(validated_project_folder('s234','S234_SUNSHINE_SKY_CITY'),'S234_SUNSHINE_SKY_CITY')
    def test_bad_codes(self):
        for code in ('../','', 'a', 'A B', 'AA/BB'):
            with self.assertRaises(ValueError):validated_project_folder(code,'Good Project')
    def test_bad_filenames(self):
        for name in ('../../../x.exe','notes.exe','', 'dir/foo.pdf'):
            if name=='dir/foo.pdf':self.assertEqual(safe_filename(name),'dir_foo.pdf')
            else:
                with self.assertRaises(ValueError):safe_filename(name)
    def test_categories(self):
        self.assertEqual(FOLDER_CATEGORIES['boq_mep'],('03_BOQ_DU_TOAN','MEP'))
        self.assertNotEqual(FOLDER_CATEGORIES['boq_mep'],FOLDER_CATEGORIES['boq_xd'])
    def test_root_id(self):
        with self.assertRaises(ValueError):DriveStorage(object(),'invalid')
if __name__=='__main__':unittest.main()
