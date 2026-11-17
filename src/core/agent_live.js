/* V7.0: verified status from server-signed Agent lifecycle events only.
   A task in "working" is NOT proof its AI Agent is executing. The app has
   no worker heartbeat, so a recent start is labelled unconfirmed. */
const safeDate=value=>{const n=Date.parse(value||'');return Number.isFinite(n)?n:0;};
export const AGENT_LIVE_LABELS={
 started_unconfirmed:'Đã bắt đầu · chưa có heartbeat',
 stale:'Chưa xác nhận tiến trình',
 completed:'Đã lưu báo cáo nháp',
 failed:'Thực thi thất bại',
 idle:'Chưa có lượt thực thi đã xác minh',
};
export const FAILURE_LABELS={
 provider:'Lỗi nhà cung cấp AI', quota:'Hạn mức gọi AI',
 network:'Lỗi kết nối mạng', drive:'Lỗi Google Drive',
 validation:'Dữ liệu đầu vào chưa hợp lệ',permission:'Không có quyền',
 resource:'Giới hạn tài nguyên',internal:'Lỗi máy chủ',
};
export function agentEvidence(cloud,agentId,projectId='',clock=Date.now()){
 const selected=projectId==='all'?'':(projectId||cloud?.selectedProjectId||'');
 const items=(cloud?.agentActivity||[]).filter(a=>
   a.agentId===agentId&&(!selected||a.projectId===selected));
 const record=items.sort((a,b)=>safeDate(b.at)-safeDate(a.at))[0];
 if(!record)return {state:'idle',label:AGENT_LIVE_LABELS.idle,verified:false,
                      hasHeartbeat:false,taskId:'',at:''};
 const age=Math.max(0,(clock-safeDate(record.at))/1000);
 // Downgrade stale starts on the client even if the embedded iframe is old.
 const state=record.state==='started_unconfirmed'&&age>120?'stale':
   ['started_unconfirmed','stale','completed','failed'].includes(record.state)?
   record.state:'idle';
 return {...record,state,label:AGENT_LIVE_LABELS[state],
  verified:state!=='idle',hasHeartbeat:false,
  detail:state==='failed'?(FAILURE_LABELS[record.failureCode]||FAILURE_LABELS.internal):
    state==='stale'?'Không có sự kiện hoàn thành/lỗi và không có heartbeat':record.mode||''};
}
export function agentEvidenceSummary(cloud,projectId=''){
 const selected=projectId==='all'?'':(projectId||cloud?.selectedProjectId||'');
 const rows=(cloud?.agentActivity||[]).filter(a=>!selected||a.projectId===selected);
 const counts={started_unconfirmed:0,stale:0,completed:0,failed:0};
 for(const r of rows){
  const e=agentEvidence(cloud,r.agentId,selected);
  if(Object.prototype.hasOwnProperty.call(counts,e.state))counts[e.state]++;
 }
 return counts;
}
export function selectedAgentTask(cloud,agentId,projectId=''){
 const selected=projectId==='all'?'':(projectId||cloud?.selectedProjectId||'');
 const items=(cloud?.tasks||[]).filter(t=>
  (!selected||t.projectId===selected)&&t.assignedAgentId===agentId&&
  !['done','cancelled'].includes(t.status));
 return items[0]||null;
}
