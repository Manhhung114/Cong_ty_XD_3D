import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {agentEvidence,agentEvidenceSummary,selectedAgentTask} from '../src/core/agent_live.js';
import {renderCEOCommandCenter} from '../src/core/hq_dashboard.js';

const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
const pid='project-folder-000001',pidOther='project-folder-000002';
const clock=Date.parse('2026-11-17T09:02:00.000Z');
const activity=(agentId,state,at='2026-11-17T09:01:40.000Z',projectId=pid)=>({
 agentId,projectId,taskId:'b'.repeat(32),taskCode:'CV-BBB',taskTitle:'Kiểm tra tủ điện',
 state,at,hasHeartbeat:false,mode:'expert',failureCode:state==='failed'?'quota':'',
});
const task=(id,parent,stage,status='todo')=>({
 id,projectId:pid,parentTaskId:parent,rootTaskId:'a'.repeat(32),
 hierarchyStage:stage,assignedAgentId:stage==='expert'?'ELE':'PM',
 dept:stage==='expert'?'electrical':'director',status,
 code:'CV-'+id.slice(0,8),title:'Rà soát điện R01',
 assignee:'manager@example.com',
 hierarchyProgress:{total:0,done:0,blockedBy:[]},
});
function cloud(status='completed'){
 const root=task('a'.repeat(32),'','ceo');
 root.hierarchyProgress={total:1,done:0,blockedBy:[]};
 return {
  enabled:true,selectedProjectId:pid,role:'admin',
  projects:[{id:pid,code:'S234',name:'SUNSHINE SKY CITY'}],
  tasks:[root,task('b'.repeat(32),root.id,'pm'),
         task('c'.repeat(32),'b'.repeat(32),'lead'),
         task('d'.repeat(32),'c'.repeat(32),'expert')],
  agentActivity:[activity('ELE',status)],
  hierarchyPlans:[{
   id:'e'.repeat(32),projectId:pid,rootTaskId:root.id,
   status:'dispatched',departments:['electrical'],
   createdAt:'2026-11-17T09:00:00Z',
  }],
 };
}
test('No Agent working state is invented from a working task or a saved report',()=>{
 const x=cloud();
 x.agentActivity=[];
 x.tasks[3].status='working';
 assert.equal(agentEvidence(x,'ELE',pid,clock).state,'idle');
 assert.equal(agentEvidence(x,'ELE',pid,clock).verified,false);
 assert.equal(agentEvidenceSummary(x,pid).started_unconfirmed,0);
 assert.ok(selectedAgentTask(x,'ELE',pid));
});
test('Signed start is labelled unconfirmed, then stale, not indefinitely running',()=>{
 const x=cloud('started_unconfirmed');
 const recent=agentEvidence(x,'ELE',pid,clock);
 assert.equal(recent.state,'started_unconfirmed');
 assert.match(recent.label,/chưa có heartbeat/);
 assert.equal(recent.hasHeartbeat,false);
 const stale=agentEvidence(x,'ELE',pid,clock+3*60000);
 assert.equal(stale.state,'stale');
 assert.match(stale.label,/Chưa xác nhận/);
});
test('Signed failures and completed drafts have distinct status, project-scoped',()=>{
 const x=cloud('failed');
 assert.equal(agentEvidence(x,'ELE',pid,clock).state,'failed');
 assert.match(agentEvidence(x,'ELE',pid,clock).detail,/Hạn mức/);
 x.agentActivity.push(activity('ELE','completed','2026-11-17T09:01:59.000Z',pidOther));
 assert.equal(agentEvidence(x,'ELE',pid,clock).state,'failed');
 assert.equal(agentEvidence(x,'ELE',pidOther,clock).state,'completed');
 assert.equal(agentEvidence(x,'ELE','all',clock).state,'completed');
});
test('CEO command center shows real hierarchy, all agents, data source caveat',()=>{
 const x=cloud('completed');
 const html=renderCEOCommandCenter(x,pid);
 assert.match(html,/CEO COMMAND CENTER/);
 assert.match(html,/S234/);
 assert.match(html,/Giám đốc CEO/);
 assert.match(html,/Quản lý dự án PM/);
 assert.match(html,/Trưởng bộ môn/);
 assert.match(html,/Chuyên gia/);
 assert.match(html,/QA\/QC độc lập/); // headline of workflow
 assert.match(html,/18 Agent/);
 assert.match(html,/chưa có heartbeat/i);
 assert.match(html,/CV-/);
 assert.match(html,/Đã lưu báo cáo nháp/);
 assert.match(html,/không tự sinh kết quả/i);
});
test('CEO control center escapes malicious task, actor and project text',()=>{
 const x=cloud('failed');
 x.projects[0].code='<img src=x onerror=alert(1)>';
 x.tasks[0].title='<script>attack()</script>';
 x.agentActivity[0].taskTitle='<svg onload=alert(1)>';
 const html=renderCEOCommandCenter(x,pid);
 assert.doesNotMatch(html,/<script>attack/);
 assert.doesNotMatch(html,/<img src=x/);
 assert.match(html,/&lt;script&gt;attack/);
 assert.match(html,/&lt;img src=x/);
});
test('Only verified source mirrored; V7 office polls authenticated read-only snapshot',()=>{
 for(const path of ['src/core/agent_live.js','src/core/hq_dashboard.js',
  'src/3d/scene.js','src/3d/illustrated.js','src/app.js',
  'src/core/monitor_dashboard.js','src/portal.css']){
  assert.equal(read(path),read('static/'+path),'mirror '+path);
 }
 const app=read('src/app.js');
 assert.match(app,/section:'overview',op:'refresh'/);
 assert.match(app,/startOfficePolling\(\)/);
 assert.match(app,/stopOfficePolling\(\)/);
 assert.match(app,/getCloud:\(\)=>window\.__xdCloud/);
 const bridge=read('drive_storage/in_app.py');
 assert.match(bridge,/"overview","projects"/);
 const workspace=read('drive_storage/workspace_ui.py');
 assert.match(workspace,/"overview": \{"refresh"\}/);
 const monitor=read('drive_storage/monitoring.py');
 assert.match(monitor,/agentRunningHeartbeat": False/);
 assert.match(monitor,/signedAgentLifecycle": True/);
});
