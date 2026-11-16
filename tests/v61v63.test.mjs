import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {AGENTS, DEPARTMENTS} from '../src/core/config.js';
import {renderCompanySuite} from '../src/core/company_suite.js';

const manifest=JSON.parse(fs.readFileSync(new URL('../data/agents_v61.json',import.meta.url),'utf8'));
const taskId='a'.repeat(32),projectId='project-folder-000001';
const baseTask={id:taskId,projectId,dept:'electrical',title:'Kiểm tra <script>alert(1)</script>',
  status:'working',code:'CV-001',assignee:'Engineer',dueDate:'2026-11-30',docCode:'DRW-E-01'};
function setup(role='admin',configured=false){
 globalThis.window={__xdDriveNonce:'a'.repeat(32),__xdCloud:{
  enabled:true,selectedProjectId:projectId,role,actor:'admin@example.com',
  projects:[{id:projectId,code:'S234',name:'SUNSHINE SKY CITY'}],
  tasks:[baseTask],documents:[],handoffs:[],agentRuns:[],
  agentsCatalog:manifest.agents,
  aiStatus:{configured,provider:configured?'openai':'none',model:configured?'gpt-4.1-mini':''},
  companyMetrics:{projects:1,tasks:1,doing:1,review:0,completed:0,overdue:0,
   unassigned:0,documents:0,documentPending:0,handoffsOpen:0,
   departments:[{department:'electrical',count:1,doing:1,pending:0,overdue:0,activeAgents:1}],
   alerts:[]}
 }};
}
test('V6.1 catalog matches all 18 existing 3D agents and departments',()=>{
 assert.equal(manifest.agents.length,18);
 assert.deepEqual(new Set(manifest.agents.map(a=>a.id)),new Set(AGENTS.map(a=>a.id)));
 const d=new Set(DEPARTMENTS.map(d=>d.id));
 for(const a of manifest.agents){
  assert.ok(d.has(a.department),'unknown department for '+a.id);
  assert.equal(a.department,AGENTS.find(x=>x.id===a.id).dept);
  assert.ok(a.skills.length>=3);
  assert.ok(a.quality_gate.length>=4);
 }
});
test('V6.1 agent cards are task-scoped and do not represent a configured AI when absent',()=>{
 setup('update',false);
 const page=renderCompanySuite('agents');
 assert.match(page,/18 Agent/);
 assert.match(page,/Kiểm tra checklist/);
 assert.match(page,/Chưa cấu hình AI máy chủ/);
 assert.match(page,/data-agent-execute="ELE"/);
 assert.doesNotMatch(page,/<script>alert/);
 assert.doesNotMatch(page,/data-agent-execute="HVA"/);
});
test('V6.2 read-only role cannot create cross-department handoffs or Admin backups',()=>{
 setup('read');
 const page=renderCompanySuite('company');
 assert.match(page,/Trung tâm điều hành toàn công ty/);
 assert.doesNotMatch(page,/data-company-action="handoff_create"/);
 assert.doesNotMatch(page,/data-company-action="ops_audit"/);
 setup('update');
 const updatePage=renderCompanySuite('company');
 assert.match(updatePage,/data-company-action="handoff_create"/);
 assert.doesNotMatch(updatePage,/data-company-action="ops_audit"/);
 setup('admin',true);
 const adminPage=renderCompanySuite('company');
 assert.match(adminPage,/data-company-action="ops_audit"/);
 assert.match(renderCompanySuite('agents'),/gpt-4.1-mini/);
});
test('V6.3 deployed JS matches source and server routes are present',()=>{
 for(const file of ['app.js','portal.css','core/company_suite.js']){
  const source=fs.readFileSync(new URL('../src/'+file,import.meta.url),'utf8');
  const deployed=fs.readFileSync(new URL('../static/src/'+file,import.meta.url),'utf8');
  assert.equal(source,deployed,'static mirror diverged: '+file);
 }
 const app=fs.readFileSync(new URL('../src/app.js',import.meta.url),'utf8');
 const bridge=fs.readFileSync(new URL('../drive_storage/in_app.py',import.meta.url),'utf8');
 const workspace=fs.readFileSync(new URL('../drive_storage/workspace_ui.py',import.meta.url),'utf8');
 assert.match(app,/renderCompanySuite\('company'\)/);
 assert.match(app,/renderCompanySuite\('agents'\)/);
 assert.match(bridge,/agentId/);
 assert.match(bridge,/handoffId/);
 assert.match(workspace,/ops_audit/);
 assert.match(workspace,/agent_run/);
});
