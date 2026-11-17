import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderCloudPage,bindCloudPage} from '../src/core/cloud_workspace.js';

const read=p=>fs.readFileSync(new URL('../'+p, import.meta.url),'utf8');
const pid='project-folder-000001',ids={
 ceo:'a'.repeat(32),pm:'b'.repeat(32),lead:'c'.repeat(32),
 expert:'d'.repeat(32),qa:'e'.repeat(32)};
const t=(id,parent,stage,agent,dept,assignee,status='todo')=>({
 id,projectId:pid,parentTaskId:parent,rootTaskId:ids.ceo,
 hierarchyStage:stage,assignedAgentId:agent,dept,assignee,
 status,title:stage+' kiểm tra tủ điện',code:'CV-'+id.slice(0,8).toUpperCase(),
 reviewHistory:[],hierarchyProgress:{total:0,done:0,blockedBy:[]},
});
function setup(role='admin',actor='admin@example.com',status='pending'){
 const tasks=[
  t(ids.ceo,'','ceo','CEO','director','director@example.com'),
  t(ids.pm,ids.ceo,'pm','PM','director','pm@example.com'),
  t(ids.lead,ids.pm,'lead','ELE','electrical','lead@example.com'),
  t(ids.expert,ids.lead,'expert','ELE','electrical','engineer@example.com'),
  t(ids.qa,ids.lead,'qa','QAC','qa','qa@example.com'),
 ];
 tasks[0].hierarchyProgress={total:1,done:0,blockedBy:[]};
 tasks[1].hierarchyProgress={total:1,done:0,blockedBy:[]};
 tasks[2].hierarchyProgress={total:2,done:0,blockedBy:[]};
 tasks[4].hierarchyProgress={total:0,done:0,blockedBy:[ids.expert]};
 globalThis.window={__xdCloud:{
  enabled:true,role,actor,selectedProjectId:pid,
  projects:[{id:pid,code:'S234',name:'SUNSHINE SKY CITY'}],
  tasks,documents:[],events:[],agentRuns:[],
  hierarchyPlans:status==='none'?[]:[{
   id:'f'.repeat(32),projectId:pid,rootTaskId:ids.ceo,
   status,departments:['electrical'],createdBy:'director@example.com'}],
  orgRoles:[],agentsCatalog:[
   {id:'CEO',title:'Giám đốc điều hành AI'},
   {id:'PM',title:'Điều phối dự án AI'},
   {id:'ELE',title:'Kỹ sư điện AI'},
   {id:'QAC',title:'QA/QC AI'},
  ]}};
 return tasks;
}
test('Admin sees signed CEO hierarchy, role editor and approval queue',()=>{
 const tasks=setup();
 const html=renderCloudPage('tasks');
 assert.match(html,/Cơ cấu tổ chức/);
 assert.match(html,/Duyệt phương án CEO/);
 assert.match(html,/Tuyến phân cấp/);
 assert.match(html,/Tiến độ cấp dưới/);
 assert.match(html,/Trưởng bộ môn/);
 assert.match(html,/Chuyên gia/);
 assert.match(html,/QA\/QC/);
 assert.match(html,/data-parent-task="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"/);
 assert.match(html,/Chưa được xử lý/);
 assert.ok(html.indexOf('portal-hierarchy-ceo')<html.indexOf('portal-hierarchy-pm'));
 assert.ok(html.indexOf('portal-hierarchy-pm')<html.indexOf('portal-hierarchy-lead'));
 assert.ok(html.indexOf('portal-hierarchy-lead')<html.indexOf('portal-hierarchy-expert'));
 assert.ok(html.indexOf('portal-hierarchy-expert')<html.indexOf('portal-hierarchy-qa'));
 assert.doesNotMatch(html,/data-agent-run-task="eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"/);
});
test('CEO request button only on un-dispatched root; after planning review replaces it',()=>{
 setup('admin','admin@example.com','none');
 let html=renderCloudPage('tasks');
 assert.match(html,/Giám đốc AI lập phương án/);
 assert.match(html,/data-workspace-op="hierarchy_propose"/);
 setup('admin','admin@example.com','pending');
 html=renderCloudPage('tasks');
 assert.doesNotMatch(html,/data-workspace-op="hierarchy_propose"/);
 assert.match(html,/data-workspace-op="hierarchy_review"/);
});
test('Role-based sign-off: assigned PM can review a lead, but QA remains Admin-only',()=>{
 setup('update','pm@example.com');
 let html=renderCloudPage('reviews');
 assert.doesNotMatch(html,/data-workspace-op="task_review"/);
 const tasks=window.__xdCloud.tasks;
 tasks[2].status='review';
 html=renderCloudPage('reviews');
 assert.match(html,/data-workspace-op="task_review"/);
 tasks[4].status='review';
 html=renderCloudPage('reviews');
 assert.equal((html.match(/data-workspace-op="task_review"/g)||[]).length,1);
 setup('update','qa@example.com');
 window.__xdCloud.tasks[4].status='review';
 html=renderCloudPage('reviews');
 assert.doesNotMatch(html,/data-workspace-op="task_review"/);
});
test('Only Admin can stop an active signed hierarchy tree',()=>{
 setup('admin','admin@example.com','dispatched');
 let html=renderCloudPage('tasks');
 assert.match(html,/Dừng toàn bộ cây phân phối/);
 assert.match(html,/data-workspace-op="hierarchy_stop"/);
 setup('update','director@example.com','dispatched');
 html=renderCloudPage('tasks');
 assert.doesNotMatch(html,/data-workspace-op="hierarchy_stop"/);
});

test('Editor assigned to PM cannot run other engineer or QA work',()=>{
 setup('update','pm@example.com','dispatched');
 const html=renderCloudPage('tasks');
 assert.match(html,/data-agent-run-task="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"/);
 assert.doesNotMatch(html,/data-agent-run-task="dddddddddddddddddddddddddddddddd"/);
 assert.doesNotMatch(html,/data-agent-run-task="eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"/);
 assert.doesNotMatch(html,/data-workspace-op="org_roles"/);
});
test('CEO plan click sends correct project/task and never API config',()=>{
 setup('admin','admin@example.com','none');
 const token='x'.repeat(32),messages=[];
 globalThis.window.__xdDriveNonce=token;
 globalThis.window.parent={postMessage:m=>messages.push(m)};
 let handler=null;
 const element={
  dataset:{workspaceOp:'hierarchy_propose',workspaceTask:ids.ceo},
  addEventListener:(event,fn)=>{assert.equal(event,'click');handler=fn;},
 };
 const root={
  querySelector:()=>null,
  querySelectorAll:s=>s==='[data-workspace-op]'?[element]:[],
 };
 bindCloudPage(root,'tasks');
 assert.equal(typeof handler,'function');
 handler();
 assert.equal(messages.length,1);
 assert.equal(messages[0].kind,'workspace');
 assert.equal(messages[0].op,'hierarchy_propose');
 assert.equal(messages[0].taskId,ids.ceo);
 assert.equal(messages[0].projectId,pid);
 assert.notEqual(messages[0].kind,'ai_config');
});
test('Deployed static modules and CSS match source bytes',()=>{
 assert.equal(read('src/core/cloud_workspace.js'),read('static/src/core/cloud_workspace.js'));
 assert.equal(read('src/portal.css'),read('static/src/portal.css'));
 const server=read('drive_storage/workspace_ui.py');
 assert.match(server,/hierarchy_propose/);
 assert.match(server,/hierarchy_review/);
 const backend=read('drive_storage/shared_workspace.py');
 for(const action of ['org.role_set','hierarchy.proposed','hierarchy.approved','hierarchy.rejected'])
  assert.ok(backend.includes('"'+action+'"'));
});
