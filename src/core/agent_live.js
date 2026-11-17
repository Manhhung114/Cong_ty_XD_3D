/* V7.0: verified status from server-signed Agent lifecycle events only.
   A task in "working" is NOT proof its AI Agent is executing. The app has
   no worker heartbeat, so a recent start is labelled unconfirmed. */
const safeDate=value=>{const n=Date.parse(value||'');return Number.isFinite(n)?n:0;};
export const AGENT_LIVE_LABELS={
 queued:'Trong hàng đợi Redis/Celery',
 running:'Đang xử lý · worker có heartbeat',
 unconfirmed:'Không xác nhận được worker',
 cancelled:'Đã hủy lượt xử lý',
 dispatch_failed:'Không kết nối được hàng đợi',
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
 const queued=(cloud?.runtimeJobs||[]).filter(job=>job.agentId===agentId&&
   (!selected||job.projectId===selected)).sort((a,b)=>
   safeDate(b.endedAt||b.heartbeatAt||b.createdAt)-
   safeDate(a.endedAt||a.heartbeatAt||a.createdAt))[0];
 const runtimeAt=queued?safeDate(queued.endedAt||queued.heartbeatAt||queued.createdAt):0;
 if(queued&&(!record||runtimeAt>=safeDate(record.at))){
  const state=AGENT_LIVE_LABELS[queued.state]?queued.state:'unconfirmed';
  return {...queued,at:queued.endedAt||queued.heartbeatAt||queued.createdAt,
   state,label:AGENT_LIVE_LABELS[state],verified:true,
   hasHeartbeat:queued.state==='running'&&queued.hasHeartbeat===true,
   detail:(state==='running'?('Tiến độ '+queued.progress+'% · '+queued.phase):
     state==='failed'?(FAILURE_LABELS[queued.failureCode]||FAILURE_LABELS.internal):
     queued.phase||''),
   workerProgress:queued.progress,
   billingVerified:queued.billingVerified===true,
  };
 }
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
 const rows=[
  ...(cloud?.agentActivity||[]),
  ...(cloud?.runtimeJobs||[]),
 ].filter(a=>!selected||a.projectId===selected);
 const counts={queued:0,running:0,unconfirmed:0,started_unconfirmed:0,
   stale:0,completed:0,failed:0,cancelled:0,dispatch_failed:0};
 const ids=new Set(rows.map(r=>r.agentId));
 for(const id of ids){
  const e=agentEvidence(cloud,id,projectId==='all'?'all':selected);
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
