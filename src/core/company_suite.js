/* V6.1-V6.3: project-scoped Company Operations Center and 18 real Agent contracts.
   All execution, mutations, quota and role checks occur in Streamlit Python.
   This module displays signed server data and never receives provider API keys. */
const h=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'" :'&#39;'}[ch]));
const state=()=>window.__xdCloud||{};
const writable=()=>['admin','update'].includes(state().role);
const ownProject=()=>state().projects?.find(p=>p.id===state().selectedProjectId)||state().projects?.[0]||null;
const lookupAgent=id=>(state().agentsCatalog||[]).find(a=>a.id===id);
const division=(dept)=>dept==='legal'?'Dùng chung':dept.startsWith('xd_')||['architecture','structure'].includes(dept)?'Xây dựng':'MEP';
const deptLabel={
 director:'Ban giám đốc',electrical:'Điện',hvac:'HVAC',plumbing:'Cấp thoát nước',
 fire:'PCCC',bim:'BIM MEP',qs:'QS MEP',qa:'QA/QC MEP',architecture:'Kiến trúc',
 structure:'Kết cấu',xd_bim:'BIM Xây dựng',xd_qs:'QS Xây dựng',
 xd_planning:'Kế hoạch thi công',xd_site:'Hiện trường',
 xd_safety:'An toàn – Chất lượng',xd_material:'Vật tư',xd_qc:'QA/QC Xây dựng',legal:'Pháp chế & hợp đồng'
};
function projectPicker(section){
 const s=state(),p=ownProject();
 return '<section class="panel padded"><div class="panel-heading"><div><h3>🏢 Điều phối theo dự án được cấp quyền</h3><p>Dữ liệu thực trên Google Drive, xác thực bằng Google OIDC</p></div>'+
 '<span class="mini-label">'+(s.role==='admin'?'ADMIN':s.role==='update'?'CẬP NHẬT':'CHỈ ĐỌC')+'</span></div>'+
 '<div class="portal-project-picker"><label>Dự án<select class="company-project-select" aria-label="Dự án">'+
 (s.projects||[]).map(x=>'<option value="'+h(x.id)+'" '+(p?.id===x.id?'selected':'')+'>'+h(x.code)+' · '+h(x.name)+'</option>').join('')+
 '</select></label><button class="btn outline" data-company-action="refresh">↻ Cập nhật dữ liệu</button></div></section>';
}
const kpi=(title,number,note='')=>
 '<div class="company-kpi"><small>'+h(title)+'</small><strong>'+h(number)+'</strong>'+
 (note?'<span>'+h(note)+'</span>':'')+'</div>';
function agentCards(){
 const s=state(),tasks=(s.tasks||[]).filter(t=>t.projectId===ownProject()?.id);
 const runs=(s.agentRuns||[]);
 const configured=s.aiStatus?.configured;
 const profiles=s.agentsCatalog||[];
 return '<section class="panel padded company-suite">'+
 '<div class="panel-heading"><div><h2>'+profiles.length+' Agent theo 16 phòng/khối nghiệp vụ</h2>'+
 '<p>Định rõ chuyên môn và kết quả. Chỉ hiện Đã chạy khi có sự kiện Agent hoàn thành và lưu báo cáo.</p></div>'+
 '<span class="mini-label">'+profiles.length+' AGENT</span></div>'+
 '<div class="company-notice">'+(configured?
 'Đã cấu hình AI dùng chung trên máy chủ: <strong>'+h(s.aiStatus.provider+' / '+s.aiStatus.model)+'</strong> trên máy chủ. Khi chạy AI, yêu cầu sự đồng ý gửi metadata dự án ra nhà cung cấp.':
 'Chưa cấu hình AI máy chủ. <strong>Kiểm tra checklist đầu vào</strong> vẫn chạy thật; chưa có phân tích từ mô hình AI. Admin vào Cài đặt → API dùng chung để lưu khóa mã hóa một lần cho cả công ty.')+
 '<br>V6.4–6.6: đã có bộ đọc mẫu PDF/XLSX/CSV/DXF/IFC và kiểm tra BOQ/công thức có nguồn; <strong>DWG/RVT, IFC clash hình học và file trên 50 MB vẫn cần worker</strong>. Mọi báo cáo cần kỹ sư thẩm tra.</div>'+
 '<div class="company-agent-grid">'+profiles.map(a=>{
 const isCoordinator=['CEO','PM','DOC','QAC'].includes(a.id);
 const compatible=tasks.filter(t=>t.dept===a.department||(isCoordinator&&t.dept!=='xd_qc'));
 const histories=runs.filter(r=>r.agentId===a.id);
 const l=histories[0];
 return '<article class="company-agent-card"><div class="company-agent-head"><span class="company-avatar">'+h(a.id)+'</span><div>'+
 '<strong>'+h(a.title)+'</strong><small>'+h(deptLabel[a.department]||a.department)+' · '+h(division(a.department))+'</small></div>'+
 '<span class="company-state">'+(l?(l.mode==='llm'?'Đã chạy AI':'Đã kiểm tra checklist'):'Chưa chạy')+'</span></div>'+
 '<p><b>Nhiệm vụ:</b> '+h(a.mission)+'</p><p><b>Đầu ra:</b> '+h(a.output)+'</p>'+
 '<div class="company-skills"><b>Kỹ năng:</b> '+a.skills.map(x=>'<span>'+h(x)+'</span>').join('')+'</div>'+
 '<p class="company-secondary"><b>Hồ sơ cần:</b> '+h((a.expected_categories||[]).join(', ')||'Theo dự án')+'</p>'+
 '<p class="company-secondary"><b>Công cụ chuyên gia:</b> '+
   h((a.expert_tools||[]).join(' · ')||'Theo nhiệm vụ')+'</p>'+
 '<p class="company-secondary"><b>Phối hợp:</b> '+a.partners.map(h).join(' • ')+'</p>'+
 '<details><summary>Giới hạn chuyên môn & kiểm tra chất lượng</summary>'+
 '<p>'+h(a.prohibition)+'</p><ul>'+a.quality_gate.map(x=>'<li>'+h(x)+'</li>').join('')+'</ul></details>'+
 (a.execution_disabled?'<p class="company-secondary">Chưa bật thực thi cho dự án này.</p>':writable()?'<div class="company-agent-operate">'+
 (compatible.length?'<label>Chọn công việc phù hợp<select data-agent-task="'+h(a.id)+'">'+compatible.map(t=>
 '<option value="'+h(t.id)+'">'+h(t.code+' · '+t.title.slice(0,60))+'</option>').join('')+'</select></label>'+
 '<button class="btn primary small" data-agent-execute="'+h(a.id)+'">Chạy Agent</button>':
 '<div class="company-secondary">Chưa có công việc phù hợp. Vào Công việc để giao nhiệm vụ.</div><button class="btn outline small" data-go="tasks">Giao công việc</button>')+
 '</div>':'<p class="company-secondary">Quyền Chỉ đọc: chỉ xem kết quả đã lưu.</p>')+
 (l?'<details><summary>Kết quả gần nhất · '+h(l.at.slice(0,16))+'</summary>'+
 '<p><b>Loại:</b> '+h(
   l.mode==='expert_llm'?'AI phân tích từ file':
   l.mode==='expert'?'Chuyên gia kiểm tra file thật':
   l.mode==='llm'?'AI metadata':'Checklist')+' · '+h(l.actor)+'</p>'+
 (l.expertEvidence?.provenance?'<p><b>File:</b> '+h(l.expertEvidence.provenance.filename)+
  ' · SHA256 '+h(l.expertEvidence.provenance.sha256.slice(0,12))+'…</p>':'')+
 '<pre class="company-result">'+h(l.result)+'</pre><p>Yêu cầu kỹ sư kiểm chứng trước khi sử dụng.</p></details>':'')+
 '</article>';
 }).join('')+'</div></section>';
}
function runHistory(){
 const s=state(),p=ownProject();
 const runs=(s.agentRuns||[]).filter(r=>r.projectId===p?.id);
 return '<section class="panel padded company-suite"><div class="panel-heading"><h3>Nhật ký kết quả Agent của dự án</h3>'+
 '<span class="mini-label">'+runs.length+' KẾT QUẢ GẦN ĐÂY</span></div>'+
 (!runs.length?'<p>Chưa có Agent nào tạo báo cáo nháp cho dự án này.</p>':
 runs.map(r=>'<details class="company-run"><summary>'+
 h((lookupAgent(r.agentId)?.title||r.agentId)+' · '+(
   r.mode==='expert_llm'?'AI + file thật':
   r.mode==='expert'?'Chuyên gia tệp thật':
   r.mode==='llm'?'AI metadata':'Checklist')+
 ' · '+r.at.slice(0,16))+'</summary><p>'+h(r.actor)+' · '+h(r.taskId)+'</p>'+
 '<pre class="company-result">'+h(r.result)+'</pre>'+
 (r.workflowStages?.length?'<ul>'+r.workflowStages.map(st=>'<li>'+
   h(st.expert)+' → '+h(st.status)+' · '+h(st.detail)+'</li>').join('')+'</ul>':'')+
 (r.expertEvidence?.provenance?'<p class="company-secondary">Nguồn: '+
   h(r.expertEvidence.provenance.filename)+' · '+h(r.expertEvidence.provenance.sha256.slice(0,16))+'…</p>':'')+
 '<p class="company-secondary">'+
 'Chưa phải tài liệu đã được phê duyệt. Kỹ sư phải xác nhận bằng chứng, số liệu và tiêu chuẩn.</p></details>').join(''))+
 '</section>';
}
function companyDashboard(){
 const s=state(),m=s.companyMetrics||{},p=ownProject();
 const tasks=(s.tasks||[]).filter(t=>t.projectId===p?.id);
 const available=(s.handoffs||[]).filter(x=>x.projectId===p?.id);
 const pending=available.filter(x=>x.status==='open');
 const notices=m.alerts||[];
 return '<section class="panel padded company-suite"><div class="panel-heading"><div><h2>V6.2 · Trung tâm điều hành toàn công ty</h2>'+
 '<p>Ưu tiên dựa trên dữ liệu thật của các dự án được cấp quyền, không dùng số liệu giả.</p></div>'+
 '<span class="mini-label">'+(s.role==='admin'?'TOÀN CÔNG TY':'DỰ ÁN ĐƯỢC CẤP QUYỀN')+'</span></div>'+
 '<div class="company-kpi-grid">'+
 kpi('DỰ ÁN',m.projects||0)+kpi('CÔNG VIỆC',m.tasks||0)+kpi('ĐANG LÀM',m.doing||0)+
 kpi('QUÁ HẠN',m.overdue||0)+kpi('CHỜ DUYỆT',m.review||0)+
 kpi('CHƯA PHÂN CÔNG',m.unassigned||0)+kpi('ƯU TIÊN CAO/KHẨN',m.highPriority||0)+kpi('HỒ SƠ CHỜ XỬ LÝ',m.documentPending||0)+
 kpi('PHỐI HỢP ĐANG MỞ',m.handoffsOpen||0)+'</div>'+
 '<div class="company-notice"><b>Quy trình điều hành:</b> PM tiếp nhận yêu cầu → kỹ sư bộ môn xử lý → phối hợp liên ngành → QA/DOC kiểm tra → Admin phê duyệt → lưu bản phát hành và nhật ký. Agent chỉ đề xuất, không thay vai trò con người.</div>'+
 '<details class="company-raci"><summary><b>📋 Ma trận trách nhiệm RACI – vận hành toàn công ty</b></summary>'+
 '<div class="company-table-wrap"><table class="company-table"><thead><tr><th>Công đoạn</th><th>Chịu trách nhiệm (R)</th><th>Chịu trách nhiệm cuối (A)</th><th>Phối hợp / thẩm tra (C)</th></tr></thead><tbody>'+
 [
  ['Tiếp nhận & phân loại','PM','Ban giám đốc','Kỹ sư bộ môn'],
  ['Giao việc & kế hoạch','PM','Ban giám đốc','PLN / Trưởng bộ môn'],
  ['Thực hiện kỹ thuật','Kỹ sư phụ trách','Trưởng dự án','Agent hỗ trợ / Bộ môn liên quan'],
  ['Phối hợp BIM & hiện trường','BIM / XBI / SIT','PM','MEP / Xây dựng'],
  ['Kiểm soát hồ sơ & QA','DOC / QAC / HSE','PM','Các kỹ sư thiết kế'],
  ['Duyệt nội bộ & phát hành','Admin được ủy quyền','Người có thẩm quyền','QA / DOC / PM']
 ].map(([stage,responsible,accountable,consulted])=>
  '<tr><td>'+h(stage)+'</td><td>'+h(responsible)+'</td><td>'+h(accountable)+'</td><td>'+h(consulted)+'</td></tr>').join('')+
 '</tbody></table></div><p class="company-secondary">RACI chỉ là hướng dẫn tổ chức; quyền phê duyệt thực tế vẫn được máy chủ kiểm tra theo tài khoản Admin. Không đồng nghĩa chữ ký số pháp lý.</p></details>'+
 
 '<h3>Vấn đề cần quản lý giải quyết</h3>'+
 (!notices.length?'<p>Chưa có cảnh báo từ metadata công việc/hồ sơ trong phạm vi được xem.</p>':
 '<div class="company-alert-list">'+notices.map(x=>'<article class="company-alert"><strong>'+
 h(x.title)+'</strong><span>'+h(x.action)+'</span></article>').join('')+'</div>')+
 '<div class="company-controls">'+
 (writable()?'<button class="btn primary" data-company-action="handoff_create">＋ Yêu cầu phối hợp liên phòng</button>':'')+
 (s.role==='admin'?'<button class="btn outline" data-company-action="ops_audit">🛡 Kiểm soát hệ thống & sao lưu</button>':'')+
 '</div></section>'+
 '<section class="panel padded company-suite"><h3>Khối lượng công việc theo bộ môn (các dự án được cấp quyền)</h3>'+
 '<div class="company-table-wrap"><table class="company-table"><thead><tr><th>Phòng ban</th><th>Tổng</th><th>Đang làm</th><th>Chờ duyệt</th><th>Quá hạn</th><th>Agent</th></tr></thead><tbody>'+
 (m.departments||[]).map(d=>'<tr><td>'+h(deptLabel[d.department]||d.department)+'</td>'+
 '<td>'+h(d.count)+'</td><td>'+h(d.doing)+'</td><td>'+h(d.pending)+'</td>'+
 '<td>'+h(d.overdue)+'</td><td>'+h(d.activeAgents)+'</td></tr>').join('')+
 '</tbody></table></div></section>'+
 '<section class="panel padded company-suite"><div class="panel-heading"><h3>V6.2 · Phiếu phối hợp liên phòng</h3>'+
 '<span class="mini-label">'+available.length+' PHIẾU</span></div>'+
 (!available.length?'<p>Chưa có yêu cầu phối hợp. Có thể tạo yêu cầu từ một nhiệm vụ của dự án.</p>':
 '<div class="company-handoff-list">'+available.map(x=>'<article class="company-handoff">'+
 '<div class="company-handoff-heading"><strong>'+h(x.title)+'</strong><span class="company-state">'+
 h(x.status==='open'?'Chờ phối hợp':'Đã xử lý')+'</span></div>'+
 '<p>'+h(deptLabel[x.sourceDept]||x.sourceDept)+' → '+h(deptLabel[x.targetDept]||x.targetDept)+'</p>'+
 '<p><b>Yêu cầu:</b> '+h(x.reason)+'</p>'+
 (x.status==='resolved'?'<p><b>Trả lời:</b> '+h(x.response)+' · '+h(x.resolvedBy)+'</p>':
 (writable()?'<button class="btn outline small" data-handoff-resolve="'+h(x.id)+'">Ghi nhận đã phối hợp</button>':''))+
 '</article>').join('')+'</div>')+
 '</section>'+
 '<section class="panel padded company-suite"><h3>V6.3 · Kiểm soát vận hành</h3>'+
 '<p>Mỗi lần tạo công việc, trình duyệt, chạy Agent hoặc bàn giao đều lưu email và thời gian theo nhật ký đã ký HMAC. Admin có thể kiểm tra và xuất bản sao dữ liệu, không xuất token hay file nhị phân.</p>'+
 '<p class="company-secondary">V6.4–6.6: chuyên gia đã có bộ đọc mẫu PDF/Excel/DXF/IFC và một số công thức kiểm tra có nguồn. Chưa có PostgreSQL sản xuất, worker CAD/BIM cho DWG/RVT hoặc IFC clash hình học, tính toán thiết kế đầy đủ hay ký số pháp lý. Bộ điều phối gồm các cổng kiểm soát, không phải hệ thống tự phê duyệt.</p></section>';
}
export function renderCompanySuite(section){
 if(!state().enabled)return '';
 const base=projectPicker(section);
 return base+(section==='agents'?agentCards()+runHistory():companyDashboard());
}
function send(section,op,taskId='',agentId='',handoffId=''){
 const token=window.__xdDriveNonce;
 const p=ownProject();
 if(!token||!p)return;
 const id=(globalThis.crypto?.randomUUID?.()||String(Date.now())+'-'+Math.random().toString().slice(2)).replace(/-/g,'').slice(0,32);
 window.parent.postMessage({
  channel:'XD_MEP_DRIVE_V1',nonce:token,
  kind:'workspace',section,op,projectId:p.id,taskId,agentId,handoffId,actionId:id
 },'*');
}
export function bindCompanySuite(root,section){
 root.querySelectorAll('.company-project-select').forEach(select=>{
  select.addEventListener('change',event=>{
   const token=window.__xdDriveNonce;
   if(!token)return;
   const id=(globalThis.crypto?.randomUUID?.()||String(Date.now())+'-'+Math.random().toString().slice(2)).replace(/-/g,'').slice(0,32);
   window.parent.postMessage({channel:'XD_MEP_DRIVE_V1',nonce:token,kind:'workspace',
    section,op:'select',projectId:event.target.value,actionId:id},'*');
  });
 });
 root.querySelectorAll('[data-company-action]').forEach(button=>{
  button.addEventListener('click',()=>send(section,button.dataset.companyAction));
 });
 root.querySelectorAll('[data-agent-execute]').forEach(button=>{
  button.addEventListener('click',()=>{
   if(!writable())return;
   const agentId=button.dataset.agentExecute;
   const taskId=root.querySelector('[data-agent-task="'+agentId+'"]')?.value||'';
   if(taskId)send('agents','agent_run',taskId,agentId);
  });
 });
 root.querySelectorAll('[data-handoff-resolve]').forEach(button=>{
  button.addEventListener('click',()=>{
   if(writable())send('company','handoff_resolve','','',button.dataset.handoffResolve);
  });
 });
}

/* Read-only reporting sheet; the dashboard is not a duplicate write screen. */
export function renderCompanyReport(){
 const s=state(),m=s.companyMetrics||{},tasks=s.tasks||[],handoffs=s.handoffs||[];
 const projectCount=(s.projects||[]).length;
 const statusKeys=['todo','working','review','done'];
 const statusLabels={todo:'Chưa bắt đầu',working:'Đang làm',review:'Chờ duyệt',done:'Hoàn thành'};
 const counts=Object.fromEntries(statusKeys.map(k=>[k,tasks.filter(t=>t.status===k).length]));
 const total=tasks.length;
 const complete=total?((counts.done/total)*100).toFixed(1)+'%':'—';
 const grouped=new Map();
 for(const task of tasks){
  const dept=task.dept||'director';
  grouped.set(dept,(grouped.get(dept)||0)+1);
 }
 const top=[...grouped].sort((a,b)=>b[1]-a[1]).slice(0,12);
 const max=top.length?Math.max(...top.map(x=>x[1]),1):1;
 const crossCount=handoffs.filter(x=>{
  const a=division(x.sourceDept),b=division(x.targetDept);
  return (a==='MEP'&&b==='Xây dựng')||(a==='Xây dựng'&&b==='MEP');
 }).length;
 const projects=(s.projects||[]).map(p=>{
  const ts=tasks.filter(t=>t.projectId===p.id),done=ts.filter(t=>t.status==='done').length;
  const open=handoffs.filter(x=>x.projectId===p.id&&x.status==='open').length;
  return '<tr><td><b>'+h(p.code)+'</b> · '+h(p.name)+'</td><td>'+ts.length+
    '</td><td>'+done+'</td><td>'+open+'</td></tr>';
 }).join('');
 return '<section class="panel padded company-suite command-report">'+
 '<div class="panel-heading"><div><h2>▥ Báo cáo & Thống kê toàn công ty</h2>'+
 '<p>Thống kê dựa trên Google Drive đã xác thực; chỉ tổng hợp dự án được cấp quyền.</p></div>'+
 '<span class="mini-label">'+(s.role==='admin'?'ADMIN':'THEO QUYỀN')+'</span></div>'+
 '<div class="company-kpi-grid">'+
 kpi('DỰ ÁN',projectCount)+kpi('CÔNG VIỆC',total)+kpi('HOÀN THÀNH',counts.done)+
 kpi('TỶ LỆ HOÀN THÀNH',complete)+kpi('PHỐI HỢP LIÊN HỆ',crossCount)+
 kpi('PHIẾU CHỜ XỬ LÝ',handoffs.filter(x=>x.status==='open').length)+
 kpi('QUÁ HẠN',m.overdue||0)+kpi('CHỜ DUYỆT',counts.review)+'</div>'+
 '<div class="command-report-grid"><section class="panel padded"><h3>Trạng thái công việc</h3>'+
 (total?statusKeys.map(k=>'<div class="command-report-row"><span>'+statusLabels[k]+'</span>'+
 '<div class="command-report-track"><b style="width:'+(100*counts[k]/total).toFixed(1)+'%"></b></div>'+
 '<strong>'+counts[k]+'</strong></div>').join(''):'<p>Chưa có công việc được ghi nhận.</p>')+
 '</section><section class="panel padded"><h3>Khối lượng theo bộ môn</h3>'+
 (top.length?top.map(([dept,n])=>'<div class="command-report-row"><span>'+h(deptLabel[dept]||dept)+'</span>'+
 '<div class="command-report-track"><b style="width:'+(100*n/max).toFixed(1)+'%"></b></div>'+
 '<strong>'+n+'</strong></div>').join(''):'<p>Chưa có số liệu bộ môn.</p>')+
 '</section></div>'+
 '<section class="panel padded"><h3>Tổng hợp dự án</h3><div class="company-table-wrap">'+
 '<table class="company-table"><thead><tr><th>Dự án</th><th>Công việc</th><th>Hoàn thành</th><th>Phối hợp đang mở</th></tr></thead>'+
 '<tbody>'+projects+'</tbody></table></div></section>'+
 '<p class="company-secondary">Đây là báo cáo trạng thái hiện tại. Giám sát Agent hiển thị sự kiện theo thời gian và luồng hai chiều MEP ↔ XD; không có số giả hoặc quyền duyệt mới.</p></section>';
}
