import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderCloudPage} from '../src/core/cloud_workspace.js';

const read=p=>fs.readFileSync(new URL('../'+p, import.meta.url),'utf8');
const pid='project-folder-000001',tid='a'.repeat(32);
function render(role,status,decision,reason='',notice=''){
 globalThis.window={__xdCloud:{
  enabled:true,role,actor:role+'@example.com',
  selectedProjectId:pid,
  projects:[{id:pid,code:'S234',name:'SUNSHINE SKY CITY'}],
  tasks:[{id:tid,projectId:pid,code:'CV-AAAA',title:'Kiểm tra tủ điện',
   dept:'electrical',assignee:'Kỹ sư Điện',assignedAgentId:'ELE',
   status,priority:'high',reviewHistory:[],lastReviewDecision:decision,
   lastReviewNote:reason,lastReviewer:'admin@example.com',
   lastReviewedAt:'2026-11-17T09:00:00Z'}],
  events:[],documents:[],lastActionNotice:notice,
  agentRuns:[{id:'r'.repeat(32),projectId:pid,taskId:tid,
   agentId:'ELE',agentTitle:'Kỹ sư Điện AI',mode:'expert',
   actor:'edit@example.com',at:'2026-11-17T09:00:00Z',
   result:'DXF sample only, not certified'}],
  agentsCatalog:[{id:'ELE',title:'Kỹ sư Điện AI',department:'electrical'}],
 }};
 return renderCloudPage('tasks');
}

test('Admin rejection displays reason/actor and actionable resubmit; retains signed draft',()=>{
 const html=render('update','working','reject','Thiếu dòng định mức');
 assert.match(html,/Yêu cầu sửa/);
 assert.match(html,/Thiếu dòng định mức/);
 assert.match(html,/Admin trả lại — cần sửa và trình lại/);
 assert.match(html,/Gửi lại báo cáo sau sửa/);
 assert.match(html,/DXF sample only, not certified/);
 assert.match(html,/Chuyên gia đọc file/);
 assert.doesNotMatch(html,/Xét duyệt \/ Trả lại/);
});

test('While waiting for Admin, display submitted state; Admin can accept or return',()=>{
 const waiting=render('admin','review','submitted','');
 assert.match(waiting,/Đã trình, đang chờ Admin xét duyệt/);
 assert.match(waiting,/Xét duyệt \/ Trả lại/);
 assert.doesNotMatch(waiting,/Gửi lại báo cáo sau sửa/);
});

test('Approved task shows reviewer and cannot rerun Agent or resubmit',()=>{
 const done=render('update','done','approve','Đã kiểm chứng');
 assert.match(done,/Đã phê duyệt/);
 assert.match(done,/admin@example.com/);
 assert.match(done,/Đã kiểm chứng/);
 assert.doesNotMatch(done,/data-workspace-op="task_submit"/);
 assert.doesNotMatch(done,/data-agent-run-task=/);
});

test('Persistent successful action notice is accessible and HTML escaped',()=>{
 const malicious='<img src=x onerror=alert(1)>';
 const html=render('admin','review','submitted','',malicious);
 assert.match(html,/class="portal-success-note" role="status"/);
 assert.match(html,/&lt;img src=x onerror=alert\(1\)&gt;/);
 assert.doesNotMatch(html,/<img src=x onerror=/);
});

test('The deployed static JS/CSS mirrors match source exactly',()=>{
 assert.equal(read('src/core/cloud_workspace.js'),read('static/src/core/cloud_workspace.js'));
 assert.equal(read('src/portal.css'),read('static/src/portal.css'));
});
