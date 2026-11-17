import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderCloudPage} from '../src/core/cloud_workspace.js';

const read=p=>fs.readFileSync(new URL('../'+p, import.meta.url),'utf8');
const pid='project-folder-000001';
const task=(id,status,assignee='',agent='')=>({
 id,projectId:pid,code:'CV-'+id.slice(0,8),title:'Đánh giá bản vẽ',
 dept:'electrical',assignee,assignedAgentId:agent,status,reviewHistory:[],
});
function page(role, tasks){
 globalThis.window={__xdCloud:{
  enabled:true,role,selectedProjectId:pid,projects:[{id:pid,code:'S234',name:'Demo'}],
  tasks,documents:[],agentRuns:[],events:[],agentsCatalog:[],
 }};
 return renderCloudPage('tasks');
}

test('Update-role unassigned working task has actionable return-to-todo, not fake cancel',()=>{
 const html=page('update',[task('a'.repeat(32),'working')]);
 assert.match(html,/data-workspace-op="task_withdraw"/);
 assert.match(html,/Thu hồi \/ Đặt về Chờ xử lý/);
 assert.doesNotMatch(html,/data-workspace-op="task_cancel"/);
});

test('Update-role todo unassigned cannot open an empty modal; explains need Admin',()=>{
 const html=page('update',[task('a'.repeat(32),'todo')]);
 assert.doesNotMatch(html,/data-workspace-op="task_withdraw"/);
 assert.match(html,/Hủy công việc \(cần Admin\)/);
 assert.match(html,/Công việc chưa giao và đang Chờ xử lý: chỉ Admin được hủy/);
});

test('Admin can open cancellation for started unassigned task; read cannot mutate',()=>{
 const t=task('a'.repeat(32),'working');
 const admin=page('admin',[t]);
 assert.match(admin,/data-workspace-op="task_withdraw"/);
 assert.match(admin,/Thu hồi \/ Hủy giao việc/);
 const read=page('read',[t]);
 assert.doesNotMatch(read,/data-workspace-op="task_withdraw"/);
});

test('Source and deployed Streamlit frontends remain byte-identical',()=>{
 assert.equal(read('src/core/cloud_workspace.js'),read('static/src/core/cloud_workspace.js'));
});
