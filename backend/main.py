"""V5.6-5.7 multi-project REST API.

Run: uvicorn backend.main:app --host 127.0.0.1 --port 8766
PRODUCTION: set DATABASE_URL, document storage, TLS reverse proxy, identity, backups.
This service does not execute any AI model yet.
"""
from __future__ import annotations
import hashlib, os, re, secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from .models import Base, User, SessionToken, Project, Membership, Task, Approval, Document, Audit, AgentConfig, utcnow
from .security import ROLES, PROJECT_ROLES, make_session, password_hash, verify_password

ROOT=Path(__file__).resolve().parent.parent
DIVISION_DEPTS = {
 'mep':{'electrical','hvac','plumbing','fire','bim','qs','qa'},
 'construction':{'architecture','structure','xd_bim','xd_qs','xd_planning','xd_site','xd_safety','xd_material'},
 'shared':{'director'},
}
ALLOWED_EXTENSIONS={'.pdf','.xlsx','.xls','.csv','.docx','.doc','.dwg','.dxf','.ifc','.rvt','.nwd','.png','.jpg','.jpeg','.txt','.json'}
MAX_FILE_BYTES=30*1024*1024

class LoginIn(BaseModel):
 username:str=Field(min_length=1,max_length=100)
 password:str=Field(min_length=1)
class NewUser(BaseModel):
 username:str=Field(pattern=r'^[a-zA-Z0-9_.-]{2,50}$')
 full_name:str=Field(min_length=2,max_length=160)
 password:str=Field(min_length=12,max_length=200)
class ProjectIn(BaseModel):
 code:str=Field(pattern=r'^[a-zA-Z0-9_-]{2,60}$')
 name:str=Field(min_length=3,max_length=200)
 client:str=Field(default='',max_length=200)
 location:str=Field(default='',max_length=200)
 start_date:str=''
 end_date:str=''
class MemberIn(BaseModel):
 username:str
 role:Literal['director','project_manager','mep_lead','construction_lead','qa','engineer','viewer']
 division:Literal['all','mep','construction']='all'
class TaskIn(BaseModel):
 title:str=Field(min_length=3,max_length=280)
 dept:str
 assignee:str=''
 priority:str='normal'
 doc_code:str=''
class SubmitIn(BaseModel):
 summary:str=Field(min_length=12,max_length=15000)
 findings:str=Field(default='',max_length=15000)
class ReviewIn(BaseModel):
 decision:Literal['approve','reject']
 note:str=Field(default='',max_length=15000)
class ImportIn(BaseModel):
 tasks:list[dict]=Field(default_factory=list,max_length=500)
class AgentIn(BaseModel):
 provider:Literal['none','openai','gemini']='none'
 model:str=Field(default='',max_length=100)
 enabled:bool=False
 monthly_budget:int=Field(default=0,ge=0,le=100000000)

def division_of(dept:str)->str:
 for division,ids in DIVISION_DEPTS.items():
  if dept in ids:return division
 raise HTTPException(422,'Phòng ban không hợp lệ')

def public_user(u):return {'id':u.id,'username':u.username,'name':u.full_name,'admin':u.global_role=='admin'}
def public_project(p):return {'id':p.id,'code':p.code,'name':p.name,'client':p.client,'location':p.location,'status':p.status,'startDate':p.start_date,'endDate':p.end_date}
def public_task(t):return {'id':t.id,'projectId':t.project_id,'title':t.title,'dept':t.dept,'division':division_of(t.dept),'assignee':t.assignee,'priority':t.priority,'docCode':t.doc_code,'status':t.status,'report':t.report,'findings':t.findings,'reviewStage':t.review_stage,'creatorId':t.creator_id,'submitterId':t.submitter_id,'legacyId':t.legacy_id,'updatedAt':t.updated_at.isoformat() if t.updated_at else ''}
def public_approval(a):return {'id':a.id,'taskId':a.task_id,'projectId':a.project_id,'actorId':a.actor_id,'stage':a.stage,'decision':a.decision,'note':a.note,'at':a.at.isoformat()}
def public_document(d):return {'id':d.id,'projectId':d.project_id,'division':d.division,'code':d.code,'category':d.category,'revision':d.revision,'filename':d.filename,'size':d.size,'sha256':d.sha256,'uploadedBy':d.uploaded_by,'at':d.created_at.isoformat()}

def create_app(database_url:str|None=None,storage_dir:str|Path|None=None,serve_frontend:bool=True):
    if database_url is None:database_url=os.environ.get('DATABASE_URL') or 'sqlite:///'+str(ROOT/'backend/storage/company.sqlite3')
    storage=Path(storage_dir or os.environ.get('DOCUMENT_STORAGE_DIR') or (ROOT/'backend/storage/documents')).resolve()
    storage.mkdir(parents=True,exist_ok=True)
    if database_url.startswith('sqlite:///'):
     target=Path(database_url.removeprefix('sqlite:///'))
     target.parent.mkdir(parents=True,exist_ok=True)
    engine=create_engine(database_url,connect_args={'check_same_thread':False} if database_url.startswith('sqlite:') else {},pool_pre_ping=True)
    Base.metadata.create_all(engine)
    dbmaker=sessionmaker(bind=engine,expire_on_commit=False)
    api=FastAPI(title='Công ty Xây dựng & MEP AI 3D API',version='0.5.7',docs_url='/api/docs',openapi_url='/api/openapi.json')
    cors=[v.strip() for v in os.getenv('ALLOWED_WEB_ORIGINS','').split(',') if v.strip()]
    cors.append('https://appassets.androidplatform.net')
    api.add_middleware(CORSMiddleware,allow_origins=cors,allow_methods=['GET','POST','PUT'],allow_headers=['Authorization','Content-Type'],allow_credentials=False)
    api.state.dbmaker=dbmaker
    api.state.storage=storage
    def db():
      with dbmaker() as s:yield s
    def current(authorization:Annotated[str|None,Header()]=None,s:Session=Depends(db)):
      if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Cần đăng nhập')
      digest=hashlib.sha256(authorization[7:].encode()).hexdigest()
      entry=s.scalar(select(SessionToken).where(SessionToken.token_hash==digest,SessionToken.revoked==False))
      if not entry:raise HTTPException(401,'Phiên đăng nhập không hợp lệ')
      deadline=entry.expires_at.replace(tzinfo=timezone.utc) if entry.expires_at.tzinfo is None else entry.expires_at
      if deadline<=utcnow():raise HTTPException(401,'Phiên đăng nhập đã hết hạn')
      user=s.get(User,entry.user_id)
      if user is None or not user.active:raise HTTPException(401,'Tài khoản không hoạt động')
      return user
    def is_admin(user):return user.global_role=='admin'
    def role_for(s,user,project_id):
      if is_admin(user):return ('admin','all')
      m=s.scalar(select(Membership).where(Membership.user_id==user.id,Membership.project_id==project_id))
      if m is None:raise HTTPException(403,'Không được truy cập dự án này')
      return m.role,m.division
    def access(s,user,project_id,action='read',dept=None):
      if s.get(Project,project_id) is None:raise HTTPException(404,'Không tìm thấy dự án')
      role,division=role_for(s,user,project_id)
      if dept:
       requested=division_of(dept)
       if division!='all' and requested not in (division,'shared'):raise HTTPException(403,'Ngoài phạm vi bộ môn được giao')
      if action in ('write','import') and role not in ('admin','director','project_manager','mep_lead','construction_lead','qa','engineer'):
       raise HTTPException(403,'Không có quyền chỉnh sửa')
      if action=='manage' and role not in ('admin','director','project_manager'):
       raise HTTPException(403,'Không có quyền quản trị dự án')
      return role,division
    def audit(s,user_id,project_id,action,target,details=''):
      s.add(Audit(actor_id=user_id,project_id=project_id,action=action,target=str(target),details=details[:3000]))
    def filter_tasks(s,user,project_id):
      _,division=access(s,user,project_id)
      tasks=s.scalars(select(Task).where(Task.project_id==project_id).order_by(Task.id.desc())).all()
      return [t for t in tasks if division=='all' or division_of(t.dept) in (division,'shared')]
    def task_for(s,user,project_id,task_id):
      t=s.get(Task,task_id)
      if t is None or t.project_id!=project_id:raise HTTPException(404,'Không tìm thấy nhiệm vụ')
      access(s,user,project_id,dept=t.dept)
      return t

    @api.get('/api/health')
    def health():return {'status':'ok','version':'V5.7','database':'configured','agentExecution':'disabled'}
    @api.post('/api/auth/login')
    def login(body:LoginIn,s:Session=Depends(db)):
      user=s.scalar(select(User).where(User.username==body.username))
      if user is None or not user.active or not verify_password(body.password,user.password_hash):
       raise HTTPException(401,'Sai tài khoản hoặc mật khẩu')
      token=make_session(s,user.id)
      audit(s,user.id,None,'auth.login',user.username);s.commit()
      return {'token':token,'user':public_user(user),'expiresIn':8*60*60}
    @api.get('/api/auth/me')
    def me(user:User=Depends(current)):return public_user(user)
    @api.post('/api/auth/logout')
    def logout(authorization:Annotated[str|None,Header()]=None,s:Session=Depends(db),user:User=Depends(current)):
      digest=hashlib.sha256(authorization[7:].encode()).hexdigest()
      x=s.scalar(select(SessionToken).where(SessionToken.token_hash==digest,SessionToken.user_id==user.id))
      if x:x.revoked=True
      audit(s,user.id,None,'auth.logout',user.username);s.commit()
      return {'ok':True}
    @api.post('/api/admin/users')
    def new_user(body:NewUser,s:Session=Depends(db),user:User=Depends(current)):
      if not is_admin(user):raise HTTPException(403,'Chỉ quản trị hệ thống tạo tài khoản')
      if s.scalar(select(User).where(User.username==body.username)):raise HTTPException(409,'Tài khoản đã tồn tại')
      u=User(username=body.username,full_name=body.full_name,password_hash=password_hash(body.password))
      s.add(u);s.flush();audit(s,user.id,None,'user.create',u.username);s.commit()
      return public_user(u)
    @api.get('/api/admin/users')
    def users(s:Session=Depends(db),user:User=Depends(current)):
      if not is_admin(user):raise HTTPException(403,'Cần quyền quản trị')
      return [public_user(x) for x in s.scalars(select(User).order_by(User.id)).all()]
    @api.get('/api/projects')
    def projects(s:Session=Depends(db),user:User=Depends(current)):
      items=s.scalars(select(Project).order_by(Project.id.desc())).all()
      return [public_project(p) for p in items if is_admin(user) or s.scalar(select(Membership.id).where(Membership.project_id==p.id,Membership.user_id==user.id)) is not None]
    @api.post('/api/projects')
    def new_project(body:ProjectIn,s:Session=Depends(db),user:User=Depends(current)):
      if not is_admin(user):raise HTTPException(403,'Chỉ quản trị hệ thống tạo dự án mới')
      if s.scalar(select(Project).where(Project.code==body.code.upper())):raise HTTPException(409,'Mã dự án đã tồn tại')
      p=Project(code=body.code.upper(),name=body.name,client=body.client,location=body.location,start_date=body.start_date,end_date=body.end_date,created_by=user.id)
      s.add(p);s.flush();audit(s,user.id,p.id,'project.create',p.code);s.commit()
      return public_project(p)
    @api.get('/api/projects/{pid}/summary')
    def summary(pid:int,s:Session=Depends(db),user:User=Depends(current)):
      tasks=filter_tasks(s,user,pid)
      _,scope=role_for(s,user,pid)
      query=select(func.count(Document.id)).where(Document.project_id==pid)
      if scope!='all':query=query.where(Document.division==scope)
      docs_count=s.scalar(query) or 0
      return {'project':public_project(s.get(Project,pid)),'tasks':len(tasks),'pending':sum(t.status=='review' for t in tasks),'done':sum(t.status=='done' for t in tasks),'documents':docs_count}
    @api.get('/api/projects/{pid}/members')
    def members(pid:int,s:Session=Depends(db),user:User=Depends(current)):
      access(s,user,pid)
      membership=s.scalars(select(Membership).where(Membership.project_id==pid)).all()
      return [{'username':s.get(User,m.user_id).username,'name':s.get(User,m.user_id).full_name,'role':m.role,'division':m.division} for m in membership]
    @api.post('/api/projects/{pid}/members')
    def add_member(pid:int,body:MemberIn,s:Session=Depends(db),user:User=Depends(current)):
      access(s,user,pid,'manage')
      target=s.scalar(select(User).where(User.username==body.username))
      if target is None:raise HTTPException(404,'Chưa có tài khoản này')
      membership=s.scalar(select(Membership).where(Membership.project_id==pid,Membership.user_id==target.id))
      if membership:
       membership.role=body.role;membership.division=body.division
      else:s.add(Membership(project_id=pid,user_id=target.id,role=body.role,division=body.division))
      audit(s,user.id,pid,'member.upsert',body.username,body.role+'/'+body.division);s.commit()
      return {'ok':True}
    @api.get('/api/projects/{pid}/tasks')
    def tasks(pid:int,s:Session=Depends(db),user:User=Depends(current)):
      return [public_task(t) for t in filter_tasks(s,user,pid)]
    @api.post('/api/projects/{pid}/tasks')
    def new_task(pid:int,body:TaskIn,s:Session=Depends(db),user:User=Depends(current)):
      access(s,user,pid,'write',body.dept)
      t=Task(project_id=pid,title=body.title,dept=body.dept,assignee=body.assignee,doc_code=body.doc_code,priority=body.priority,creator_id=user.id)
      s.add(t);s.flush();audit(s,user.id,pid,'task.create',t.id);s.commit()
      return public_task(t)
    @api.post('/api/projects/{pid}/tasks/{tid}/submit')
    def submit(pid:int,tid:int,body:SubmitIn,s:Session=Depends(db),user:User=Depends(current)):
      t=task_for(s,user,pid,tid)
      role,_=access(s,user,pid,'write',t.dept)
      if t.creator_id!=user.id and role not in ('admin','director','project_manager','mep_lead','construction_lead'):
       raise HTTPException(403,'Chỉ người tạo hoặc quản lý được gửi báo cáo nhiệm vụ')
      if t.status not in ('todo','working'):raise HTTPException(409,'Chỉ nhiệm vụ đang làm mới được gửi duyệt')
      t.report=body.summary.strip();t.findings=body.findings.strip();t.submitter_id=user.id;t.status='review';t.review_stage='qa'
      audit(s,user.id,pid,'task.submit',tid,'review_stage=qa');s.commit()
      return public_task(t)
    def reviewer_is_allowed(s,user,task):
      role,_=role_for(s,user,task.project_id)
      if user.id in (task.creator_id,task.submitter_id):return False
      expected={'qa':{'qa','admin'},'lead':{'mep_lead' if division_of(task.dept)=='mep' else 'construction_lead' if division_of(task.dept)=='construction' else 'director','admin'},'pm':{'project_manager','director','admin'}}.get(task.review_stage,set())
      if role not in expected:return False
      already=s.scalars(select(Approval.actor_id).where(Approval.task_id==task.id,Approval.decision=='approve')).all()
      return user.id not in already
    @api.get('/api/projects/{pid}/approvals')
    def approvals(pid:int,s:Session=Depends(db),user:User=Depends(current)):
      access(s,user,pid)
      return [public_task(t) for t in filter_tasks(s,user,pid) if t.status=='review' and reviewer_is_allowed(s,user,t)]
    @api.get('/api/projects/{pid}/tasks/{tid}/history')
    def approval_history(pid:int,tid:int,s:Session=Depends(db),user:User=Depends(current)):
      task_for(s,user,pid,tid)
      return [public_approval(x) for x in s.scalars(select(Approval).where(Approval.task_id==tid,Approval.project_id==pid).order_by(Approval.id)).all()]
    @api.post('/api/projects/{pid}/tasks/{tid}/review')
    def review(pid:int,tid:int,body:ReviewIn,s:Session=Depends(db),user:User=Depends(current)):
      t=task_for(s,user,pid,tid)
      if t.status!='review' or not t.report:raise HTTPException(409,'Không có báo cáo hợp lệ đang chờ duyệt')
      role,division=role_for(s,user,pid)
      if user.id in (t.creator_id,t.submitter_id):raise HTTPException(403,'Người tạo/gửi không được tự duyệt')
      # One person may not approve more than one stage of the same submission.
      prev=s.scalars(select(Approval).where(Approval.task_id==tid,Approval.decision=='approve')).all()
      if any(x.actor_id==user.id for x in prev):raise HTTPException(403,'Không được duyệt hai cấp trên cùng hồ sơ')
      stage=t.review_stage
      required={'qa':{'qa','admin'},'lead':{'mep_lead' if division_of(t.dept)=='mep' else 'construction_lead' if division_of(t.dept)=='construction' else 'director','admin'},'pm':{'project_manager','director','admin'}}[stage]
      if role not in required:raise HTTPException(403,'Chưa có quyền duyệt cấp '+stage)
      if body.decision=='reject' and len(body.note.strip())<5:raise HTTPException(422,'Phải ghi lý do trả lại ít nhất 5 ký tự')
      a=Approval(task_id=t.id,project_id=pid,actor_id=user.id,stage=stage,decision=body.decision,note=body.note)
      s.add(a)
      if body.decision=='reject':t.status='working';t.review_stage='qa'
      else:
       next_stage={'qa':'lead','lead':'pm','pm':None}[stage]
       if next_stage:t.review_stage=next_stage
       else:t.status='done'
      audit(s,user.id,pid,'approval.'+body.decision,t.id,'stage='+stage);s.commit()
      return public_task(t)
    @api.post('/api/projects/{pid}/import-tasks')
    def import_tasks(pid:int,body:ImportIn,s:Session=Depends(db),user:User=Depends(current)):
      access(s,user,pid,'manage')
      imported=0;skipped=0
      for row in body.tasks:
       legacy=str(row.get('id',''))[:80];title=str(row.get('title','')).strip()[:280];dept=str(row.get('dept',''))
       if not legacy or len(title)<3 or dept not in DIVISION_DEPTS['mep']|DIVISION_DEPTS['construction']|DIVISION_DEPTS['shared']:
        skipped+=1;continue
       if s.scalar(select(Task.id).where(Task.project_id==pid,Task.legacy_id==legacy)):
        skipped+=1;continue
       t=Task(project_id=pid,legacy_id=legacy,title=title,dept=dept,assignee=str(row.get('assignee',''))[:120],doc_code=str(row.get('docCode',''))[:120],priority=str(row.get('priority',''))[:30],status='todo',creator_id=user.id)
       s.add(t);imported+=1
      audit(s,user.id,pid,'tasks.import',pid,f'imported={imported};skipped={skipped}');s.commit()
      return {'imported':imported,'skipped':skipped,'note':'Nhiệm vụ cũ được đưa về chờ xử lý; hồ sơ nhị phân chưa được nhập.'}
    @api.get('/api/projects/{pid}/documents')
    def docs(pid:int,s:Session=Depends(db),user:User=Depends(current)):
      _,div=access(s,user,pid)
      entries=s.scalars(select(Document).where(Document.project_id==pid).order_by(Document.id.desc())).all()
      return [public_document(d) for d in entries if div=='all' or d.division==div]
    @api.post('/api/projects/{pid}/documents')
    async def add_doc(pid:int,division:Annotated[str,Form()],category:Annotated[str,Form()],code:Annotated[str,Form()],file:UploadFile=File(),s:Session=Depends(db),user:User=Depends(current)):
      role,allowed=access(s,user,pid,'write')
      if division not in ('mep','construction') or (allowed!='all' and allowed!=division):raise HTTPException(403,'Không có quyền tải hồ sơ lĩnh vực này')
      code=code.strip().upper()
      if not re.fullmatch(r'[A-Z0-9_-]{2,100}',code):raise HTTPException(422,'Mã hồ sơ không hợp lệ')
      filename=Path(file.filename or '').name
      if not filename or Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:raise HTTPException(422,'Loại tệp chưa được cho phép')
      content=await file.read(MAX_FILE_BYTES+1)
      if len(content)>MAX_FILE_BYTES:raise HTTPException(413,'Giới hạn 30 MB mỗi tệp')
      rev=s.scalar(select(func.max(Document.revision)).where(Document.project_id==pid,Document.division==division,Document.code==code)) or 0
      key=f'{pid}/{secrets.token_hex(18)}{Path(filename).suffix.lower()}'
      dst=(storage/key).resolve()
      if not dst.is_relative_to(storage):raise HTTPException(400,'Đường dẫn không hợp lệ')
      dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(content)
      d=Document(project_id=pid,division=division,code=code,category=category[:50],revision=rev+1,filename=filename[:255],content_type=file.content_type or 'application/octet-stream',size=len(content),sha256=hashlib.sha256(content).hexdigest(),storage_key=key,uploaded_by=user.id)
      s.add(d);s.flush();audit(s,user.id,pid,'document.upload',d.id,f'{code}/R{d.revision} sha256={d.sha256}');s.commit()
      return public_document(d)
    @api.get('/api/projects/{pid}/documents/{did}/download')
    def download(pid:int,did:int,s:Session=Depends(db),user:User=Depends(current)):
      _,div=access(s,user,pid)
      d=s.get(Document,did)
      if not d or d.project_id!=pid:raise HTTPException(404,'Không tìm thấy hồ sơ')
      if div!='all' and div!=d.division:raise HTTPException(403,'Không có quyền tải hồ sơ')
      path=(storage/d.storage_key).resolve()
      if not path.is_relative_to(storage) or not path.exists():raise HTTPException(404,'Không tìm thấy tệp gốc')
      audit(s,user.id,pid,'document.download',d.id);s.commit()
      return FileResponse(str(path),media_type='application/octet-stream',filename=d.filename)
    @api.get('/api/projects/{pid}/audit')
    def logs(pid:int,s:Session=Depends(db),user:User=Depends(current)):
      role,_=access(s,user,pid)
      if role not in ('admin','director','project_manager','qa','mep_lead','construction_lead'):
       raise HTTPException(403,'Không có quyền xem nhật ký')
      entries=s.scalars(select(Audit).where(Audit.project_id==pid).order_by(Audit.id.desc()).limit(250)).all()
      return [{'id':a.id,'actorId':a.actor_id,'action':a.action,'target':a.target,'details':a.details,'at':a.at.isoformat()} for a in entries]
    @api.get('/api/admin/agents')
    def agents(s:Session=Depends(db),user:User=Depends(current)):
      if not is_admin(user):raise HTTPException(403,'Cần quyền quản trị')
      return [{'agentId':c.agent_id,'provider':c.provider,'model':c.model,'enabled':c.enabled,'monthlyBudget':c.monthly_budget} for c in s.scalars(select(AgentConfig)).all()]
    @api.put('/api/admin/agents/{agent_id}')
    def config_agent(agent_id:str,body:AgentIn,s:Session=Depends(db),user:User=Depends(current)):
      if not is_admin(user):raise HTTPException(403,'Cần quyền quản trị')
      if not re.fullmatch(r'[A-Z0-9]{2,6}',agent_id):raise HTTPException(422,'Mã nhân viên không hợp lệ')
      c=s.scalar(select(AgentConfig).where(AgentConfig.agent_id==agent_id))
      if c is None:c=AgentConfig(agent_id=agent_id);s.add(c)
      c.provider=body.provider;c.model=body.model;c.enabled=body.enabled;c.monthly_budget=body.monthly_budget
      audit(s,user.id,None,'agent.config',agent_id,'provider='+body.provider+'; no API keys stored');s.commit()
      return {'agentId':agent_id,'saved':True,'executionEnabled':False,'note':'AI execution remains disabled until separately implemented and verified.'}
    @api.post('/api/projects/{pid}/tasks/{tid}/execute')
    def execute_agent(pid:int,tid:int,s:Session=Depends(db),user:User=Depends(current)):
      task_for(s,user,pid,tid);access(s,user,pid,'write')
      raise HTTPException(501,'Chưa triển khai công cụ AI thật; không mô phỏng kết quả như đã thực thi')

    if serve_frontend:
      # Deliberately NEVER expose repository root: it contains server source,
      # database and possibly private configuration. Whitelist public assets.
      @api.get('/')
      @api.get('/index.html')
      def home():return FileResponse(str(ROOT/'index.html'),media_type='text/html')
      for public in ('src','assets','data','versions','project_templates'):
       api.mount('/'+public,StaticFiles(directory=str(ROOT/public),html=False),name='public-'+public)
    return api

app=create_app()
