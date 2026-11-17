import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {summarizeMonitor,renderMonitorDashboard} from '../src/core/monitor_dashboard.js';

const PID='project-folder-012345678';
const now='2026-11-17T02:00:00+00:00';
const event=(id,action,sys,dep,props={})=>({
 id:id.repeat(32),at:'2026-11-17T01:45:00+00:00',projectId:PID,
 action,agentId:'',taskId:'',department:dep,system:sys,
 sourceDept:'',targetDept:'',relation:'',actor:'reader@example.com',...props,
});
const handoff=(id,src,dst,relation,status='open')=>({
 id:id.repeat(32),projectId:PID,title:'Phối hợp <script>danger</script>',
 sourceDept:src,targetDept:dst,relation,status,
 createdAt:'2026-11-17T00:00:00+00:00',
 resolvedAt:status==='resolved'?'2026-11-17T01:10:00+00:00':'',
 taskId:'x'.repeat(32)
});
const packet={
 schema:'XD_MEP_MONITOR_V67',asOf:now,readOnly:true,pollSeconds:15,
 events:[
  event('a','agent.completed','mep','electrical',{agentId:'ELE'}),
  event('b','agent.completed','xd','structure',{agentId:'STR'}),
  event('c','handoff.requested','mep','electrical',{sourceDept:'electrical',targetDept:'structure',relation:'mep_to_xd'}),
  event('d','handoff.requested','xd','structure',{sourceDept:'structure',targetDept:'bim',relation:'xd_to_mep'}),
 ],
 tasks:[
  {id:'x'.repeat(32),projectId:PID,dept:'electrical',system:'mep',
   status:'review',dueDate:'2026-11-16',reviewSince:'2026-11-15T01:00:00Z'},
  {id:'y'.repeat(32),projectId:PID,dept:'structure',system:'xd',
   status:'working',dueDate:'2026-11-18',reviewSince:''},
 ],
 handoffs:[
  handoff('e','electrical','structure','mep_to_xd'),
  handoff('f','structure','bim','xd_to_mep','resolved'),
 ],
 eventsTruncated:false,eventsAvailable:4
};
const f=(system='all',period='today',project='all',department='all')=>({system,period,project,department});
test('V6.7 uses actual signed events and distinguishes MEP, XD, cross-system',()=>{
 const all=summarizeMonitor(packet,f(),new Date(now));
 assert.equal(all.agentRuns,2);
 assert.equal(all.handoffs.length,2);
 assert.equal(all.flows.length,2);
 assert.equal(all.overdue.length,1);
 assert.equal(all.reviewStale.length,1);
 assert.equal(all.agentsActiveInPeriod,2);
 assert.equal(all.completionRate,0);
 assert.equal(all.responseMinutes,70);
 const mep=summarizeMonitor(packet,f('mep'),new Date(now));
 const xd=summarizeMonitor(packet,f('xd'),new Date(now));
 const cross=summarizeMonitor(packet,f('cross'),new Date(now));
 assert.equal(mep.tasks.length,1);
 assert.equal(xd.tasks.length,1);
 assert.equal(mep.agentRuns,1);
 assert.equal(xd.agentRuns,1);
 assert.equal(cross.tasks.length,0);
 assert.equal(cross.agentRuns,0);
 assert.equal(cross.handoffWindow.length,2);
 assert.deepEqual(cross.flows.map(x=>x.source),['electrical','structure']);
});
test('V6.7 project filters cannot fabricate activity',()=>{
 assert.equal(summarizeMonitor(packet,f('all','today','unrecognized'),new Date(now)).events.length,0);
 const empty={...packet,events:[],tasks:[],handoffs:[]};
 const s=summarizeMonitor(empty,f(),new Date(now));
 assert.equal(s.agentRuns,0);
 assert.equal(s.responseMinutes,null);
 assert.equal(s.completionRate,null);
 assert.equal(s.alerts.length,0);
});
test('V6.7 renders approved dashboard groups with no injected HTML or fake counts',()=>{
 globalThis.window={__xdDriveNonce:'a'.repeat(32),__xdCloud:{
  enabled:true,role:'admin',selectedProjectId:PID,
  projects:[{id:PID,code:'S234',name:'SUNSHINE SKY CITY'}],
  agentsCatalog:[{id:'ELE',title:'Điện'},{id:'STR',title:'Kết cấu'}],
  monitorData:packet,
 }};
 const html=renderMonitorDashboard();
 for(const part of [
  'Giám sát Agent','Hệ MEP','Hệ XD','Chỉ phối hợp MEP',
  'v67-system','v67-project','v67-period','v67-dept',
  'Hoạt động của Agent theo thời gian','Trạng thái công việc',
  'Luồng phối hợp MEP','Mạng lưới phòng ban',
  'Timeline phối hợp','Top Agent','Cảnh báo',
  'Gần thời gian thực','15 giây',
 ]){
  assert.ok(html.includes(part),part);
 }
 assert.ok(html.includes('<svg '),'charts are SVG; no external CDN');
 assert.doesNotMatch(html,/<script>danger<\/script>/);
 assert.doesNotMatch(html,/\b256\b|\b412\b/);
});
test('V6.7 frontend and server are wired without weakening Admin settings',()=>{
 const app=fs.readFileSync(new URL('../src/app.js',import.meta.url),'utf8');
 const deploy=fs.readFileSync(new URL('../static/src/app.js',import.meta.url),'utf8');
 assert.equal(app,deploy);
 assert.match(app,/monitor:.*renderMonitorDashboard/);
 assert.match(app,/stopMonitorPolling/);
 assert.match(app,/n.id==='settings'/);
 for(const name of ['core/monitor_dashboard.js','polish.css']){
  assert.equal(
   fs.readFileSync(new URL('../src/'+name,import.meta.url),'utf8'),
   fs.readFileSync(new URL('../static/src/'+name,import.meta.url),'utf8')
  );
 }
 const bridge=fs.readFileSync(new URL('../drive_storage/in_app.py',import.meta.url),'utf8');
 assert.match(bridge,/monitorProject/);
 assert.match(bridge,/"monitor"/);
 const backend=fs.readFileSync(new URL('../drive_storage/monitoring.py',import.meta.url),'utf8');
 assert.match(backend,/MEP_DEPARTMENTS/);
 assert.match(backend,/XD_DEPARTMENTS/);
 assert.match(backend,/WINDOW_DAYS = 7/);
});
