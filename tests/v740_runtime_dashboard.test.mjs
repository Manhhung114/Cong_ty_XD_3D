import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {agentEvidence,agentEvidenceSummary} from '../src/core/agent_live.js';
import {renderCEOCommandCenter} from '../src/core/hq_dashboard.js';

const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
const pid='project-folder-000001';
const task='a'.repeat(32);
const time='2026-11-17T10:00:00.000Z';
function base(){
 return {enabled:true,selectedProjectId:pid,
  projects:[{id:pid,code:'S234',name:'SUNSHINE SKY CITY'}],
  tasks:[{id:task,projectId:pid,title:'Kiểm tra bản vẽ điện',status:'working',
          assignedAgentId:'ELE',rootTaskId:task,parentTaskId:'',hierarchyStage:'ceo'}],
  agentActivity:[],hierarchyPlans:[],runtimeEnabled:true,runtimeJobs:[]};
}
const job=(state,extra={})=>({
 id:'b'.repeat(32),projectId:pid,taskId:task,agentId:'ELE',mode:'expert',
 state,createdAt:time,heartbeatAt:time,hasHeartbeat:state==='running',
 progress:54,phase:'reading_and_analyzing',actualCostUsd:null,billingVerified:false,...extra});
test('A task marked working is not falsely displayed as live Agent',()=>{
 const data=base();
 assert.equal(agentEvidence(data,'ELE').state,'idle');
 data.runtimeJobs.push(job('queued'));
 assert.equal(agentEvidence(data,'ELE').state,'queued');
 assert.equal(agentEvidence(data,'ELE').hasHeartbeat,false);
 assert.equal(agentEvidenceSummary(data).queued,1);
});
test('A live worker heartbeat is distinct from unconfirmed signed attempt',()=>{
 const data=base();
 data.agentActivity.push({agentId:'ELE',projectId:pid,
  state:'started_unconfirmed',at:'2026-11-17T09:59:20Z'});
 data.runtimeJobs.push(job('running'));
 const evidence=agentEvidence(data,'ELE',pid,Date.parse(time));
 assert.equal(evidence.state,'running');
 assert.equal(evidence.hasHeartbeat,true);
 assert.equal(evidence.workerProgress,54);
 assert.match(evidence.label,/heartbeat/);
 assert.equal(agentEvidenceSummary(data).running,1);
 data.runtimeJobs[0].state='unconfirmed';
 data.runtimeJobs[0].hasHeartbeat=false;
 assert.equal(agentEvidence(data,'ELE',pid,Date.parse(time)).state,'unconfirmed');
 assert.equal(agentEvidence(data,'ELE').hasHeartbeat,false);
});
test('CEO center counts only authenticated running workers',()=>{
 const data=base();
 data.runtimeJobs.push(job('running'));
 const html=renderCEOCommandCenter(data,pid);
 assert.match(html,/CEO COMMAND CENTER/);
 assert.match(html,/worker có heartbeat/);
 assert.match(html,/Agent/);
 assert.match(html,/V7.4/);
 assert.doesNotMatch(html,/<script>/);
});
test('Runtime source and deployed mirrors are identical',()=>{
 for(const p of ['core/agent_live.js','core/hq_dashboard.js','core/monitor_dashboard.js',
                  '3d/scene.js','3d/illustrated.js']){
  assert.equal(read('src/'+p),read('static/src/'+p),p);
 }
 const ui=read('drive_storage/company_ui.py');
 assert.match(ui,/Đưa Agent vào hàng đợi V7\.4/);
 assert.match(ui,/Thu hồi lượt/);
 const server=read('drive_storage/workspace_ui.py');
 assert.match(server,/runtimeJobs/);
 const python=read('agent_runtime/api.py');
 assert.match(python,/\/api\/runtime\/jobs\/cancel/);
});
