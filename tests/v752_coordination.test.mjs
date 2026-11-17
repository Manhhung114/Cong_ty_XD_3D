import test from 'node:test';
import assert from 'node:assert/strict';
import {renderCloudPage,bindCloudPage} from '../src/core/cloud_workspace.js';
import {renderCompanySuite,bindCompanySuite} from '../src/core/company_suite.js';

const project='project-folder-000001';
const task='f'.repeat(32);
const meeting='a'.repeat(32);
function setup(role='admin',active=true,status='pending_approval'){
 globalThis.window={__xdDriveNonce:'n'.repeat(32),__xdCloud:{
   enabled:true,role,actor:'admin@example.com',selectedProjectId:project,
   meetingsAvailable:active,
   projects:[{id:project,code:'DA01',name:'Công trình 1'}],
   tasks:[{id:task,projectId:project,code:'CV-TASK',title:'Điện HVAC PCCC',
           dept:'electrical',status:'working',assignee:'ele@example.com',
           assignedAgentId:'ELE',hierarchyStage:'',reviewHistory:[],
           hierarchyProgress:{total:0,done:0,blockedBy:[]}}],
   meetings:[{id:meeting,projectId:project,title:'Họp phối hợp MEP',
     agenda:'Máng cáp và ống gió <img src=x onerror=alert(1)>',
     scheduledAt:'2026-11-18T09:00:00+07:00',
     departments:['electrical','hvac'],
     status,minutes:'Đã thảo luận',decisions:'Điều chỉnh tuyến cáp',
     actions:[{title:'Sửa tuyến cáp',dept:'electrical',assignee:'ele@example.com'}],
     actionTaskIds:[],totalActions:0,completedActions:0,readyToClose:false}],
   handoffs:[],events:[],agentsCatalog:[],agentRuns:[],documents:[],
   companyMetrics:{projects:1,tasks:1,doing:1,review:0,overdue:0,unassigned:0,
                   highPriority:0,documentPending:0,handoffsOpen:0,departments:[],alerts:[]},
 }};
}
test('company dashboard shows linked meetings, honest state and Admin review',()=>{
 setup();
 const html=renderCompanySuite('company');
 assert.match(html,/Tạo cuộc họp phối hợp/);
 assert.match(html,/Duyệt kết luận cuộc họp/);
 assert.match(html,/Máng cáp và ống gió/);
 assert.doesNotMatch(html,/<img src=x onerror=/);
 assert.match(html,/&lt;img src=x onerror=alert\(1\)&gt;/);
 assert.match(html,/data-meeting-op="meeting_approve"/);
});
test('editor can record minutes but not approve; disabled flag hides mutations',()=>{
 setup('update',true,'scheduled');
 let html=renderCompanySuite('company');
 assert.match(html,/data-meeting-op="meeting_minutes"/);
 assert.doesNotMatch(html,/data-meeting-op="meeting_approve"/);
 setup('read',true,'scheduled');
 html=renderCompanySuite('company');
 assert.doesNotMatch(html,/data-meeting-op=/);
 assert.doesNotMatch(html,/data-company-action="meeting_create"/);
 setup('admin',false,'scheduled');
 html=renderCompanySuite('company');
 assert.doesNotMatch(html,/data-meeting-op=/);
 assert.doesNotMatch(html,/data-company-action="meeting_create"/);
});
test('task card offers same scoped meeting and workflow hints',()=>{
 setup();
 let html=renderCloudPage('tasks');
 assert.match(html,/Giao việc/);
 assert.match(html,/Họp phối hợp khi vướng/);
 assert.match(html,/Mở họp liên bộ môn/);
 assert.match(html,/data-workspace-op="meeting_create"/);
 setup('read');
 html=renderCloudPage('tasks');
 assert.doesNotMatch(html,/data-workspace-op="meeting_create"/);
});
test('meeting approval sends only a scoped authenticated workspace command',()=>{
 setup();
 const messages=[];
 window.parent={postMessage:m=>messages.push(m)};
 const button={dataset:{meetingOp:'meeting_approve',meetingId:meeting},
   addEventListener:(type,callback)=>{assert.equal(type,'click');button.click=callback}};
 const root={querySelectorAll:selector=>selector==='[data-meeting-op]'?[button]:[]};
 bindCompanySuite(root,'company');
 button.click();
 assert.equal(messages.length,1);
 assert.equal(messages[0].section,'company');
 assert.equal(messages[0].op,'meeting_approve');
 assert.equal(messages[0].meetingId,meeting);
 assert.equal(messages[0].projectId,project);
 assert.equal(messages[0].nonce,'n'.repeat(32));
 assert.equal(messages[0].kind,'workspace');
});

test('mobile-friendly task focus filters only change local view and not signed data',()=>{
 setup('admin',true,'scheduled');
 window.__xdCloud.meetings[0].taskIds=[task];
 const makeControl=mode=>({
   dataset:{taskFocus:mode},attrs:{},addEventListener:(name,handler)=>{assert.equal(name,'click');controlHandlers[mode]=handler},
   setAttribute(key,val){this.attrs[key]=val}
 });
 const controlHandlers={};
 const tabs=['all','mine','cross'].map(makeControl);
 const card={dataset:{taskId:task},hidden:false};
 const empty={hidden:true};
 const root={
   querySelector:selector=>selector==='[data-task-focus-empty]'?empty:null,
   querySelectorAll:selector=>selector==='[data-task-focus]'?tabs:
     selector==='.portal-task[data-task-id]'?[card]:[],
 };
 bindCloudPage(root,'tasks');
 controlHandlers.mine();
 assert.equal(card.hidden,true);
 assert.equal(empty.hidden,false);
 controlHandlers.cross();
 assert.equal(card.hidden,false);
 assert.equal(empty.hidden,true);
 assert.equal(tabs[2].attrs['aria-pressed'],'true');
 assert.equal(window.__xdCloud.tasks.length,1);
});
