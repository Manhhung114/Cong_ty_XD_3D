/* V7.0 CEO Command Center: visualize only authorized signed project data.
   No synthetic activity, worker heartbeat, or autonomous agent execution. */
import {AGENTS} from './config.js';
import {agentEvidence,agentEvidenceSummary} from './agent_live.js';
const h=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stageName={
 ceo:'Giám đốc CEO',pm:'Quản lý dự án PM',lead:'Trưởng bộ môn',
 expert:'Chuyên gia',qa:'QA/QC độc lập'
};
const stageOrder={ceo:0,pm:1,lead:2,expert:3,qa:4};
const statusName={
 todo:'Chờ xử lý',working:'Đang thực hiện',review:'Chờ duyệt',
 done:'Đã phê duyệt',cancelled:'Đã hủy'
};
const planName={
 pending:'Chờ Admin duyệt',dispatched:'Đã phân phối',
 rejected:'Đã trả phương án',stopped:'Đã dừng'
};
const when=raw=>{
 if(!raw||!Number.isFinite(Date.parse(raw)))return '—';
 return new Date(raw).toLocaleString('vi-VN',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit'});
};
function scopeData(cloud,selected='all'){
 const valid=new Set((cloud?.projects||[]).map(p=>p.id));
 const permitted=id=>valid.has(id)&&(selected==='all'||id===selected);
 return {
  projects:(cloud?.projects||[]).filter(p=>permitted(p.id)),
  tasks:(cloud?.tasks||[]).filter(t=>permitted(t.projectId)),
  plans:(cloud?.hierarchyPlans||[]).filter(p=>permitted(p.projectId)),
  activity:(cloud?.agentActivity||[]).filter(a=>permitted(a.projectId)),
 };
}
export function renderCEOCommandCenter(cloud,project='all'){
 const {projects,tasks,plans,activity}=scopeData(cloud,project);
 const titles=new Map(tasks.map(t=>[t.id,t]));
 const codes=new Map(projects.map(p=>[p.id,p.code]));
 const live=agentEvidenceSummary(cloud,project);
 const open=tasks.filter(t=>t.status!=='done'&&t.status!=='cancelled').length;
 const waiting=plans.filter(p=>p.status==='pending').length;
 const failures=activity.filter(a=>agentEvidence(cloud,a.agentId,project).state==='failed').length;
 const groups=plans.slice().sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt))).slice(0,8);
 const lines=groups.map(plan=>{
  const root=titles.get(plan.rootTaskId);
  if(!root)return '';
  const tree=tasks.filter(t=>t.id===root.id||t.rootTaskId===root.id);
  tree.sort((a,b)=>(stageOrder[a.hierarchyStage]??99)-(stageOrder[b.hierarchyStage]??99));
  const progress=tree.filter(t=>t.status==='done').length;
  const nodes=tree.map(t=>{
   const stage=t.hierarchyStage||'ceo';
   const blocked=t.hierarchyProgress?.blockedBy?.length||0;
   const last=activity.find(a=>a.taskId===t.id&&a.agentId===t.assignedAgentId);
   return '<div class="v70-tree-node v70-stage-'+h(stage)+'">'+
    '<div class="v70-tree-stage">'+h(stageName[stage]||stage)+'</div>'+
    '<strong>'+h(t.code||t.id)+'</strong>'+
    '<span>'+h(t.title)+'</span>'+
    '<small>Agent '+h(t.assignedAgentId||'Chưa gán')+' · '+h(t.assignee||'Chưa có người phụ trách')+'</small>'+
    '<span class="v70-task-state">'+h(statusName[t.status]||t.status)+
    (blocked?' · Chờ '+blocked+' tiền nhiệm':'')+'</span>'+
    (last?'<small class="v70-evidence">Lượt Agent: '+h(agentEvidence(cloud,last.agentId,project).label)+'</small>':'')+
    '</div>';
  }).join('');
  return '<details class="v70-hierarchy"'+(groups.length===1?' open':'')+'><summary>'+
   '<span><b>'+h(codes.get(plan.projectId)||'Dự án')+' · '+h(root.title)+'</b>'+
   '<small>'+h(planName[plan.status]||plan.status)+' · '+
   progress+'/'+tree.length+' nhiệm vụ đã duyệt</small></span>'+
   '<span class="v70-hierarchy-toggle">Chi tiết</span></summary>'+
   '<div class="v70-node-rail">'+nodes+'</div>'+
   '<p class="v70-hint">Mũi tên thể hiện quan hệ phân cấp theo công việc có chữ ký; '+
   'Agent chỉ chạy sau khi người có quyền kích hoạt. Không tự sinh kết quả.</p></details>';
 }).join('');
 const cards=AGENTS.map(a=>{
  const e=agentEvidence(cloud,a.id,project);
  const state=e.state;
  return '<details class="v70-agent-card v70-state-'+h(state)+'"><summary>'+
   '<strong class="v70-agent-id">'+h(a.id)+'</strong><span>'+h(a.name)+'</span>'+
   '<small>'+h(e.label)+'</small></summary>'+
   '<p><b>Nhiệm vụ:</b> '+h(e.taskCode||'—')+' · '+h(e.taskTitle||'Chưa có lượt chạy đã ký')+'</p>'+
   '<p><b>Thời điểm:</b> '+h(when(e.at))+'</p>'+
   (e.detail?'<p><b>Chi tiết:</b> '+h(e.detail)+'</p>':'')+
   '<p class="v70-hint">Không có heartbeat máy chủ; không suy diễn Agent đang chạy từ trạng thái công việc.</p>'+
   '</details>';
 }).join('');
 return '<section class="v70-ceo-control" aria-label="Trung tâm điều phối CEO V7.0">'+
  '<div class="v70-ceo-head"><div><span class="v70-kicker">V7.0 · CEO COMMAND CENTER</span>'+
  '<h3>Điều phối công ty AI 3D</h3><p>Dữ liệu thật theo dự án được phép xem · nhật ký Google Drive có chữ ký</p></div>'+
  '<div class="v70-ceo-counts"><span><strong>'+plans.length+'</strong> phương án</span>'+
  '<span><strong>'+waiting+'</strong> chờ duyệt</span>'+
  '<span><strong>'+open+'</strong> việc mở</span>'+
  '<span><strong>'+live.started_unconfirmed+'</strong> đã bắt đầu*</span>'+
  '<span><strong>'+failures+'</strong> lỗi gần nhất</span></div></div>'+
  '<p class="v70-warning">* “Đã bắt đầu” chỉ có sự kiện ký số, không có heartbeat hay worker chạy nền. '+
  'Sau 120 giây chưa có kết thúc, chuyển sang “Chưa xác nhận tiến trình”.</p>'+
  '<h4>Luồng phân phối CEO → PM → Trưởng bộ môn → Chuyên gia & QA</h4>'+
  (lines||'<div class="v70-empty">Chưa có phương án phân phối CEO trong phạm vi đã chọn. '+
   'Vào Công việc → giao nhiệm vụ CEO → Giám đốc lập phương án → Admin duyệt để tạo cây thật.</div>')+
  '<h4>18 Agent · trạng thái từ sự kiện thực thi đã ký</h4>'+
  '<div class="v70-agent-grid">'+cards+'</div>'+
  '</section>';
}
