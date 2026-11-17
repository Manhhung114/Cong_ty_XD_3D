/* V6.7 — near-real-time signed event monitor, no mock data.
   Native SVG charts avoid CDN/Plotly dependencies in Streamlit srcdoc iframe.
   Separate MEP & XD; actual cross-system handoffs, no invented agent edges. */
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const st=()=>window.__xdCloud||{};
const mon=()=>st().monitorData||null;
const systemFor=d=>['electrical','hvac','plumbing','fire','bim','qs','qa'].includes(d)?'mep':
 ['architecture','structure','xd_bim','xd_qs','xd_planning','xd_site','xd_safety','xd_material'].includes(d)?'xd':'shared';
const departments={
 director:'Ban giám đốc',electrical:'Điện',hvac:'HVAC',plumbing:'Cấp thoát nước',fire:'PCCC',
 bim:'BIM MEP',qs:'QS MEP',qa:'QA/QC MEP',architecture:'Kiến trúc',structure:'Kết cấu',
 xd_bim:'BIM XD',xd_qs:'QS XD',xd_planning:'Kế hoạch XD',xd_site:'Thi công',
 xd_safety:'HSE XD',xd_material:'Vật tư XD'
};
const actions={
 'project.created':'Tạo dự án','task.created':'Tạo công việc','task.started':'Bắt đầu công việc',
 'task.submitted':'Trình duyệt công việc','task.approved':'Đã duyệt công việc',
 'task.returned':'Trả lại công việc','agent.completed':'Agent hoàn thành phân tích',
 'handoff.requested':'Gửi phiếu phối hợp','handoff.resolved':'Đóng phiếu phối hợp',
 'document.registered':'Đăng ký hồ sơ','document.metadata_updated':'Sửa thông tin hồ sơ',
 'document.submitted':'Trình hồ sơ','document.approved':'Duyệt hồ sơ',
 'document.returned':'Trả lại hồ sơ','document.archived':'Lưu trữ hồ sơ'
};
const tz='Asia/Ho_Chi_Minh';
const localDay=raw=>new Intl.DateTimeFormat('sv-SE',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(raw));
const localHour=raw=>new Intl.DateTimeFormat('vi-VN',{timeZone:tz,hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(raw));
const fmtTime=raw=>raw?localHour(raw)+' · '+localDay(raw):'—';
const minutesBetween=(start,end)=>Math.max(0,(new Date(end).getTime()-new Date(start).getTime())/60000);
const timeDuration=minutes=>{
 if(!Number.isFinite(minutes))return '—';
 if(minutes<60)return Math.round(minutes)+'p';
 const hours=Math.floor(minutes/60),mins=Math.round(minutes%60);
 return hours+'g '+mins+'p';
};
const colors={cyan:'#22c6f4',green:'#27ddab',amber:'#ffbc4a',purple:'#b68aff',pink:'#ef81d8',
 blue:'#3aa4ff',red:'#ff6877',grey:'#8ea9bc',xd:'#a07cf6',mep:'#27c8eb'};
const parseAt=raw=>{const n=Date.parse(raw||'');return Number.isFinite(n)?n:NaN;};
let activeFilters=null;
function filters(){
 const saved=st().monitorPreferences||{};
 return activeFilters||{
  project:saved.project||'all',system:saved.system||'all',
  period:saved.period||'today',department:saved.department||'all',
 };
}
function viewPeriod(at,period,now){
 const stamp=parseAt(at);
 if(!Number.isFinite(stamp)||stamp>now+300000)return false;
 if(period==='hour')return stamp>=now-3600000;
 if(period==='week')return localDay(stamp)>=localDay(now-6*86400000)&&localDay(stamp)<=localDay(now);
 return localDay(stamp)===localDay(now);
}
function isCross(row){
 return row.relation==='mep_to_xd'||row.relation==='xd_to_mep';
}
function matchSystem(row,mode){
 if(mode==='all')return true;
 if(mode==='cross')return isCross(row);
 const src=systemFor(row.sourceDept),dst=systemFor(row.targetDept);
 return row.system===mode||src===mode||dst===mode;
}
function matchScope(row,f){
 if(f.project!=='all'&&row.projectId!==f.project)return false;
 if(!matchSystem(row,f.system))return false;
 if(f.department!=='all'&&![
  row.department,row.sourceDept,row.targetDept,row.dept
 ].includes(f.department))return false;
 return true;
}
export function summarizeMonitor(packet,f,nowDate){
 const now=nowDate instanceof Date?nowDate.getTime():Date.parse(packet?.asOf||'');
 if(!packet||packet.schema!=='XD_MEP_MONITOR_V67'||!Number.isFinite(now)){
  return null;
 }
 const within=at=>viewPeriod(at,f.period,now);
 const events=(packet.events||[]).filter(e=>matchScope(e,f)&&within(e.at))
  .slice().sort((a,b)=>b.at.localeCompare(a.at));
 const tasks=(packet.tasks||[]).filter(t=>matchScope(t,f));
 const handoffs=(packet.handoffs||[]).filter(h=>matchScope(h,f));
 const handoffWindow=handoffs.filter(h=>within(h.createdAt));
 const solved=handoffs.filter(h=>h.status==='resolved'&&within(h.resolvedAt)&&
  Number.isFinite(minutesBetween(h.createdAt,h.resolvedAt)));
 const responseMinutes=solved.length?
  solved.reduce((n,h)=>n+minutesBetween(h.createdAt,h.resolvedAt),0)/solved.length:null;
 const today=localDay(now);
 const overdue=tasks.filter(t=>t.dueDate&&t.dueDate<today&&t.status!=='done');
 const reviewStale=tasks.filter(t=>t.status==='review'&&t.reviewSince&&
  now-parseAt(t.reviewSince)>86400000);
 const pending=handoffs.filter(h=>h.status==='open');
 const staleHandoffs=pending.filter(h=>now-parseAt(h.createdAt)>4*3600000);
 const agentRuns=events.filter(e=>e.action==='agent.completed');
 const taskEvents=events.filter(e=>e.action.startsWith('task.'));
 const activeAgentIds=new Set(agentRuns.map(e=>e.agentId).filter(Boolean));
 const complete=tasks.filter(t=>t.status==='done');
 const deptCounts=new Map(),agentCounts=new Map(),flows=new Map(),handoffCounts=new Map();
 for(const e of agentRuns){
  deptCounts.set(e.department,(deptCounts.get(e.department)||0)+1);
  agentCounts.set(e.agentId,(agentCounts.get(e.agentId)||0)+1);
 }
 for(const h of handoffWindow){
  const key=h.sourceDept+'|'+h.targetDept;
  flows.set(key,(flows.get(key)||0)+1);
  handoffCounts.set(h.targetDept,(handoffCounts.get(h.targetDept)||0)+1);
 }
 const counts={todo:0,working:0,review:0,done:0};
 for(const t of tasks)if(Object.prototype.hasOwnProperty.call(counts,t.status))counts[t.status]++;
 const alerts=[];
 if(staleHandoffs.length)alerts.push({level:'critical',
  title:staleHandoffs.length+' phiếu phối hợp quá 4 giờ',
  detail:'Phòng nhận cần phản hồi hoặc cập nhật trạng thái'});
 if(overdue.length)alerts.push({level:'critical',
  title:overdue.length+' công việc quá hạn',detail:'PM kiểm tra người phụ trách và mốc tiến độ'});
 if(reviewStale.length)alerts.push({level:'warning',
  title:reviewStale.length+' công việc chờ duyệt trên 24 giờ',detail:'QA/PM đối chiếu chứng cứ trước khi duyệt'});
 const pendingByTarget=new Map();
 for(const h of pending)pendingByTarget.set(h.targetDept,(pendingByTarget.get(h.targetDept)||0)+1);
 for(const [dept,n] of [...pendingByTarget].sort((a,b)=>b[1]-a[1]).slice(0,1)){
  if(n>=5)alerts.push({level:'warning',
    title:departments[dept]+' đang nhận '+n+' phiếu chưa xử lý',
    detail:'Có thể cần bố trí thêm người phối hợp'});
 }
 return {
  now,events,tasks,handoffs,handoffWindow,solved,responseMinutes,pending,
  staleHandoffs,overdue,reviewStale,counts,
  agentRuns:agentRuns.length,taskEvents:taskEvents.length,
  agentsActiveInPeriod:activeAgentIds.size,
  completionRate:tasks.length?complete.length/tasks.length*100:null,
  departments:[...deptCounts].sort((a,b)=>b[1]-a[1]),
  agents:[...agentCounts].sort((a,b)=>b[1]-a[1]),
  flows:[...flows].map(([key,value])=>({source:key.split('|')[0],target:key.split('|')[1],value}))
   .sort((a,b)=>b.value-a.value),
  bottleneck:[...pendingByTarget].sort((a,b)=>b[1]-a[1]),
  alerts,
 };
}
const svg=(inside,box='0 0 700 250',title='Biểu đồ')=>'<svg class="v67-svg" viewBox="'+box+
 '" role="img" aria-label="'+esc(title)+'" preserveAspectRatio="xMidYMid meet">'+inside+'</svg>';
const empty=msg=>'<div class="v67-empty"><span>◌</span><p>'+esc(msg)+'</p></div>';
function bucketsOf(period,now){
 if(period==='hour'){
  return Array.from({length:12},(_,i)=>{
   const time=new Date(now-(11-i)*300000);
   return {at:time.getTime(),label:localHour(time),key:Math.floor(time.getTime()/300000)};
  });
 }
 if(period==='week'){
  return Array.from({length:7},(_,i)=>{
   const time=new Date(now-(6-i)*86400000);
   return {at:time.getTime(),label:localDay(time).slice(5),key:localDay(time)};
  });
 }
 return Array.from({length:24},(_,i)=>({at:i,label:String(i).padStart(2,'0')+':00',
  key:localDay(now)+'-'+i}));
}
function bucketFor(at,period){
 const d=new Date(at);
 if(period==='hour')return Math.floor(d.getTime()/300000);
 if(period==='week')return localDay(d);
 const hr=new Intl.DateTimeFormat('en-GB',{timeZone:tz,hour:'2-digit',hour12:false}).format(d);
 return localDay(d)+'-'+Number(hr==='24'?0:hr);
}
function activityChart(s,f){
 if(!s.events.length)return empty('Chưa có sự kiện trong khoảng thời gian đã chọn');
 const buckets=bucketsOf(f.period,s.now);
 const keys=['task','agent','handoff','approval'];
 const palette={task:colors.cyan,agent:colors.green,handoff:colors.amber,approval:colors.pink};
 const labels={task:'Công việc',agent:'Agent',handoff:'Phối hợp',approval:'Phê duyệt'};
 const values=Object.fromEntries(keys.map(k=>[k,buckets.map(()=>0)]));
 const idx=new Map(buckets.map((b,i)=>[String(b.key),i]));
 for(const e of s.events){
  const key=String(bucketFor(e.at,f.period));
  const j=idx.get(key);
  if(j===undefined)continue;
  const channel=e.action==='agent.completed'?'agent':
   e.action.startsWith('handoff.')?'handoff':
   /^(task|document)\.(approved|returned)$/.test(e.action)?'approval':
   e.action.startsWith('task.')?'task':null;
  if(channel)values[channel][j]++;
 }
 const max=Math.max(1,...Object.values(values).flat());
 const left=48,right=662,top=18,bottom=202;
 const grid=Array.from({length:5},(_,i)=>{
  const y=top+(bottom-top)*i/4;
  return '<line x1="'+left+'" y1="'+y+'" x2="'+right+'" y2="'+y+'" stroke="#27465a" stroke-width=".8"/>'+
  '<text x="35" y="'+(y+4)+'" text-anchor="end" fill="#7facc6" font-size="11">'+Math.round(max*(4-i)/4)+'</text>';
 }).join('');
 const timeLabels=buckets.map((b,i)=>i%(f.period==='today'?4:f.period==='hour'?2:1)===0?
  '<text x="'+(left+(right-left)*i/(buckets.length-1))+'" y="228" fill="#90b6c8" font-size="11" text-anchor="middle">'+esc(b.label)+'</text>':'').join('');
 const paths=keys.map(k=>{
  const data=values[k];
  const points=data.map((v,i)=>[left+(right-left)*i/(buckets.length-1),bottom-(bottom-top)*v/max]);
  const path=points.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  return '<path d="'+path+'" fill="none" stroke="'+palette[k]+'" stroke-width="2.8" stroke-linecap="round"/>'+
  points.map((p,i)=>i%(f.period==='today'?3:1)===0?
    '<circle class="v67-chart-point" cx="'+p[0]+'" cy="'+p[1]+'" r="4" fill="'+palette[k]+'">'+
    '<title>'+esc(buckets[i].label)+' · '+esc(labels[k])+': '+data[i]+' lượt</title></circle>':'').join('');
 }).join('');
 return '<div class="v67-plot">'+svg(grid+paths+timeLabels,'0 0 700 245','Hoạt động theo thời gian')+'</div>'+
 '<div class="v67-legend">'+keys.map(k=>'<span><i style="background:'+palette[k]+'"></i>'+labels[k]+'</span>').join('')+'</div>';
}
function donutChart(s){
 const vals=s.counts;
 const entries=[
  ['todo','Chưa bắt đầu',colors.cyan],['working','Đang làm',colors.amber],
  ['review','Chờ duyệt',colors.purple],['done','Hoàn thành',colors.green]
 ];
 const sum=entries.reduce((n,[k])=>n+vals[k],0);
 if(!sum)return empty('Chưa có công việc thuộc phạm vi đang xem');
 let offset=0;
 const rings=entries.map(([k,label,color])=>{
  const portion=vals[k]/sum;
  const part='<circle cx="108" cy="106" r="64" fill="none" stroke="'+color+
    '" stroke-width="23" stroke-dasharray="'+(portion*402.12).toFixed(2)+' 402.12"'+
    ' stroke-dashoffset="'+(-offset*402.12).toFixed(2)+'" transform="rotate(-90 108 106)"/>';
  offset+=portion;return part;
 }).join('');
 const center='<text x="108" y="104" font-size="27" fill="#f1fbff" text-anchor="middle" font-weight="750">'+sum+
 '</text><text x="108" y="122" font-size="11" fill="#a3c4d4" text-anchor="middle">Công việc</text>';
 return '<div class="v67-donut-wrap">'+svg(rings+center,'0 0 220 220','Tỷ lệ trạng thái công việc')+
 '<div class="v67-donut-list">'+entries.map(([k,label,color])=>
 '<div><i style="background:'+color+'"></i><span>'+label+'</span><strong>'+vals[k]+'</strong></div>').join('')+
 '</div></div>';
}
function barChart(items,maxBars=7){
 const vals=items.slice(0,maxBars);
 if(!vals.length)return empty('Chưa có dữ liệu hoạt động theo bộ môn');
 const max=Math.max(1,...vals.map(x=>x[1]));
 return '<div class="v67-bar-list">'+vals.map(([dept,n])=>{
  const color=systemFor(dept)==='xd'?colors.xd:systemFor(dept)==='mep'?colors.cyan:colors.amber;
  return '<div class="v67-bar-row"><span title="'+esc(departments[dept]||dept)+'">'+
   esc(departments[dept]||dept)+'</span><div class="v67-bar-track"><b style="width:'+
   (n/max*100).toFixed(1)+'%;background:'+color+'"></b></div><strong>'+n+'</strong></div>';
 }).join('')+'</div>';
}
function sankeyChart(flows){
 const list=flows.slice(0,18);
 if(!list.length)return empty('Chưa có phiếu phối hợp trong kỳ giữa các bộ môn MEP/XD');
 const sources=[...new Set(list.map(x=>x.source))].slice(0,7);
 const targets=[...new Set(list.map(x=>x.target))].slice(0,7);
 const layout=(arr,x)=>arr.map((id,i)=>({id,x,y:32+i*(230/Math.max(1,arr.length-1))}));
 const left=layout(sources,110),right=layout(targets,580);
 const coords=new Map([...left.map(p=>['L'+p.id,p]),...right.map(p=>['R'+p.id,p])]);
 const max=Math.max(1,...list.map(x=>x.value));
 const links=list.map(x=>{
  const a=coords.get('L'+x.source),b=coords.get('R'+x.target);
  if(!a||!b)return '';
  const c=systemFor(x.source)==='xd'?colors.xd:colors.cyan;
  const width=2+16*x.value/max;
  return '<path d="M '+(a.x+54)+' '+a.y+' C 300 '+a.y+', 380 '+b.y+', '+(b.x-54)+' '+b.y+
   '" fill="none" stroke="'+c+'" stroke-opacity=".27" stroke-width="'+width.toFixed(1)+'">'+
   '<title>'+esc((departments[x.source]||x.source)+' → '+(departments[x.target]||x.target)+': '+x.value+' lượt')+'</title></path>';
 }).join('');
 const nodes=[...left,...right].map((p,i)=>{
  const name=departments[p.id]||p.id;const x=p.x, y=p.y;
  const color=systemFor(p.id)==='xd'?colors.xd:systemFor(p.id)==='mep'?colors.cyan:colors.amber;
  return '<rect x="'+(x-54)+'" y="'+(y-15)+'" width="108" height="30" rx="9" fill="#102f47" stroke="'+color+'" stroke-width="1.7"/>'+
   '<text x="'+x+'" y="'+(y+4)+'" fill="#e0f5ff" text-anchor="middle" font-size="11">'+esc(name.length>16?name.slice(0,15)+'…':name)+'</text>';
 }).join('');
 return svg(links+nodes,'0 0 690 290','Sankey luồng phối hợp thực MEP và Xây dựng')+
 '<p class="v67-note">Chiều mũi tên: phòng gửi → phòng nhận. Bề dày đường = số phiếu phát sinh trong kỳ.</p>';
}
function networkChart(flows){
 if(!flows.length)return empty('Chưa có mạng phối hợp thực tế');
 const counts=new Map();
 for(const row of flows){
  counts.set(row.source,(counts.get(row.source)||0)+row.value);
  counts.set(row.target,(counts.get(row.target)||0)+row.value);
 }
 const nodes=[...counts.keys()].sort((a,b)=>counts.get(b)-counts.get(a)).slice(0,9);
 const pos=new Map(nodes.map((id,i)=>{
  const angle=-Math.PI/2+(2*Math.PI*i/nodes.length);
  return [id,{x:255+180*Math.cos(angle),y:142+104*Math.sin(angle)}];
 }));
 const max=Math.max(1,...flows.map(f=>f.value));
 const lines=flows.map(row=>{
  const a=pos.get(row.source),b=pos.get(row.target);
  if(!a||!b)return '';
  return '<line x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+
  '" stroke="'+(systemFor(row.source)===systemFor(row.target)?colors.cyan:colors.pink)+
  '" stroke-width="'+(1+3*row.value/max).toFixed(1)+'" opacity=".55"/>';
 }).join('');
 const shapes=nodes.map(id=>{
  const p=pos.get(id),system=systemFor(id);
  const color=system==='xd'?colors.xd:system==='mep'?colors.cyan:colors.amber;
  return '<circle cx="'+p.x+'" cy="'+p.y+'" r="24" fill="#102c43" stroke="'+color+'" stroke-width="2.5"/>'+
    '<text x="'+p.x+'" y="'+(p.y+4)+'" fill="#eafaff" font-size="10" text-anchor="middle">'+esc(id.toUpperCase().slice(0,5))+'</text>';
 }).join('');
 return svg(lines+shapes,'0 0 510 280','Mạng lưới phối hợp các bộ môn, theo phiếu thật');
}
function timelineChart(s){
 const list=s.handoffs.slice().sort((a,b)=>b.createdAt.localeCompare(a.createdAt)).slice(0,5);
 if(!list.length)return empty('Chưa có phiếu phối hợp được ghi nhận');
 const max=Math.max(1,...list.map(h=>minutesBetween(h.createdAt,h.resolvedAt||new Date(s.now).toISOString())));
 return '<div class="v67-timeline">'+list.map(h=>{
  const duration=minutesBetween(h.createdAt,h.resolvedAt||new Date(s.now).toISOString());
  const isLate=h.status==='open'&&duration>240;
  return '<div class="v67-timeline-row"><div><strong>'+esc(h.id.slice(0,8).toUpperCase())+'</strong>'+
   '<small>'+esc(departments[h.sourceDept]||h.sourceDept)+' → '+esc(departments[h.targetDept]||h.targetDept)+'</small></div>'+
   '<div class="v67-time-track"><b style="width:'+(Math.max(5,duration/max*100)).toFixed(1)+
   '%;background:'+(isLate?colors.red:h.status==='open'?colors.amber:colors.green)+'"></b></div>'+
   '<span>'+esc(timeDuration(duration))+(h.status==='open'?' · Mở':' ✓')+'</span></div>';
 }).join('')+'</div>';
}
function rankings(items,labelFn){
 if(!items.length)return empty('Chưa có dữ liệu xếp hạng');
 const top=items.slice(0,5),max=Math.max(...top.map(x=>x[1]),1);
 return '<div class="v67-rank-list">'+top.map(([id,n],i)=>'<div class="v67-rank-row">'+
 '<b>'+(i+1)+'</b><span>'+esc(labelFn(id))+'</span>'+
 '<div><i style="width:'+(n/max*100).toFixed(1)+'%"></i></div><strong>'+n+'</strong></div>').join('')+'</div>';
}
function feed(s){
 const list=s.events.slice(0,8);
 if(!list.length)return empty('Chưa có sự kiện mới trong phạm vi được chọn');
 const taskMap=new Map((st().monitorData?.tasks||[]).map(t=>[t.id,t]));
 const agentMap=new Map((st().agentsCatalog||[]).map(a=>[a.id,a.title]));
 return '<div class="v67-live-feed">'+list.map(e=>{
  const icon=e.action==='agent.completed'?'◎':e.action.startsWith('handoff.')?'↗':
   e.action.startsWith('document.')?'▤':'✓';
  const note=e.agentId?(agentMap.get(e.agentId)||e.agentId):
   e.sourceDept&&e.targetDept?(departments[e.sourceDept]||e.sourceDept)+' → '+(departments[e.targetDept]||e.targetDept):
   taskMap.get(e.taskId)?.code||'';
  return '<div class="v67-feed-row"><time>'+esc(localHour(e.at))+'</time><span class="v67-feed-icon">'+icon+'</span>'+
   '<div><strong>'+esc(actions[e.action]||e.action)+'</strong>'+
   '<small>'+esc(note)+(e.actor?' · '+esc(e.actor):'')+'</small></div></div>';
 }).join('')+'</div>';
}
function card(title,body,additionalClass=''){
 return '<section class="v67-card '+additionalClass+'"><div class="v67-card-title"><h3>'+title+'</h3></div>'+body+'</section>';
}
function metric(name,value,unit,color='cyan',icon='◉'){
 return '<div class="v67-stat v67-stat-'+color+'"><span class="v67-stat-icon">'+icon+'</span>'+
 '<div><small>'+esc(name)+'</small><strong>'+esc(value)+'</strong>'+
 '<span>'+esc(unit)+'</span></div></div>';
}
function renderAlerts(list){
 if(!list.length)return '<div class="v67-good">✓ Chưa phát hiện cảnh báo từ dữ liệu đã ghi nhận.</div>';
 return '<div class="v67-alerts">'+list.map(a=>
 '<article class="'+(a.level==='critical'?'is-critical':'is-warning')+'">'+
 '<strong>'+esc(a.title)+'</strong><p>'+esc(a.detail)+'</p></article>').join('')+'</div>';
}
function filteredDashboard(f){
 const packet=mon(),s=summarizeMonitor(packet,f);
 if(!s)return '<div class="v67-empty">Chưa có dữ liệu giám sát đã xác thực.</div>';
 const titles={all:'MEP + Xây dựng',mep:'Hệ MEP',xd:'Hệ Xây dựng',cross:'Phối hợp MEP ↔ XD'};
 const hint=f.system==='cross'?'Luồng liên hệ chỉ tính phiếu phối hợp giữa MEP và XD.':'KPI tồn đọng là trạng thái hiện tại; biểu đồ sự kiện theo khoảng thời gian đã chọn.';
 const agentLabels=id=>(st().agentsCatalog||[]).find(x=>x.id===id)?.title||id;
 return '<div class="v67-kpis">'+
 metric('LƯỢT AGENT HOÀN THÀNH',s.agentRuns,'Trong kỳ · '+s.agentsActiveInPeriod+' Agent','cyan','◎')+
 metric('CÔNG VIỆC ĐANG MỞ',s.tasks.filter(x=>x.status!=='done').length,'Tình trạng hiện tại','purple','▤')+
 metric('PHIẾU PHỐI HỢP ĐANG MỞ',s.pending.length,'MEP ↔ XD và nội bộ','green','⇄')+
 metric('PHẢN HỒI TRUNG BÌNH',s.responseMinutes===null?'—':timeDuration(s.responseMinutes),
    s.solved.length+' phiếu đóng trong kỳ','amber','◷')+
 metric('CÔNG VIỆC QUÁ HẠN',s.overdue.length,'Theo hạn đã giao','red','⚠')+
 metric('TỶ LỆ HOÀN THÀNH',s.completionRate===null?'—':s.completionRate.toFixed(1)+'%',
    s.tasks.length+' công việc','blue','✓')+'</div>'+
 '<p class="v67-scope-info">Đang xem: <strong>'+esc(titles[f.system])+'</strong> · '+
 esc(hint)+(packet.eventsTruncated?' <strong>⚠ Nhật ký 7 ngày đã giới hạn '+packet.events.length+' sự kiện mới nhất; cần backend phân trang để tính đủ.</strong>':'')+'</p>'+
 '<div class="v67-layout v67-top-grid">'+
 card('Hoạt động của Agent theo thời gian',activityChart(s,f),'v67-wide')+
 card('Trạng thái công việc · '+s.tasks.length,donutChart(s),'v67-donut-card')+
 card('Lượt Agent theo bộ môn',barChart(s.departments),'v67-dept-card')+'</div>'+
 '<div class="v67-layout v67-middle-grid">'+
 card('Luồng phối hợp MEP ↔ Xây dựng & nội bộ',sankeyChart(s.flows),'v67-flow-card')+
 card('Mạng lưới phòng ban',networkChart(s.flows),'v67-network-card')+
 card('Hoạt động vừa ghi nhận',feed(s),'v67-feed-card')+'</div>'+
 '<div class="v67-layout v67-bottom-grid">'+
 card('Timeline phối hợp · 5 phiếu gần đây',timelineChart(s),'v67-timeline-card')+
 card('Top Agent hoạt động',rankings(s.agents,agentLabels),'v67-top-agents')+
 card('Phòng nhận tồn đọng nhiều',rankings(s.bottleneck,id=>departments[id]||id),'v67-bottleneck')+
 card('Cảnh báo & khuyến nghị',renderAlerts(s.alerts),'v67-warning-card')+'</div>';
}
export function renderMonitorDashboard(){
 const packet=mon();
 if(!st().enabled||!packet)return '<section class="v67-shell">'+
 '<h2>Giám sát Agent V6.7</h2><p>Đang yêu cầu dữ liệu giám sát có chữ ký từ máy chủ…</p></section>';
 const f=filters();
 const projectList=(st().projects||[]).filter(p=>p.id!==undefined);
 const deptOptions=Object.keys(departments).filter(d=>d!=='director');
 const control=(id,label,options,current)=>'<label>'+label+'<select id="'+id+'">'+options.map(([v,t])=>
 '<option value="'+esc(v)+'"'+(current===v?' selected':'')+'>'+esc(t)+'</option>').join('')+'</select></label>';
 return '<div class="v67-shell"><div class="v67-hero">'+
 '<div class="v67-hero-title"><span class="v67-ecg">⌁</span><div><h2>Giám sát Agent — Hoạt động & Phối hợp</h2>'+
 '<p>V6.7 · Trung tâm vận hành của hai hệ MEP và Xây dựng</p></div></div>'+
 '<div class="v67-live-pill"><span class="v67-live-dot"></span>Gần thời gian thực · 15 giây</div></div>'+
 '<div class="v67-toolbar">'+
 control('v67-system','Phạm vi',['all','mep','xd','cross'].map(v=>[v,
  ({all:'Toàn công ty · MEP + XD',mep:'Hệ MEP',xd:'Hệ XD',cross:'Chỉ phối hợp MEP ↔ XD'})[v]]),f.system)+
 control('v67-project','Dự án',[['all','Tất cả dự án được cấp'],...projectList.map(p=>[p.id,p.code+' · '+p.name])],f.project)+
 control('v67-period','Thời gian',[['hour','1 giờ gần nhất'],['today','Hôm nay'],['week','7 ngày']],f.period)+
 control('v67-dept','Bộ môn',[['all','Tất cả bộ môn'],...deptOptions.map(x=>[x,departments[x]])],f.department)+
 '<div class="v67-toolbar-actions"><button class="v67-refresh" id="v67-refresh">↻ Làm mới ngay</button>'+
 '<label class="v67-auto"><input id="v67-auto" type="checkbox" checked> Tự cập nhật</label></div></div>'+
 '<p class="v67-last-sync">Nguồn: nhật ký Google Drive có chữ ký HMAC · Lần kiểm tra gần nhất: '+
 esc(fmtTime(packet.asOf))+' · Không có tiến trình Agent chạy nền/heartbeat.</p>'+
 '<div id="v67-dynamic">'+filteredDashboard(f)+'</div>'+
 '<footer class="v67-footer">Dữ liệu chỉ gồm các dự án được tài khoản Google cho phép xem. '+
 'Mỗi 15 giây hệ thống tải lại snapshot máy chủ; không phải WebSocket. '+
 'Không tự tạo dữ liệu demo hoặc tuyên bố Agent đang chạy khi chỉ có sự kiện hoàn tất.</footer></div>';
}
function sendMonitorRefresh(f){
 if(!window.__xdDriveNonce||!st().enabled)return;
 const id=(globalThis.crypto?.randomUUID?.()||
    Array.from({length:4},()=>Math.floor(Math.random()*0x100000000).toString(16).padStart(8,'0')).join(''))
   .replace(/-/g,'').slice(0,32);
 window.parent.postMessage({
  channel:'XD_MEP_DRIVE_V1',nonce:window.__xdDriveNonce,
  kind:'workspace',section:'monitor',op:'refresh',
  projectId:st().selectedProjectId||'',actionId:id,
  monitorProject:f.project,monitorSystem:f.system,
  monitorPeriod:f.period,monitorDepartment:f.department,
 },'*');
}
export function requestMonitorSnapshot(){sendMonitorRefresh(filters());}
export function stopMonitorPolling(){
 if(typeof window!=='undefined'&&window.__xdMonitorTimer){
  clearInterval(window.__xdMonitorTimer);window.__xdMonitorTimer=null;
 }
}
export function bindMonitorDashboard(root){
 if(!mon())return;
 stopMonitorPolling();
 const fields=[['project','v67-project'],['system','v67-system'],
  ['period','v67-period'],['department','v67-dept']];
 for(const [name,id] of fields)root.querySelector('#'+id)?.addEventListener('change',()=>{
  const next={...filters(),[name]:root.querySelector('#'+id)?.value||'all'};
  activeFilters=next;
  const dynamic=root.querySelector('#v67-dynamic');
  if(dynamic)dynamic.innerHTML=filteredDashboard(next);
 });
 root.querySelector('#v67-refresh')?.addEventListener('click',()=>sendMonitorRefresh(filters()));
 const auto=root.querySelector('#v67-auto');
 window.__xdMonitorTimer=setInterval(()=>{
  if(!auto?.checked||document.visibilityState==='hidden')return;
  if(!document.querySelector('.v67-shell')){stopMonitorPolling();return;}
  sendMonitorRefresh(filters());
 },15000);
}
