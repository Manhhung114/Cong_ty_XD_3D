import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.main import create_app
from backend.models import User
from backend.security import password_hash

@pytest.fixture()
def scenario(tmp_path):
 app=create_app('sqlite:///'+str(tmp_path/'test.sqlite3'),storage_dir=tmp_path/'documents',serve_frontend=False)
 with app.state.dbmaker() as s:
  s.add(User(username='admin',full_name='Administrator',password_hash=password_hash('admin-secure-123456'),global_role='admin'))
  s.commit()
 client=TestClient(app)
 def login(name,password):
  response=client.post('/api/auth/login',json={'username':name,'password':password});assert response.status_code==200,response.text
  return {'Authorization':'Bearer '+response.json()['token']}
 headers=login('admin','admin-secure-123456')
 def request(path,**kwargs):return client.request(kwargs.pop('method','GET'),path,headers=headers,**kwargs)
 return client,headers,login,request

def setup(scenario):
 client,admin,login,r=scenario
 ids={}
 for code in ['A01','B02']:
  response=r('/api/projects',method='POST',json={'code':code,'name':'Project '+code})
  assert response.status_code==200,response.text
  ids[code]=response.json()['id']
 users=[('author','Engineer'),('reviewer','QA reviewer'),('lead','MEP discipline lead'),('pm','Project manager'),('outsider','Outsider'),('xd','Construction reviewer')]
 for username,name in users:
  assert r('/api/admin/users',method='POST',json={'username':username,'full_name':name,'password':f'{username}-super-long-password'}).status_code==200
 for username,role,division in [('author','engineer','mep'),('reviewer','qa','mep'),('lead','mep_lead','mep'),('pm','project_manager','all'),('xd','construction_lead','construction')]:
  assert r(f'/api/projects/{ids["A01"]}/members',method='POST',json={'username':username,'role':role,'division':division}).status_code==200
 creds={name:login(name,name+'-super-long-password') for name,_ in users}
 return ids,creds

def test_health_and_auth(scenario):
 client,admin,login,r=scenario
 assert client.get('/api/health').json()['agentExecution']=='disabled'
 assert client.get('/api/projects').status_code==401
 assert client.post('/api/auth/login',json={'username':'admin','password':'wrong'}).status_code==401
 assert r('/api/auth/me').json()['admin']
 assert r('/api/admin/agents',method='PUT',json={}).status_code==405

def test_projects_are_isolated_and_membership_controls(scenario):
 client,admin,login,r=scenario;ids,creds=setup(scenario)
 assert len(client.get('/api/projects',headers=creds['author']).json())==1
 assert client.get(f'/api/projects/{ids["B02"]}/tasks',headers=creds['author']).status_code==403
 assert client.get(f'/api/projects/{ids["A01"]}/tasks',headers=creds['outsider']).status_code==403
 assert client.post(f'/api/projects/{ids["A01"]}/tasks',headers=creds['author'],json={'title':'Load design','dept':'structure'}).status_code==403
 assert client.post('/api/projects',headers=creds['author'],json={'code':'A03','name':'Unauthorized project'}).status_code==403
 assert client.get(f'/api/projects/{ids["A01"]}/members',headers=creds['author']).status_code==200
 assert client.post(f'/api/projects/{ids["A01"]}/members',headers=creds['author'],json={'username':'outsider','role':'viewer'}).status_code==403

def test_review_requires_three_distinct_authorized_people(scenario):
 client,admin,login,r=scenario;ids,creds=setup(scenario);p=ids['A01']
 b=client.post(f'/api/projects/{p}/tasks',headers=creds['author'],json={'title':'Check electrical load','dept':'electrical','assignee':'ELE'});assert b.status_code==200,b.text
 tid=b.json()['id']; base=f'/api/projects/{p}/tasks/{tid}'
 assert client.post(base+'/review',headers=creds['reviewer'],json={'decision':'approve'}).status_code==409
 assert client.post(base+'/submit',headers=creds['author'],json={'summary':'short'}).status_code==422
 assert client.post(base+'/submit',headers=creds['author'],json={'summary':'Calculated the electrical load and attached findings.'}).status_code==200
 assert client.post(base+'/review',headers=creds['author'],json={'decision':'approve'}).status_code==403
 assert client.post(base+'/review',headers=creds['lead'],json={'decision':'approve'}).status_code==403
 assert client.post(base+'/review',headers=creds['pm'],json={'decision':'approve'}).status_code==403
 assert client.post(base+'/review',headers=creds['reviewer'],json={'decision':'approve'}).json()['reviewStage']=='lead'
 assert client.post(base+'/review',headers=creds['reviewer'],json={'decision':'approve'}).status_code==403
 assert client.post(base+'/review',headers=creds['xd'],json={'decision':'approve'}).status_code==403
 assert client.post(base+'/review',headers=creds['lead'],json={'decision':'approve'}).json()['reviewStage']=='pm'
 assert client.post(base+'/review',headers=creds['pm'],json={'decision':'approve'}).json()['status']=='done'
 history=client.get(base+'/history',headers=creds['author']).json();assert [x['stage'] for x in history]==['qa','lead','pm']
 assert len(client.get(f'/api/projects/{p}/audit',headers=creds['pm']).json())>=3
 assert client.post(base+'/execute',headers=creds['author']).status_code==501

def test_review_rejection_requires_note_and_resubmission(scenario):
 client,admin,login,r=scenario;ids,creds=setup(scenario);p=ids['A01']
 t=client.post(f'/api/projects/{p}/tasks',headers=creds['author'],json={'title':'Check BOQ quantity','dept':'qs'}).json();tid=t['id']
 root=f'/api/projects/{p}/tasks/{tid}'
 client.post(root+'/submit',headers=creds['author'],json={'summary':'Work completed, BOQ quantities checked.'})
 assert client.post(root+'/review',headers=creds['reviewer'],json={'decision':'reject','note':'bad'}).status_code==422
 response=client.post(root+'/review',headers=creds['reviewer'],json={'decision':'reject','note':'Quantity mismatch in revision R02'})
 assert response.status_code==200 and response.json()['status']=='working'
 assert client.post(root+'/submit',headers=creds['author'],json={'summary':'Corrected all quantities for revised drawing.'}).status_code==200

def test_document_storage_revisions_and_no_cross_project_download(scenario):
 client,admin,login,r=scenario;ids,creds=setup(scenario);a=ids['A01'];b=ids['B02']
 def upload(pid,data):
  return client.post(f'/api/projects/{pid}/documents',headers=admin,data={'division':'mep','category':'drawings','code':'DRW-E-001'},files={'file':('drawing.pdf',data,'application/pdf')})
 one=upload(a,b'%PDF-1.4 original');two=upload(a,b'%PDF-1.4 revised');three=upload(b,b'%PDF-1.4 other project')
 assert [x.status_code for x in [one,two,three]]==[200,200,200]
 assert [x.json()['revision'] for x in [one,two,three]]==[1,2,1]
 path=f'/api/projects/{a}/documents/{one.json()["id"]}/download'
 assert client.get(path,headers=creds['outsider']).status_code==403
 assert client.get(path,headers=creds['author']).content==b'%PDF-1.4 original'
 assert client.get(f'/api/projects/{a}/documents',headers=creds['author']).status_code==200
 assert client.post(f'/api/projects/{a}/documents',headers=creds['author'],data={'division':'construction','category':'drawings','code':'DRW-E-001'},files={'file':('drawing.pdf',b'x','application/pdf')}).status_code==403

def test_import_never_auto_approves_or_deletes_local(scenario):
 client,admin,login,r=scenario;ids,creds=setup(scenario);p=ids['A01']
 source=[{'id':'TASK-001','title':'Check LV distribution','dept':'electrical','status':'done','report':'legacy approved'},{'id':'TASK-002','title':'Check beam detail','dept':'structure'}]
 path=f'/api/projects/{p}/import-tasks'
 answer=client.post(path,headers=creds['pm'],json={'tasks':source});assert answer.status_code==200
 assert answer.json()['imported']==2
 again=client.post(path,headers=creds['pm'],json={'tasks':source});assert again.json()['imported']==0
 entries=client.get(f'/api/projects/{p}/tasks',headers=creds['pm']).json()
 assert len(entries)==2 and all(x['status']=='todo' for x in entries)

def test_agent_config_is_server_side_and_no_secret(scenario):
 client,admin,login,r=scenario;ids,creds=setup(scenario)
 x=r('/api/admin/agents/ELE',method='PUT',json={'provider':'openai','model':'model-to-be-configured','enabled':True,'monthly_budget':100000})
 assert x.status_code==200 and x.json()['executionEnabled'] is False
 profiles=r('/api/admin/agents').json();assert len(profiles)==1 and 'key' not in str(profiles).lower()
 assert client.get('/api/admin/agents',headers=creds['author']).status_code==403

def test_backend_serves_public_assets_but_not_database_or_server_code(tmp_path):
 app=create_app('sqlite:///'+str(tmp_path/'database.sqlite3'),storage_dir=tmp_path/'docs',serve_frontend=True)
 c=TestClient(app)
 assert c.get('/').status_code==200
 assert c.get('/src/portal.js').status_code==200
 assert c.get('/assets/office_xd_mep_isometric_v5_7.webp').status_code==200
 for private in ['/backend/main.py','/backend/storage/company.sqlite3','/.github/workflows/build-android-apk.yml','/.env']:
  assert c.get(private).status_code==404,private

def test_pending_queue_only_includes_approvals_current_role_can_perform(scenario):
 client,admin,login,r=scenario;ids,creds=setup(scenario);p=ids['A01']
 t=client.post(f'/api/projects/{p}/tasks',headers=creds['author'],json={'title':'Check electrical design','dept':'electrical'}).json()
 client.post(f'/api/projects/{p}/tasks/{t["id"]}/submit',headers=creds['author'],json={'summary':'Reviewed electrical single line and calculations.'})
 assert len(client.get(f'/api/projects/{p}/approvals',headers=creds['reviewer']).json())==1
 assert not client.get(f'/api/projects/{p}/approvals',headers=creds['lead']).json()
 assert not client.get(f'/api/projects/{p}/approvals',headers=creds['author']).json()
 client.post(f'/api/projects/{p}/tasks/{t["id"]}/review',headers=creds['reviewer'],json={'decision':'approve'})
 assert not client.get(f'/api/projects/{p}/approvals',headers=creds['reviewer']).json()
 assert len(client.get(f'/api/projects/{p}/approvals',headers=creds['lead']).json())==1
