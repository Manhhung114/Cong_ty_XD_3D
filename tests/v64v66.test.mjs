import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderCompanySuite} from '../src/core/company_suite.js';

const catalog=JSON.parse(fs.readFileSync(new URL('../data/agents_v61.json',import.meta.url),'utf8')).agents;
const pid='project-folder-012345678',tid='b'.repeat(32);
function setup(role='admin'){
 globalThis.window={__xdDriveNonce:'a'.repeat(32),__xdCloud:{
  enabled:true,role,actor:'admin@example.com',
  selectedProjectId:pid,
  projects:[{id:pid,code:'S234',name:'SUNSHINE SKY CITY'}],
  tasks:[{id:tid,projectId:pid,code:'CV01',title:'BOQ MEP <script>bad</script>',
          dept:'qs',assignee:'QS',status:'todo',dueDate:'2026-12-01'}],
  documents:[],handoffs:[],events:[],fileInventory:null,companyMetrics:{
    projects:1,tasks:1,doing:0,overdue:0,unassigned:0,review:0,
    highPriority:0,documentPending:0,handoffsOpen:0,departments:[],alerts:[],
  },agentsCatalog:catalog.map(a=>({...a,expert_tools:['boq_arithmetic','source_completeness']})),
  agentRuns:[{id:'c'.repeat(32),agentId:'QSU',taskId:tid,projectId:pid,
      actor:'editor@example.com',at:'2026-11-16T10:00:00Z',mode:'expert',result:'BOQ: mẫu có nguồn',
      workflowStages:[{expert:'QSU',status:'analyzed',detail:'Đã đọc bảng tính'}],
      expertEvidence:{provenance:{filename:'BOQ_R01.csv',sha256:'e'.repeat(64)}}}],
  aiStatus:{configured:false,provider:'none',model:''},
 }};
}
test('V6.4-6.6 Agent UI reports evidence-backed file analyses but escapes user text',()=>{
 setup();
 const page=renderCompanySuite('agents');
 assert.match(page,/đọc mẫu PDF\/XLSX\/CSV\/DXF\/IFC/);
 assert.match(page,/Công cụ chuyên gia/);
 assert.match(page,/BOQ_R01.csv/);
 assert.match(page,/SHA256/);
 assert.match(page,/Chuyên gia tệp thật/);
 assert.doesNotMatch(page,/<script>bad<\/script>/);
});
test('V6.6 keeps server permission boundaries in the UI',()=>{
 setup('read');
 const page=renderCompanySuite('agents');
 assert.doesNotMatch(page,/data-agent-execute="QSU"/);
});
test('V6.6 Python routes real file extraction and signed review only on server',()=>{
 const backend=fs.readFileSync(new URL('../drive_storage/company_ui.py',import.meta.url),'utf8');
 const rules=fs.readFileSync(new URL('../drive_storage/expert_rules.py',import.meta.url),'utf8');
 const orchestrator=fs.readFileSync(new URL('../drive_storage/expert_orchestrator.py',import.meta.url),'utf8');
 assert.match(backend,/run_expert\(/);
 assert.match(backend,/file_docs/);
 assert.match(orchestrator,/agent.completed/);
 assert.match(orchestrator,/sha256/);
 assert.match(rules,/standardCheck/);
 for(const p of ['core/company_suite.js']){
  const source=fs.readFileSync(new URL('../src/'+p,import.meta.url),'utf8');
  const mirror=fs.readFileSync(new URL('../static/src/'+p,import.meta.url),'utf8');
  assert.equal(source,mirror);
 }
});
