/* V5.9/V6.0: Read-only cloud HTML and server-command bridge.
 * Mutations are always verified in Streamlit, never accepted from the browser
 * without Google OIDC and per-project RBAC. Legacy local data is untouched.
 */
const h=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[ch]));
const labels={todo:'Chờ xử lý',working:'Đang thực hiện',review:'Chờ duyệt',done:'Hoàn thành',cancelled:'Đã hủy'};
const actionLabels={
 'project.created':'Tạo dự án', 'task.created':'Giao công việc',
 'task.started':'Bắt đầu công việc', 'task.submitted':'Trình phê duyệt',
 'task.approved':'Chấp thuận', 'task.returned':'Trả lại', 'task.assigned':'Phân công kỹ sư và Agent',
 'task.unassigned':'Thu hồi phân công', 'task.cancelled':'Hủy công việc',
 'org.role_set':'Bổ nhiệm vị trí nhân sự', 'hierarchy.proposed':'CEO đề xuất phân việc',
 'hierarchy.approved':'Admin duyệt và giao việc các cấp',
 'hierarchy.rejected':'Admin trả lại phương án CEO',
 'document.registered':'Đăng ký hồ sơ trên Drive',
 'document.metadata_updated':'Cập nhật sổ hồ sơ',
 'document.submitted':'Trình hồ sơ',
 'document.approved':'Duyệt hồ sơ',
 'document.returned':'Trả hồ sơ yêu cầu sửa',
 'document.archived':'Chuyển hồ sơ lưu trữ'
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
const canReviewTask=t=>{
 if(canReview())return true;
 if(role()!=='update'||!t.parentTaskId||t.hierarchyStage==='qa')return false;
 const parent=(view().tasks||[]).find(x=>x.id===t.parentTaskId);
 const actor=(view().actor||'').toLowerCase();
 return !!(parent&&(parent.assignee||'').toLowerCase()===actor&&
  (t.assignee||'').toLowerCase()!==actor);
};
const taskWithdrawControl=t=>{
 if(!canWrite())return '';
 if(t.hierarchyStage&&!canReview()){
  const parent=(view().tasks||[]).find(x=>x.id===t.parentTaskId);
  const isManager=parent&&String(parent.assignee||'').toLowerCase()===
    String(view().actor||'').toLowerCase();
  if(!isManager)return '<button type="button" class="btn outline small" disabled '+
   'title="Chỉ cấp quản lý trực tiếp hoặc Admin được thu hồi">↩ Thu hồi (cần cấp quản lý)</button>';
 }
 if(['done','cancelled'].includes(t.status))
  return '<button type="button" class="btn outline small" disabled title="Công việc đã đóng và không thể hủy lại">↩ Thu hồi / Hủy giao việc</button>';
 if(canReview())return btn('↩ Thu hồi / Hủy giao việc','task_withdraw',t.id);
 // Editor may withdraw an assignment, or reset unassigned work in progress.
 // Permanent cancellation remains an authenticated Admin action.
 if(['todo','working'].includes(t.status)&&
   (t.status==='working'||t.assignee||t.assignedAgentId))
  return btn('↩ Thu hồi / Đặt về Chờ xử lý','task_withdraw',t.id);
 const reason=t.status==='review'?'Công việc đang chờ duyệt: chỉ Admin được hủy':
  'Công việc chưa giao và đang Chờ xử lý: chỉ Admin được hủy';
 return '<button type="button" class="btn outline small" disabled title="'+h(reason)+
  '">↩ Hủy công việc (cần Admin)</button>';
};
const header=()=>{
 const s=view(),p=current();
 return '<section class="panel padded"><div class="panel-heading"><div><h3>☁️ V5.9 / V6.0 · Dữ liệu dùng chung</h3><p>Google Drive bảo vệ dự án, công việc và phê duyệt • '+h(s.actor||'')+'</p></div><span class="mini-label">'+(s.role==='admin'?'ADMIN':s.role==='update'?'CẬP NHẬT':'CHỈ ĐỌC')+'</span></div>'+
 '<div class="portal-project-picker"><label>Dự án đang làm việc<select id="cloudProjectSelect"><option value="">— Chọn dự án —</option>'+
 (s.projects||[]).map(x=>'<option value="'+h(x.id)+'" '+(p&&p.id===x.id?'selected':'')+'>'+h(x.code)+' · '+h(x.name)+'</option>').join('')+
 '</select></label><div class="drive-sheet-actions">'+btn('↻ Làm mới dữ liệu','refresh')+'</div></div>'+
 (s.lastActionNotice?'<p class="portal-success-note" role="status">✓ '+h(s.lastActionNotice)+'</p>':'')+
 '</section>';
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
const hierarchyStages={ceo:'Giám đốc',pm:'PM · Quản lý dự án',lead:'Trưởng bộ môn',expert:'Chuyên gia',qa:'QA/QC'};
const tasksHtml=filter=>{
 const all=selectedTasks();
 const order=[],visited=new Set();
 const walk=(task,depth=0)=>{
  if(visited.has(task.id)||depth>5)return;
  visited.add(task.id);
  order.push(task);
  all.filter(t=>t.parentTaskId===task.id).forEach(t=>walk(t,depth+1));
 };
 all.filter(t=>!t.parentTaskId||!all.some(x=>x.id===t.parentTaskId)).forEach(t=>walk(t));
 all.forEach(t=>walk(t));
 const tasks=order.filter(t=>!filter||t.status===filter);
 const pendingPlans=(view().hierarchyPlans||[]).filter(p=>
  p.projectId===current()?.id&&p.status==='pending');
 return '<section class="panel padded"><div class="panel-heading"><h3>'+(filter?'Hồ sơ chờ phê duyệt':'Công việc dự án')+'</h3><span class="mini-label">'+tasks.length+' CÔNG VIỆC</span></div>'+
 (canWrite()&&!filter?'<div class="portal-review-actions">'+btn('＋ Tạo công việc','task_create','','primary')+
  (canReview()?btn('⚙ Cơ cấu tổ chức','org_roles'):'')+
  (canReview()&&pendingPlans.length?btn('✓ Duyệt phương án CEO ('+pendingPlans.length+')','hierarchy_review','','primary'):'')+
  '</div>':'')+
 '<div class="portal-tasks">'+tasks.map(t=>{
 const history=t.reviewHistory||[];
 const reports=(view().agentRuns||[]).filter(r=>r.taskId===t.id&&r.projectId===t.projectId);
 const specialist=(view().agentsCatalog||[]).find(a=>a.id===t.assignedAgentId);
 const agentLabel=specialist?specialist.title+' ('+specialist.id+')':'Chưa gán Agent';
 const runLabel=t.status==='cancelled'?'Không chạy — công việc đã hủy':
  reports.length?'Đã tạo '+reports.length+' báo cáo nháp; chờ kỹ sư kiểm chứng':
  'Agent chưa chạy cho công việc này';
 const returned=t.status==='working'&&t.lastReviewDecision==='reject';
 const p=all.find(x=>x.id===t.parentTaskId);
 const plan=(view().hierarchyPlans||[]).find(x=>x.rootTaskId===t.id&&x.status==='pending');
 const existingPlan=(view().hierarchyPlans||[]).some(x=>
  x.rootTaskId===t.id&&['pending','dispatched'].includes(x.status));
 const progress=t.hierarchyProgress||{total:0,done:0,blockedBy:[]};
 const blocked=(progress.blockedBy||[]).length>0;
 const actor=(view().actor||'').toLowerCase();
 const canOperate=canWrite()&&(!t.hierarchyStage||canReview()||
  (t.assignee||'').toLowerCase()===actor);
 const supervisor=p&&((p.assignee||'').toLowerCase()===actor);
 const canDelegate=canReview()||!!supervisor;
 const statusLabel=returned?'Yêu cầu sửa':(labels[t.status]||t.status);
 return '<article class="portal-task portal-hierarchy-'+h(t.hierarchyStage||'none')+'" data-parent-task="'+h(t.parentTaskId||'')+'"><div class="portal-task-head"><div><strong>'+h(t.title)+'</strong><small>'+h(t.code)+' · '+h(t.dept)+' · '+h(t.assignee||'Chưa giao')+
 '</small></div><span class="portal-pill '+(t.status==='review'?'review':t.status==='done'?'done':t.status==='cancelled'?'cancelled':returned?'returned':'')+'">'+h(statusLabel)+'</span></div>'+
 (t.hierarchyStage?'<p class="company-secondary"><b>Tuyến phân cấp:</b> '+
  h(hierarchyStages[t.hierarchyStage]||t.hierarchyStage)+
  (p?' · Cấp trên: '+h(p.code):' · Công việc gốc')+
  (t.assignedBy?' · Được giao bởi: '+h(t.assignedBy):'')+'</p>':'')+
 (progress.total?'<p class="company-secondary" role="status"><b>Tiến độ cấp dưới:</b> '+
  progress.done+'/'+progress.total+' nhiệm vụ con đã được duyệt</p>':'')+
 (blocked?'<p class="portal-hierarchy-block" role="status">🔒 Chưa được xử lý: còn '+
  progress.blockedBy.length+' nhiệm vụ tiền nhiệm chưa được duyệt.</p>':'')+
 (plan?'<p class="portal-hierarchy-block" role="status">CEO đã gửi phương án; chờ Admin phê duyệt phân phối.</p>':'')+
 '<p class="company-secondary"><b>Chuyên gia được giao:</b> '+h(agentLabel)+
  ' · <b>Trạng thái Agent:</b> '+h(runLabel)+'</p>'+
 (t.status==='cancelled'?'<p class="company-secondary"><b>Đã hủy:</b> '+h(t.cancelReason||'')+
  ' · '+h(t.cancelledBy||'')+' · '+h(t.cancelledAt||'')+'</p>':
  (!t.assignee&&!t.assignedAgentId&&t.withdrawnAt?'<p class="company-secondary"><b>Đã thu hồi:</b> '+
   h(t.withdrawReason||'')+' · '+h(t.withdrawnBy||'')+'</p>':''))+
 (returned?'<div class="portal-return-note" role="status"><b>↩ Admin trả lại — cần sửa và trình lại</b>'+
  '<p>'+h(t.lastReviewNote||'Chưa có lý do')+'</p><small>Người trả: '+h(t.lastReviewer||'')+
  ' · '+h(t.lastReviewedAt||'')+'</small></div>':
  t.status==='done'&&t.lastReviewDecision==='approve'?
  '<p class="company-secondary" role="status"><b>✓ Đã phê duyệt:</b> '+h(t.lastReviewer||'')+
  ' · '+h(t.lastReviewedAt||'')+(t.lastReviewNote?' · '+h(t.lastReviewNote):'')+'</p>':
  t.status==='review'?'<p class="company-secondary" role="status"><b>Đã trình, đang chờ Admin xét duyệt</b>'+
  ' · '+h(t.lastSubmittedAt||'')+'</p>':'')+
 (t.dueDate?'<p>Hạn: '+h(t.dueDate)+'</p>':'')+
 (t.docCode?'<p>Hồ sơ: '+h(t.docCode)+'</p>':'')+
 (t.report?'<div class="portal-report"><b>Báo cáo</b><p>'+h(t.report)+'</p><p>'+h(t.findings)+'</p></div>':'')+
 (reports.length?'<details><summary>🤖 Báo cáo nháp Agent ('+reports.length+')</summary>'+
 reports.map(run=>'<div class="company-run"><strong>'+h(run.agentTitle||run.agentId)+
 ' · '+h(({llm:'AI metadata',expert_llm:'AI + đọc mẫu file',expert:'Chuyên gia đọc file',preflight:'Checklist'})[run.mode]||run.mode)+'</strong><p>'+h(run.actor)+
 ' · '+h(run.at.slice(0,16))+'</p><pre class="company-result">'+h(run.result)+'</pre>'+
 '<p class="company-secondary">Kết quả này chưa được kỹ sư kiểm chứng hoặc phê duyệt.</p></div>').join('')+
 '</details>':'')+
 (t.priority&&t.priority!=='normal'?'<p><b>Ưu tiên: '+h(
  {low:'Thấp',high:'Cao',critical:'Khẩn cấp'}[t.priority]||t.priority
 )+'</b></p>':'')+
  '<div class="portal-review-actions">'+
 (canWrite()&&['todo','working'].includes(t.status)&&
   (!t.hierarchyStage||canDelegate)?btn('Gán / Sửa phân công','task_assign',t.id):'')+
 (canWrite()&&t.assignedAgentId==='CEO'&&t.dept==='director'&&
  !t.parentTaskId&&!existingPlan&&['todo','working'].includes(t.status)&&
  (canReview()||(t.assignee||'').toLowerCase()===actor)?
  btn('🏢 Giám đốc AI lập phương án','hierarchy_propose',t.id,'primary'):'')+
 (canReview()&&plan?btn('✓ Duyệt phân phối từ CEO','hierarchy_review',t.id,'primary'):'')+
 taskWithdrawControl(t)+
 (canOperate&&!blocked&&specialist&&['todo','working'].includes(t.status)?
  '<button type="button" class="btn primary small" data-agent-run-task="'+h(t.id)+'" data-agent-run-id="'+h(specialist.id)+'" data-agent-run-project="'+h(t.projectId)+'">🤖 Chạy Agent '+h(specialist.id)+'</button>':'')+
 (canOperate&&!blocked&&t.status==='todo'?btn('Bắt đầu','task_start',t.id):'')+
 (canOperate&&!blocked&&(!progress.total||progress.done===progress.total)&&
  ['todo','working'].includes(t.status)?
  btn(returned?'Gửi lại báo cáo sau sửa':'Gửi báo cáo phê duyệt','task_submit',t.id,'primary'):'')+
 (canReviewTask(t)&&t.status==='review'?btn('Xét duyệt / Trả lại','task_review',t.id,'primary'):'')+
 '</div>'+
 (history.length?'<details><summary>Lịch sử xử lý ('+history.length+')</summary>'+history.map(x=>'<p>'+h(x.at)+' · '+h(x.actor)+' · '+h(({withdraw:'Thu hồi phân công',cancel:'Hủy công việc',submitted:'Trình duyệt',approve:'Phê duyệt',reject:'Trả lại'})[x.decision]||x.decision)+' · '+h(x.note)+'</p>').join('')+'</details>':'')+
 '</article>';
 }).join('')+'</div>'+
 (!tasks.length?'<div class="empty-state">Chưa có công việc trong mục này.</div>':'')+
 '<p class="footnote">Mọi quyết định được ghi theo tài khoản Google đăng nhập; chưa thay thế chữ ký số hoặc phê duyệt pháp lý.</p></section>';
};
const docStatusLabel={
  unregistered:'Chưa lập sổ',draft:'Mới lập sổ',pending:'Chờ duyệt',
  approved:'Đã duyệt',returned:'Yêu cầu sửa',archived:'Lưu trữ',
  missing:'Không tìm thấy'
};
const docTextStatus=s=>docStatusLabel[s]||s||'—';
const docByteSize=size=>{
  const bytes=Number(size||0);
  return bytes>=1048576?(bytes/1048576).toFixed(2)+' MB':(bytes/1024).toFixed(1)+' KB';
};
const docDate=raw=>{
  if(!raw)return '—';
  const d=new Date(raw);
  return Number.isNaN(d.getTime())?raw:d.toLocaleDateString('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric'});
};
const docsHtml=()=>{
 const s=view(),p=current();
 const registered=p?(s.documents||[]).filter(d=>d.projectId===p.id):[];
 const items=Array.isArray(s.fileInventory)?s.fileInventory:null;
 const counts=s.fileCounts||{};
 return '<section class="panel padded xd-document-control">'+
 '<div class="panel-heading"><div><h2>📚 Sổ quản lý hồ sơ & kiểm kê Google Drive</h2>'+
 '<p>Quản lý toàn bộ file đã tải lên theo dự án, nhóm hồ sơ, mã tài liệu và phiên bản.</p></div>'+
 '<span class="mini-label">V6.0.1</span></div>'+
 '<div class="portal-review-actions xd-doc-toolbar">'+
 btn('↻ Kiểm kê toàn bộ file Drive','document_inventory','','primary')+
 btn('📋 Quản lý hồ sơ / duyệt / tải bản gốc','document_manage')+
 '</div>'+
 (items===null?
  '<div class="info-strip">Nhấn <b>Kiểm kê toàn bộ file Drive</b> để quét các nhóm hồ sơ, bao gồm cả những file đã tải lên từ trước nhưng chưa ghi sổ. Bảng sẽ hiển thị tên tệp, revision, trạng thái, thời điểm và người ghi sổ.</div>'+
  '<div class="portal-document-list">'+registered.map(d=>
    '<div class="portal-document"><span><strong>'+h(d.code)+'</strong> · '+h(d.revision||'—')+
    ' · '+h(d.filename)+' · '+h(docTextStatus(d.status||'draft'))+
    ' · '+h(d.actor||'Chưa rõ')+'</span>'+
    '<button type="button" class="btn outline small" data-v601-file="'+h(d.id)+'">Chi tiết</button></div>'
  ).join('')+'</div>':
  '<div class="xd-doc-summary">'+
  [['TỔNG TỆP',counts.total||0],['ĐÃ GHI SỔ',counts.registered||0],
   ['CHƯA GHI SỔ',counts.unregistered||0],['CHỜ DUYỆT',counts.pending||0],
   ['ĐÃ DUYỆT',counts.approved||0],['MẤT LIÊN KẾT',counts.missing||0],
   ['THAY ĐỔI FILE',counts.modified||0]].map(([l,v])=>
   '<div class="xd-doc-counter"><small>'+h(l)+'</small><strong>'+h(v)+'</strong></div>'
  ).join('')+'</div>'+
  ((counts.truncated)?'<div class="info-strip">Bảng hiển thị '+h(counts.displayed)+'/'+h(counts.total)+' tệp đầu tiên để bảo đảm hiệu năng. Chọn Quản lý hồ sơ để tìm và xuất CSV đầy đủ trên máy chủ.</div>':'')+
  '<div class="xd-doc-filters">'+
  '<label>Tìm kiếm<input id="v601DocSearch" type="search" placeholder="Tên file, mã hồ sơ, người ghi sổ…" autocomplete="off"></label>'+
  '<label>Nhóm hồ sơ<select id="v601DocCategory"><option value="all">Tất cả nhóm</option>'+
  [...new Set(items.map(x=>x.category))].sort().map(x=>
   '<option value="'+h(x)+'">'+h(x.replaceAll('_',' ').toUpperCase())+'</option>').join('')+
  '</select></label>'+
  '<label>Trạng thái<select id="v601DocStatus"><option value="all">Tất cả trạng thái</option>'+
  Object.entries(docStatusLabel).map(([k,v])=>'<option value="'+h(k)+'">'+h(v)+'</option>').join('')+
  '</select></label>'+
  '<label>Sắp xếp<select id="v601DocSort"><option value="new">Mới cập nhật</option>'+
  '<option value="name">Tên hồ sơ A–Z</option><option value="revision">Revision mới nhất</option></select></label>'+
  '</div>'+
  '<div class="portal-review-actions xd-doc-toolbar"><label class="xd-doc-check">'+
  '<input type="checkbox" id="v601DocLatest"> Chỉ hiển thị revision mới nhất</label>'+
  '<button type="button" class="btn outline small" id="v601DocExport">⬇ CSV danh sách đang hiển thị</button>'+
  '<span id="v601DocResults" class="mini-label" aria-live="polite"></span></div>'+
  '<div class="xd-doc-table-scroll"><table class="xd-doc-table">'+
  '<thead><tr><th>Mã hồ sơ / Tên file</th><th>Nhóm</th><th>Phiên bản</th>'+
  '<th>Trạng thái</th><th>Ngày tải</th><th>Người ghi sổ</th><th>Dung lượng</th><th>Thao tác</th></tr></thead>'+
  '<tbody id="v601DocTableBody"></tbody></table></div>'+
  '<p class="footnote">Ngày tải theo Google Drive; người ghi sổ chỉ xác định khi hồ sơ được thao tác qua ứng dụng. File cũ chưa có thông tin người tải qua app sẽ được đánh dấu Chưa xác định. Tệp đã duyệt muốn sửa nội dung phải tải thành revision mới.</p>')+
 '<p class="footnote">Tệp IndexedDB cũ vẫn nằm trên thiết bị; không xóa hoặc tự di chuyển dữ liệu cũ.</p>'+
 '</section>';
};
function _csvSafe(value){
 const raw=String(value??'');
 const safe=/^[\s]*[=+\-@]/.test(raw)?"'"+raw:raw;
 return '"'+safe.replaceAll('"','""')+'"';
}
function exportDocumentCatalog(items){
 const cols=['Mã hồ sơ','Tên file','Nhóm','Phiên bản','Trạng thái','Dung lượng (bytes)',
 'Ngày tạo Drive','Ngày cập nhật','Người ghi sổ','Mô tả','Đã ghi sổ','File không còn','ID'];
 const data=[cols,...items.map(d=>[d.code,d.filename,d.category,d.revision,
  docTextStatus(d.status),d.sizeBytes,d.createdTime,d.modifiedTime,d.actor,d.description,
  d.registered?'Có':'Không',d.missing?'Có':'Không',d.id])];
 const csv='\ufeff'+data.map(row=>row.map(_csvSafe).join(',')).join('\r\n');
 const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='XD_MEP_so_kiem_soat_ho_so_'+new Date().toISOString().slice(0,10)+'.csv';
 document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
}
function bindDocumentInventory(root){
 const all=Array.isArray(view().fileInventory)?view().fileInventory:null;
 const tbody=root.querySelector('#v601DocTableBody');
 const p=current();
 if(!tbody){
  root.querySelectorAll('[data-v601-file]').forEach(b=>b.addEventListener('click',()=>{
   send('documents','document_manage','',p?.id||'',b.dataset.v601File);
  }));
  return;
 }
 const search=root.querySelector('#v601DocSearch'),cat=root.querySelector('#v601DocCategory');
 const status=root.querySelector('#v601DocStatus'),sort=root.querySelector('#v601DocSort');
 const latest=root.querySelector('#v601DocLatest'),results=root.querySelector('#v601DocResults');
 const draw=()=>{
  const q=search.value.trim().toLocaleLowerCase('vi');
  let filtered=(all||[]).filter(d=>
   (cat.value==='all'||d.category===cat.value)&&
   (status.value==='all'||d.status===status.value)&&
   (!latest.checked||d.latest||d.missing)&&
   (!q||[d.code,d.filename,d.actor,d.category,d.description].join(' ').toLocaleLowerCase('vi').includes(q))
  );
  if(sort.value==='name')filtered.sort((a,b)=>a.code.localeCompare(b.code,'vi'));
  if(sort.value==='revision')filtered.sort((a,b)=>((b.revision.match(/\d+/)?.[0]||0)-
      (a.revision.match(/\d+/)?.[0]||0)));
  if(sort.value==='new')filtered.sort((a,b)=>
     (b.modifiedTime||b.registeredAt||'').localeCompare(a.modifiedTime||a.registeredAt||''));
  const limit=150;
  tbody.innerHTML=filtered.slice(0,limit).map(d=>
    '<tr'+(d.missing?' class="xd-doc-missing"':'')+'><td><strong>'+h(d.code)+'</strong>'+
    '<small>'+h(d.filename)+'</small>'+ (d.integrityWarning?'<small class="xd-doc-alert">⚠ File thay đổi</small>':'')+
    (d.missing?'<small class="xd-doc-alert">⚠ Không tìm thấy trên Drive</small>':'')+
    '</td><td>'+h(d.category.replaceAll('_',' ').toUpperCase())+'</td>'+
    '<td>'+h(d.revision||'—')+(d.latest?'<small>Mới nhất</small>':'')+'</td>'+
    '<td><span class="xd-doc-status xd-status-'+h(d.status)+'">'+h(docTextStatus(d.status))+'</span></td>'+
    '<td>'+h(docDate(d.createdTime||d.registeredAt))+'</td>'+
    '<td>'+h(d.actor||'Chưa xác định')+'</td>'+
    '<td>'+h(docByteSize(d.sizeBytes))+'</td>'+
    '<td><button type="button" class="btn outline small" data-v601-file="'+h(d.id)+'">Chi tiết</button></td></tr>'
  ).join('')||'<tr><td colspan="8" class="xd-doc-empty">Không có hồ sơ phù hợp bộ lọc.</td></tr>';
  results.textContent='Hiển thị '+Math.min(filtered.length,limit)+' / '+filtered.length+' tệp';
 };
 for(const control of [search,cat,status,sort,latest])control.addEventListener('input',draw);
 tbody.addEventListener('click',e=>{
  const button=e.target.closest('[data-v601-file]');
  if(button)send('documents','document_manage','',p?.id||'',button.dataset.v601File);
 });
 root.querySelector('#v601DocExport')?.addEventListener('click',()=>exportDocumentCatalog(all||[]));
 draw();
}
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
export function requestDocumentInventory(){
 if(!Array.isArray(view().fileInventory))send('documents','document_inventory');
}
const send=(section,op,taskId='',projectId='',fileId='',agentId='')=>{
 const currentProject=current();
 const token=window.__xdDriveNonce;
 if(!token)return;
 const requestId=(globalThis.crypto?.randomUUID?.()||String(Date.now())+'-'+Math.random().toString().slice(2)).replace(/-/g,'').slice(0,32);
 window.parent.postMessage({
  channel:'XD_MEP_DRIVE_V1',nonce:token,kind:'workspace',section,op,
  projectId:projectId||currentProject?.id||'',taskId:taskId||'',fileId:fileId||'',agentId:agentId||'',
  actionId:requestId,
 },'*');
};
let backupHandlerAttached=false;
export function bindCloudPage(root,section){
 if(section==='documents')bindDocumentInventory(root);
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
  if(['task_create','task_assign','task_withdraw','task_start','task_submit','hierarchy_propose'].includes(op)&&!canWrite())return;
  if(['org_roles','hierarchy_review'].includes(op)&&!canReview())return;
  if(op==='task_review'){
   const selected=(view().tasks||[]).find(t=>t.id===b.dataset.workspaceTask);
   if(!selected||!canReviewTask(selected))return;
  }
  send(section,op,b.dataset.workspaceTask||'');
 }));
 root.querySelectorAll('[data-agent-run-task]').forEach(b=>b.addEventListener('click',()=>{
  if(!canWrite())return;
  send('agents','agent_run',b.dataset.agentRunTask,b.dataset.agentRunProject,'',
       b.dataset.agentRunId);
 }));
}
