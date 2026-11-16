/* V5.7.3 — Offline-first projects, documents and internal review.
 * No login, permission checks or server calls in this mode.
 * The original authenticated backend remains in src/portal.js for future deployment.
 */
import {AGENTS,DEPARTMENTS,CATEGORIES} from './core/config.js';
import {listDocuments,addDocument,downloadDocument} from './core/documents.js';

export const WORKSPACE_KEY='xd-mep-local-workspace-v573';
const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stamp=()=>new Date().toISOString();
const uid=()=>globalThis.crypto?.randomUUID?.()||'id-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
const docProject=d=>String(d.project||'');
const divisionOf=dept=>DEPARTMENTS.find(d=>d.id===dept)?.division||'mep';
const typeChoices=[['all','Toàn công ty','Whole company'],['mep','Cơ điện MEP','MEP'],['construction','Xây dựng','Construction']];
const statusMap={todo:['Chờ xử lý','To do'],working:['Đang thực hiện','In progress'],review:['Chờ duyệt','Pending review'],done:['Hoàn thành','Completed']};
function getSafe(){try{const value=JSON.parse(localStorage.getItem(WORKSPACE_KEY)||'null');if(value&&Array.isArray(value.projects)&&Array.isArray(value.tasks)&&Array.isArray(value.events))return value;}catch{}return {version:1,projects:[],tasks:[],events:[],selectedProjectId:null,legacyImported:false};}
export function createProjectInStore(store,data){
 const code=String(data.code||'').trim().toUpperCase();
 const name=String(data.name||'').trim();
 if(!/^[A-Z0-9_-]{2,60}$/.test(code))throw Error('Mã dự án chỉ gồm chữ, số, dấu gạch nối và gạch dưới (2–60 ký tự)');
 if(name.length<2)throw Error('Tên dự án quá ngắn');
 if(store.projects.some(p=>p.code.toUpperCase()===code))throw Error('Mã dự án đã tồn tại');
 const item={id:uid(),code,name,client:String(data.client||'').trim(),location:String(data.location||'').trim(),division:data.division||'all',createdAt:stamp()};
 store.projects.unshift(item);store.selectedProjectId=item.id;return item;
}
export function addTaskInStore(store,data){
 const project=store.projects.find(p=>p.id===data.projectId);if(!project)throw Error('Cần chọn dự án');
 const title=String(data.title||'').trim();if(title.length<3)throw Error('Nội dung công việc quá ngắn');
 if(!DEPARTMENTS.some(d=>d.id===data.dept))throw Error('Bộ phận không hợp lệ');
 const item={id:uid(),code:`CV-${Date.now().toString(36).toUpperCase().slice(-8)}`,projectId:project.id,title,dept:data.dept,
  division:divisionOf(data.dept),assignee:String(data.assignee||'').trim()||AGENTS.find(a=>a.dept===data.dept)?.id||'PM',
  docCode:String(data.docCode||'').trim(),status:'todo',createdAt:stamp(),reviewHistory:[]};
 store.tasks.unshift(item);return item;
}
export function submitTaskInStore(store,id,{summary,findings=''}){
 const task=store.tasks.find(t=>t.id===id);if(!task)throw Error('Không tìm thấy nhiệm vụ');
 const report=String(summary||'').trim();if(report.length<12)throw Error('Báo cáo cần ít nhất 12 ký tự');
 task.report=report;task.findings=String(findings||'').trim();task.status='review';task.submittedAt=stamp();
 task.reviewHistory??=[];task.reviewHistory.push({at:stamp(),decision:'submitted',note:report});return task;
}
export function reviewTaskInStore(store,id,{decision,reviewer,comment=''}){
 const task=store.tasks.find(t=>t.id===id);if(!task||task.status!=='review')throw Error('Nhiệm vụ không ở trạng thái chờ duyệt');
 if(!['approve','reject'].includes(decision))throw Error('Quyết định không hợp lệ');
 if(String(reviewer||'').trim().length<2)throw Error('Nhập tên người kiểm tra');
 if(decision==='approve'&&String(task.report||'').trim().length<12)throw Error('Chưa có báo cáo đủ nội dung để duyệt');
 if(decision==='reject'&&String(comment||'').trim().length<5)throw Error('Cần ghi rõ lý do trả lại');
 task.status=decision==='approve'?'done':'working';task.reviewHistory??=[];
 task.reviewHistory.push({at:stamp(),decision,reviewer:String(reviewer).trim(),note:String(comment).trim()});return task;
}

export class LocalProjectPortal {
 constructor({getLanguage,getLegacyState,onChange,notify}){
  this.getLanguage=getLanguage;this.getLegacyState=getLegacyState;this.onChange=onChange;this.notify=notify;
  this.store=getSafe();this.docs=[];this.projectId=this.store.selectedProjectId||null;this.currentProject=null;
  this.user={name:'Thiết bị hiện tại',local:true};this.projects=[];this.tasks=[];this.audit=[];this.summary={};
  this._migrateLegacy();this._sync();this._loadDocs();
 }
 get en(){return this.getLanguage()==='en'}
 t(vi,en){return this.en?en:vi}
 _migrateLegacy(){
  if(this.store.legacyImported)return;
  const legacy=(this.getLegacyState()?.tasks||[]).filter(t=>t&&t.title&&t.dept);
  if(legacy.length){
   const p=createProjectInStore(this.store,{code:'LEGACY-LOCAL',name:'Dữ liệu công việc cũ',division:'all'});
   for(const t of legacy){
    const copy={...t,id:uid(),code:t.id||'CV-CU',projectId:p.id,division:divisionOf(t.dept),
     status:['todo','working','review','done'].includes(t.status)?t.status:'todo',reviewHistory:t.reviewHistory||[]};
    if(t.reviewSubmission?.summary)copy.report=t.reviewSubmission.summary;
    this.store.tasks.push(copy);
   }
  }
  this.store.legacyImported=true;this._save();
 }
 _save(){localStorage.setItem(WORKSPACE_KEY,JSON.stringify(this.store));}
 _sync(){
  this.projects=this.store.projects;this.projectId=this.store.selectedProjectId||this.projects[0]?.id||null;
  this.currentProject=this.projects.find(p=>p.id===this.projectId)||null;
  this.tasks=this.store.tasks.filter(t=>t.projectId===this.projectId);
  this.audit=this.store.events.filter(e=>e.projectId===this.projectId);
  this.summary=Object.fromEntries(this.projects.map(p=>{
   const ts=this.store.tasks.filter(t=>t.projectId===p.id);return [p.id,{tasks:ts.length,pending:ts.filter(t=>t.status==='review').length,documents:this.docs.filter(d=>docProject(d)===p.code).length}];
  }));
 }
 async _loadDocs(){try{this.docsAll=await listDocuments()}catch{this.docsAll=[];}this.docs=this.docsAll.filter(d=>docProject(d)===this.currentProject?.code);this._sync();this.onChange?.()}
 _change(){this._save();this._sync();this.onChange?.()}
 _event(action,details){this.store.events.unshift({id:uid(),projectId:this.store.selectedProjectId||this.projectId,action,details,at:stamp()});this.store.events=this.store.events.slice(0,500);}
 changeProject(id){if(!this.projects.some(p=>p.id===id))throw Error('Không tìm thấy dự án');this.store.selectedProjectId=id;this.projectId=id;this.docs=(this.docsAll||[]).filter(d=>docProject(d)===this.projects.find(p=>p.id===id)?.code);this._sync();this._save();this.onChange();}
 labelStatus(status){const v=statusMap[status]||[status,status];return v[this.en?1:0]}
 deptOptions(){return DEPARTMENTS.map(d=>`<option value="${escape(d.id)}">${escape(d.name)}</option>`).join('')}
 projectHeader(){return `<div class="portal-project-picker"><label>${this.t('Dự án đang chọn','Selected project')}<select id="localSelectProject"><option value="">${this.t('— Chưa chọn dự án —','— Select a project —')}</option>${this.projects.map(p=>`<option value="${escape(p.id)}" ${p.id===this.projectId?'selected':''}>${escape(p.code)} · ${escape(p.name)}</option>`).join('')}</select></label><span class="portal-project-total">${this.projects.length} ${this.t('dự án trên thiết bị','local projects')}</span></div>`}
 projectForm(){return `<form class="panel padded portal-form" id="localCreateProject"><h3>${this.t('Tạo dự án mới','New project')}</h3><label>${this.t('Mã dự án','Project code')}<input name="code" required placeholder="DA-001" maxlength="60" pattern="[A-Za-z0-9_-]{2,60}"></label><label>${this.t('Tên dự án','Project name')}<input name="name" minlength="2" required></label><label>${this.t('Chủ đầu tư','Client')}<input name="client"></label><label>${this.t('Địa điểm','Location')}<input name="location"></label><label>${this.t('Phạm vi','Scope')}<select name="division">${typeChoices.map(([id,vi,en])=>`<option value="${id}">${this.t(vi,en)}</option>`).join('')}</select></label><button type="submit" class="btn primary">＋ ${this.t('Tạo dự án','Create project')}</button></form>`}
 taskForm(){return `<form id="localCreateTask" class="panel padded portal-form"><h3>${this.t('Giao công việc mới','New task')}</h3><label>${this.t('Nội dung công việc','Task title')}<input name="title" minlength="3" required></label><label>${this.t('Phòng ban','Department')}<select name="dept">${this.deptOptions()}</select></label><label>${this.t('Người/Agent phụ trách','Assigned person / agent')}<select name="assignee"><option value="">${this.t('Theo phòng ban','Default by department')}</option>${AGENTS.map(a=>`<option value="${escape(a.id)}">${escape(a.name)}</option>`).join('')}</select></label><label>${this.t('Mã hồ sơ liên quan','Related document code')}<input name="docCode"></label><button type="submit" class="btn primary">＋ ${this.t('Tạo nhiệm vụ','Create task')}</button></form>`}
 projectCards(){return `<div class="portal-summary-grid">${this.projects.map(p=>{const sum=this.summary[p.id]||{};return `<button type="button" data-local-project="${escape(p.id)}" class="portal-project-card ${p.id===this.projectId?'active':''}"><strong>${escape(p.name)}</strong><small>${escape(p.code)} · ${escape(p.client||'')}</small><div class="portal-project-numbers"><span>${sum.tasks||0} ${this.t('việc','tasks')}</span><span>${sum.pending||0} ${this.t('chờ duyệt','pending')}</span><span>${sum.documents||0} ${this.t('hồ sơ','files')}</span></div></button>`}).join('')||`<div class="empty-state">${this.t('Chưa có dự án. Tạo dự án đầu tiên để bắt đầu.','No projects yet. Create your first project to begin.')}</div>`}</div>`}
 taskRows(){return `<section class="panel padded"><div class="panel-heading"><h3>${this.t('Công việc dự án','Project tasks')}</h3><span class="mini-label">${this.tasks.length}</span></div><div class="portal-tasks">${this.tasks.map(t=>`<article class="portal-task"><div class="portal-task-head"><div><strong>${escape(t.title)}</strong><small>${escape(t.code||t.id)} · ${escape(DEPARTMENTS.find(d=>d.id===t.dept)?.name||t.dept)} · ${escape(t.assignee||'')}</small></div><span class="portal-pill ${t.status==='review'?'review':t.status==='done'?'done':''}">${escape(this.labelStatus(t.status))}</span></div>${t.docCode?`<p>${this.t('Hồ sơ','Document')}: ${escape(t.docCode)}</p>`:''}${t.report?`<div class="portal-report"><strong>${this.t('Báo cáo','Report')}</strong><p>${escape(t.report)}</p></div>`:''}${t.status==='todo'?`<button class="btn outline small" data-local-start="${escape(t.id)}">${this.t('Bắt đầu xử lý','Start work')}</button>`:''}${t.status==='todo'||t.status==='working'?`<details><summary>${this.t('Gửi báo cáo để phê duyệt','Submit report for review')}</summary><form class="portal-form" data-local-submit="${escape(t.id)}"><label>${this.t('Báo cáo kết quả','Result summary')}<textarea name="summary" required minlength="12"></textarea></label><label>${this.t('Phát hiện / lưu ý','Findings / notes')}<textarea name="findings"></textarea></label><button class="btn primary" type="submit">${this.t('Gửi phê duyệt','Submit for review')}</button></form></details>`:''}${t.status==='review'?`<button type="button" class="btn outline small" data-local-open-review="${escape(t.id)}">${this.t('Xem và duyệt','Review details')}</button>`:''}</article>`).join('')||`<div class="empty-state">${this.t('Dự án chưa có công việc.','No tasks in this project.')}</div>`}</div></section>`}
 approvalsPage(){return `${this.projectHeader()}<section class="panel padded portal-approval-page"><h2>${this.t('Chờ phê duyệt nội bộ','Local approval queue')}</h2><p class="footnote">${this.t('Chưa có xác thực người duyệt. Quyết định chỉ có giá trị quản lý nội bộ trên thiết bị, không thay thế chữ ký hoặc phê duyệt pháp lý.','Reviewers are not authenticated. These are local workflow records, not legally binding signatures or approvals.')}</p>${this.tasks.filter(t=>t.status==='review').map(t=>`<article class="portal-review"><div class="portal-task-head"><div><strong>${escape(t.title)}</strong><small>${escape(t.code||t.id)} · ${escape(t.assignee)}</small></div><span class="portal-pill review">${this.t('Chờ duyệt','Pending')}</span></div><div class="portal-report"><strong>${this.t('Báo cáo kết quả','Result report')}</strong><p>${escape(t.report||'')}</p><p>${escape(t.findings||'')}</p><small>${this.t('Mã hồ sơ','Document code')}: ${escape(t.docCode||'—')}</small></div><form class="portal-form" data-local-review="${escape(t.id)}"><label>${this.t('Tên người kiểm tra','Reviewer name')}<input name="reviewer" minlength="2" required></label><label>${this.t('Nhận xét','Comments')}<textarea name="comment" placeholder="${this.t('Nhập lý do khi trả lại','Enter reason when returning')}"></textarea></label><div class="portal-review-actions"><button type="button" class="btn primary" data-local-decision="approve">✓ ${this.t('Phê duyệt','Approve')}</button><button type="button" class="btn outline" data-local-decision="reject">↶ ${this.t('Trả lại','Return')}</button></div></form><details><summary>${this.t('Lịch sử xét duyệt','Review history')}</summary>${(t.reviewHistory||[]).map(h=>`<p>${escape(h.at)} · ${escape(h.reviewer||'')} · ${escape(h.decision)} · ${escape(h.note||'')}</p>`).join('')||'—'}</details></article>`).join('')||`<div class="empty-state">${this.t('Không có công việc chờ duyệt.','Nothing is pending approval.')}</div>`}</section>`}
 docsPage(){return `${this.projectHeader()}<section class="panel padded"><h2>${this.t('Hồ sơ theo dự án','Project documents')}</h2><p class="footnote">${this.t('Tệp được lưu trong IndexedDB của thiết bị. Hãy sao lưu tệp gốc trước khi xóa dữ liệu ứng dụng.','Files are stored in this device’s IndexedDB. Back up originals before clearing app data.')}</p><div class="portal-document-list">${this.docs.map(d=>`<div class="portal-document"><span>${escape(d.code)} · R${String(d.revision||1).padStart(2,'0')} · ${escape(d.filename)}</span><button type="button" class="btn outline small" data-local-download="${escape(d.id)}">↓ ${this.t('Tải tệp','Download')}</button></div>`).join('')||`<p>${this.t('Chưa có hồ sơ cho dự án này.','No documents in this project yet.')}</p>`}</div><form class="portal-form portal-upload" id="localUploadDocument"><label>${this.t('Tệp hồ sơ','Document file')}<input type="file" name="file" required></label><label>${this.t('Loại hồ sơ','Category')}<select name="category">${CATEGORIES.map(c=>`<option value="${escape(c.id)}">${escape(c.title)}</option>`).join('')}</select></label><label>${this.t('Lĩnh vực','Division')}<select name="division"><option value="mep">MEP</option><option value="construction">${this.t('Xây dựng','Construction')}</option></select></label><label>${this.t('Mã hồ sơ','Document code')}<input name="code" placeholder="DRW-E-001"></label><label>${this.t('Mô tả thay đổi','Change description')}<input name="description"></label><button type="submit" class="btn primary">↑ ${this.t('Lưu hồ sơ','Save document')}</button></form></section>`}
 projectPage(){return `${this.projectHeader()}${this.projectCards()}<div class="portal-section-grid">${this.projectForm()}</div>`}
 taskPage(){return `${this.projectHeader()}${this.currentProject?`<div class="portal-section-grid">${this.taskForm()}</div>${this.taskRows()}`:`<div class="empty-state">${this.t('Tạo hoặc chọn dự án trong Quản lý dự án.','Create or select a project under Project Management.')}</div>`}`}
 activityPage(){return `${this.projectHeader()}<section class="panel padded"><h2>${this.t('Nhật ký hoạt động trên thiết bị','Local activity log')}</h2><p class="footnote">${this.t('Nhật ký có thể bị chỉnh sửa trên thiết bị, không phải nhật ký kiểm toán bảo mật.','This device log is editable and is not a tamper-proof security audit trail.')}</p>${this.audit.map(e=>`<div class="portal-document"><strong>${escape(e.action)}</strong><span>${escape(e.at)} · ${escape(e.details||'')}</span></div>`).join('')||`<p>${this.t('Chưa có hoạt động.','No activities yet.')}</p>`}</section>`}
 render(kind){return kind==='reviews'?this.approvalsPage():kind==='documents'?this.docsPage():kind==='tasks'?this.taskPage():kind==='activity'?this.activityPage():this.projectPage()}
 async run(fn){try{await fn();this._change()}catch(e){this.notify(e.message,true)}}
 bind(root){
  const on=(sel,event,handler)=>root.querySelector(sel)?.addEventListener(event,handler);
  on('#localSelectProject','change',e=>{if(e.target.value)this.changeProject(e.target.value)});
  root.querySelectorAll('[data-local-project]').forEach(b=>b.onclick=()=>this.changeProject(b.dataset.localProject));
  on('#localCreateProject','submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));this.run(()=>{createProjectInStore(this.store,data);this._event('project.create',data.code);this.notify(this.t('Đã tạo dự án','Project created'))})});
  on('#localCreateTask','submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));this.run(()=>{const t=addTaskInStore(this.store,{...data,projectId:this.projectId});this._event('task.create',t.title);this.notify(this.t('Đã giao việc','Task created'))})});
  root.querySelectorAll('[data-local-start]').forEach(b=>b.onclick=()=>this.run(()=>{const t=this.store.tasks.find(t=>t.id===b.dataset.localStart);if(t){t.status='working';this._event('task.start',t.title)}}));
  root.querySelectorAll('[data-local-submit]').forEach(f=>f.addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(f));this.run(()=>{const t=submitTaskInStore(this.store,f.dataset.localSubmit,data);this._event('task.submit',t.title);this.notify(this.t('Đã gửi duyệt','Submitted for review'))})}));
  root.querySelectorAll('[data-local-open-review]').forEach(b=>b.onclick=()=>this.notify(this.t('Mở mục Chờ phê duyệt ở menu','Open Pending Approvals from the menu')));
  root.querySelectorAll('[data-local-review]').forEach(f=>f.querySelectorAll('[data-local-decision]').forEach(b=>b.addEventListener('click',()=>{const data=Object.fromEntries(new FormData(f));this.run(()=>{const t=reviewTaskInStore(this.store,f.dataset.localReview,{...data,decision:b.dataset.localDecision});this._event('task.review',`${t.title} · ${b.dataset.localDecision}`);this.notify(this.t('Đã lưu quyết định nội bộ','Local decision recorded'))})})));
  on('#localUploadDocument','submit',e=>{e.preventDefault();const f=new FormData(e.currentTarget);this.run(async()=>{const file=f.get('file');const doc=await addDocument({file,category:f.get('category'),code:f.get('code'),division:f.get('division'),description:f.get('description'),project:this.currentProject.code});this._event('document.upload',`${doc.code} R${doc.revision}`);await this._loadDocs();this.notify(this.t('Đã lưu tệp vào thiết bị','File saved on device'))})});
  root.querySelectorAll('[data-local-download]').forEach(b=>b.onclick=()=>{const doc=this.docs.find(d=>d.id===b.dataset.localDownload);if(doc)downloadDocument(doc)});
 }
}
