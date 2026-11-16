import sys
import unittest
import re
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from drive_storage.manager import DriveStorage, FOLDER_CATEGORIES


class FakeRequest:
    def __init__(self, thunk): self.thunk = thunk
    def execute(self): return self.thunk()


class FakeFiles:
    def __init__(self, data): self.d = data
    def list(self, q='', fields='', pageSize=100, pageToken=None):
        def run():
            folder = re.search(r"'([^']+)' in parents", q)
            target = re.search(r"name = '([^']+)'", q)
            folder_id = folder.group(1) if folder else None
            name = target.group(1) if target else None
            files = [f.copy() for f in self.d.items.values()
                     if folder_id in f.get('parents', [])
                     and (name is None or f['name'] == name)
                     and ("mimeType = 'application/vnd.google-apps.folder'" not in q
                          or f['mimeType'] == 'application/vnd.google-apps.folder')]
            return {'files': files}
        return FakeRequest(run)
    def create(self, body, fields='', media_body=None):
        def run():
            self.d.seq += 1
            rec = {'id': 'new-id-000000000' + str(self.d.seq),
                   'name': body['name'],
                   'parents': body.get('parents', []),
                   'mimeType': body.get('mimeType', 'application/pdf'),
                   'appProperties': body.get('appProperties', {}),
                   'webViewLink': 'https://drive.google.com/file/d/new-id/view'}
            self.d.items[rec['id']] = rec
            return rec.copy()
        return FakeRequest(run)
    def get(self, fileId, fields=''):
        def run():
            f = self.d.items[fileId].copy()
            f['capabilities'] = {'canAddChildren': True}
            f['trashed'] = False
            return f
        return FakeRequest(run)


class FakeAbout:
    def get(self, fields=''): return FakeRequest(lambda: {'user': {'emailAddress': 'admin@example.com'}})


class FakeDrive:
    def __init__(self):
        self.seq = 0
        self.items = {}
        self.items['root-folder-0000000']={'id': 'root-folder-0000000',
              'name': 'CONG_TY_XD_MEP_AI_3D',
              'parents': [], 'mimeType': 'application/vnd.google-apps.folder'}
        self.items['project-root-00000']={'id': 'project-root-00000',
              'name': '01_DU_AN', 'parents': ['root-folder-0000000'],
              'mimeType': 'application/vnd.google-apps.folder'}
        self.items['existing-s234-0000']={'id': 'existing-s234-0000',
              'name': 'S234_SUNSHINE_SKY_CITY', 'parents': ['project-root-00000'],
              'mimeType': 'application/vnd.google-apps.folder'}
        self.items['outside-root-000000']={'id': 'outside-root-000000',
              'name': 'OTHER_CUSTOMER', 'parents': [],
              'mimeType': 'application/vnd.google-apps.folder'}
    def files(self): return FakeFiles(self)
    def about(self): return FakeAbout()


class DriveStructureTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeDrive()
        self.drive = DriveStorage(self.fake, 'root-folder-0000000')

    def test_existing_project_reused_casefolded(self):
        self.assertEqual(self.drive.project('s234', 'Sunshine Sky City'), 'existing-s234-0000')
        self.assertEqual(len(self.drive.list_projects()), 1)

    def test_same_code_other_name_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Mã dự án đã có'):
            self.drive.project('S234', 'COMPLETELY_DIFFERENT_SITE')
        self.assertEqual(len(self.drive.list_projects()), 1)

    def test_scaffolds_separate_project_categories(self):
        new_id = self.drive.ensure_project_tree('DA002', 'NHA MAY B')
        self.assertNotEqual(new_id, 'existing-s234-0000')
        direct = [f for f in self.fake.items.values() if new_id in f.get('parents', [])]
        self.assertEqual(len(direct), 13)
        self.assertEqual(len(self.drive.list_projects()), 2)
        self.assertEqual(self.drive.ensure_project_tree('DA002', 'NHA MAY B'), new_id)
        direct2 = [f for f in self.fake.items.values() if new_id in f.get('parents', [])]
        self.assertEqual(len(direct2), 13)
        self.assertEqual(self.drive.destination_by_id(new_id,'drawings_mep') !=
                         self.drive.destination_by_id(new_id,'drawings_xd'), True)
        self.assertNotEqual(self.drive.destination_by_id(new_id,'boq_mep'),
                            self.drive.destination_by_id('existing-s234-0000','boq_mep'))

    def test_unrelated_project_id_rejected(self):
        with self.assertRaisesRegex(ValueError, 'không thuộc'):
            self.drive.destination_by_id('outside-root-000000', 'boq_mep')

    def test_verify_connection(self):
        info=self.drive.verify_connection()
        self.assertEqual(info['email'],'admin@example.com')
        self.assertEqual(info['root_name'],'CONG_TY_XD_MEP_AI_3D')

    def test_revision_and_preserve_old_files(self):
        http=ModuleType('googleapiclient.http')
        class MediaIoBaseUpload:
            def __init__(self, stream, mimetype, resumable): pass
        http.MediaIoBaseUpload=MediaIoBaseUpload
        root=ModuleType('googleapiclient')
        with patch.dict(sys.modules, {'googleapiclient': root, 'googleapiclient.http':http}):
            a=self.drive.upload_to_project(project_id='existing-s234-0000',category='boq_mep',filename='BOQ.xlsx',data=b'data-test')
            b=self.drive.upload_to_project(project_id='existing-s234-0000',category='boq_mep',filename='BOQ.xlsx',data=b'data-test')
        self.assertEqual(a['name'],'BOQ_R01.xlsx')
        self.assertEqual(b['name'],'BOQ_R02.xlsx')
        self.assertNotEqual(a['id'],b['id'])
        self.assertEqual(a['parents'],b['parents'])

if __name__=='__main__': unittest.main()
