/* V5.9/V6.0: Read-only cloud HTML and server-command bridge.
 * Mutations are always verified in Streamlit, never accepted from the browser
 * without Google OIDC and per-project RBAC. Legacy local data is untouched.
 */
const h=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[ch]));
const labels={todo:'Chờ xử lý',working:'Đang thực hiện',review:'Chờ duyệt',done:'Hoàn thành'};
const actionLabels={
 'project.created':'Tạo dự án', 'task.created':'Giao công việc',
 'task.started':'Bắt đầu công việc', 'task.submitted':'Trình phê duyệt',
 'task.approved':'Chấp thuận', 'task.returned':'Trả lại',
 'document.registered':'Đăng ký hồ sơ trên Drive'
};
const view=()=>window.__xdCloud||{enabled:false,projects:[],tasks:[],documents:[],events:[]};
const current=()=>{
 const s=view();
 return s.projects.find(p=>p.id===s.selectedProjectId)||s.projects[0]||null;
};
const btn=(label,op,task='',other='outline')=>'<button type="button" class="btn '+other+' small" data-workspace-op="'+h(op)+'" data-workspace-task="'+h(task)+'">'+label+'</button>';
const role=()=>view().role||'read';
const canWrite=()=>['update','admin'].includes(role());
const canReview=()=>role()==='admin';
const header=()=>{
 const s=view(),p=current();
 return '<section class="panel padded"><div class="panel-heading"><div><h3>☁️ V5.9 / V6.0 · Dữ liệu dùng chung</h3><p>Google Drive bảo vệ dự án, công việc và phê duyệt • '+h(s.actor||'')+'</p></div><span class="mini-label">'+(s.role==='admin'?'ADMIN':s.role==='update'?'CẬP NHẬT':'CHỈ ĐỌC')+'</span></div>'+
 '<div class="portal-project-picker"><label>Dự án đang làm việc<select id="cloudProjectSelect"><option value="">— Chọn dự án —</option>'+
 (s.projects||[]).map(x=>'<option value="'+h(x.id)+'" '+(p&&p.id===x.id?'selected':'')+'>'+h(x.code)+' · '+h(x.name)+'</option>').join('')+
 '</select></label><div class="drive-sheet-actions">'+btn('↻ Làm mới dữ liệu','refresh')+'</div></div></section>';
};
const selectedTasks=()=>{
 const p=current();return p?(view().tasks||[]).filter(t=>t.projectId===p.id):[];
};
const projectCards=()=>{
 const s=view();
 return '<section class="panel padded"><div class="panel-heading"><h3>Danh sách dự án được cấp quyền</h3><span class="mini-label">'+s.projects.length+' DỰ ÁN</span></div>'+
 '<div class="portal-summary-grid">'+s.projects.map(p=>{
 const ts=s.tasks.filter(t=>t.projectId===p.id);
 const ds=s.documents.filter(d=>d.projectId===p.id);
 return '<article class="portal-project-card"><strong>'+h(p.code)+' · '+h(p.name)+'</strong><small>'+h(p.client||'')+'</small><div class="portal-project-numbers">'+
 '<span>'+ts.length+' công việc</span><span>'+ts.filter(t=>t.status==='review').length+' chờ duyệt</span><span>'+ds.length+' hồ sơ lập sổ</span></div></article>';
 }).join('')+'</div>'+
 (canReview()?'<div class="portal-review-actions">'+btn('＋ Tạo dự án mới','project_create','','primary')+btn('Sao lưu dữ liệu cũ trên thiết bị','legacy_backup')+btn('↑ Nhập bản sao dữ liệu cũ','project_import')+'</div>':'')+
 '<p class="footnote">Dự án cũ trong trình duyệt được giữ nguyên để đối chiếu. Không tự xóa hoặc tự chuyển dữ liệu.</p></section>';
};
const tasksHtml=filter=>{
 const tasks=selectedTasks().filter(t=>!filter||t.status===filter);
 return '<section class="panel padded"><div class="panel-heading"><h3>'+(filter?'Hồ sơ chờ phê duyệt':'Công việc dự án')+'</h3><span class="mini-label">'+tasks.length+' CÔNG VIỆC</span></div>'+
 (canWrite()&&!filter?'<div class="portal-review-actions">'+btn('＋ Tạo công việc','task_create','','primary')+'</div>':'')+
 '<div class="portal-tasks">'+tasks.map(t=>{
 const history=t.reviewHistory||[];
 return '<article class="portal-task"><div class="portal-task-head"><div><strong>'+h(t.title)+'</strong><small>'+h(t.code)+' · '+h(t.dept)+' · '+h(t.assignee||'Chưa giao')+
 '</small></div><span class="portal-pill '+(t.status==='review'?'review':t.status==='done'?'done':'')+'">'+h(labels[t.status]||t.status)+'</span></div>'+
 (t.dueDate?'<p>Hạn: '+h(t.dueDate)+'</p>':'')+
 (t.docCode?'<p>Hồ sơ: '+h(t.docCode)+'</p>':'')+
 (t.report?'<div class="portal-report"><b>Báo cáo</b><p>'+h(t.report)+'</p><p>'+h(t.findings)+'</p></div>':'')+
 '<div class="portal-review-actions">'+
 (canWrite()&&t.status==='todo'?btn('Bắt đầu','task_start',t.id):'')+
 (canWrite()&&['todo','working'].includes(t.status)?btn('Gửi báo cáo phê duyệt','task_submit',t.id,'primary'):'')+
 (canReview()&&t.status==='review'?btn('Xét duyệt / Trả lại','task_review',t.id,'primary'):'')+
 '</div>'+
 (history.length?'<details><summary>Nhật ký phê duyệt ('+history.length+')</summary>'+history.map(x=>'<p>'+h(x.at)+' · '+h(x.actor)+' · '+h(x.decision)+' · '+h(x.note)+'</p>').join('')+'</details>':'')+
 '</article>';
 }).join('')+'</div>'+
 (!tasks.length?'<div class="empty-state">Chưa có công việc trong mục này.</div>':'')+
 '<p class="footnote">Mọi quyết định được ghi theo tài khoản Google đăng nhập; chưa thay thế chữ ký số hoặc phê duyệt pháp lý.</p></section>';
};
const docsHtml=()=>{
 const p=current(),docs=p?(view().documents||[]).filter(d=>d.projectId===p.id):[];
 return '<section class="panel padded"><div class="panel-heading"><h3>Kho hồ sơ Google Drive · Sổ phiên bản</h3><span class="mini-label">'+docs.length+' HỒ SƠ ĐÃ LẬP SỔ</span></div>'+
 '<p>Tải tệp lên hoặc xem/tải xuống bằng các nút Google Drive ở đầu sheet. Mỗi lần upload tạo revision mới. Lưu vào sổ hồ sơ trong hộp thoại Drive để tra cứu chung.</p>'+
 '<div class="portal-document-list">'+docs.map(d=>'<article class="portal-document"><span><strong>'+h(d.code)+'</strong> · '+h(d.revision||'Không ghi phiên bản')+
 ' · '+h(d.filename)+'<small> · '+h(d.category)+' · '+h(d.actor)+'</small></span></article>').join('')+'</div>'+
 (!docs.length?'<div class="empty-state">Chưa lập sổ hồ sơ. Những tệp đã có trên Drive vẫn xem được tại nút Xem hồ sơ / Tải xuống.</div>':'')+
 '<p class="footnote">Dữ liệu tài liệu cũ trong IndexedDB vẫn lưu trên thiết bị; cần sao lưu trước khi chuyển đổi.</p></section>';
};
const activityHtml=()=>{
 const p=current(),ev=(view().events||[]).filter(e=>!p||e.projectId===p.id);
 return '<section class="panel padded"><h3>Nhật ký tác nghiệp tập trung</h3><p>Nhật ký ghi từ máy chủ, gắn tài khoản Google; lưu dạng sự kiện ký xác thực trên Drive.</p>'+
 ev.slice().reverse().map(e=>'<div class="portal-document"><strong>'+h(actionLabels[e.action]||e.action)+'</strong><span>'+h(e.at)+' · '+h(e.actor)+' · '+h(e.detail)+'</span></div>').join('')+
 (!ev.length?'<div class="empty-state">Chưa có hoạt động.</div>':'')+'</section>';
};
export function renderCloudPage(section){
 const s=view();if(!s.enabled)return '';
 return header()+ (section==='projects'?projectCards():
 section==='tasks'?tasksHtml(''):
 section==='reviews'?tasksHtml('review'):
 section==='documents'?docsHtml():
 section==='activity'?activityHtml():'');
}
const send=(section,op,taskId='',projectId='')=>{
 const currentProject=current();
 const token=window.__xdDriveNonce;
 if(!token)return;
 const requestId=(globalThis.crypto?.randomUUID?.()||String(Date.now())+'-'+Math.random().toString().slice(2)).replace(/-/g,'').slice(0,32);
 window.parent.postMessage({
  channel:'XD_MEP_DRIVE_V1',nonce:token,kind:'workspace',section,op,
  projectId:projectId||currentProject?.id||'',taskId:taskId||'',
  actionId:requestId,
 },'*');
};
let backupHandlerAttached=false;
export function bindCloudPage(root,section){
 root.querySelector('#cloudProjectSelect')?.addEventListener('change',e=>send(section,'select','',''+e.target.value));
 root.querySelectorAll('[data-workspace-op]').forEach(b=>b.addEventListener('click',()=>{
  const op=b.dataset.workspaceOp;
  if(op==='legacy_backup'){
   const data=localStorage.getItem('xd-mep-local-workspace-v573');
   if(!data){alert('Không tìm thấy dữ liệu cục bộ cũ.');return;}
   const blob=new Blob([data],{type:'application/json;charset=utf-8'});
   const url=URL.createObjectURL(blob),a=document.createElement('a');
   a.href=url;a.download='XD_MEP_local_workspace_backup_'+new Date().toISOString().slice(0,10)+'.json';
   document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
   alert('Đã xuất bản sao metadata. Tệp gốc lưu IndexedDB cần sao lưu riêng tại Kho tài liệu cũ.');
   return;
  }
  if(op==='project_create'&&role()!=='admin')return;
  if(['task_create','task_start','task_submit'].includes(op)&&!canWrite())return;
  if(op==='task_review'&&!canReview())return;
  send(section,op,b.dataset.workspaceTask||'');
 }));
}
