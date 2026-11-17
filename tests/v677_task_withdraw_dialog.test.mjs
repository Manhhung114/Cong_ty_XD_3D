import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderCloudPage, bindCloudPage} from '../src/core/cloud_workspace.js';

const read=p=>fs.readFileSync(new URL('../'+p, import.meta.url),'utf8');
const project='project-folder-000001';
const task=(id,status='working',overrides={})=>({
 id,projectId:project,code:'CV-'+id.slice(0,8),
 title:'Kiểm tra bản vẽ điện',dept:'electrical',assignee:'Kỹ sư điện',
 assignedAgentId:'ELE',status,reviewHistory:[],...overrides,
});
const cloud=(role,tasks)=>({
 enabled:true,role,actor:role+'@example.com',selectedProjectId:project,
 projects:[{id:project,code:'S234',name:'SUNSHINE SKY CITY'}],
 tasks,documents:[],events:[],agentRuns:[],
 agentsCatalog:[{id:'ELE',title:'Kỹ sư điện AI',department:'electrical'}],
});

test('Every writable task card shows recall/cancel button; closed tasks disable it',()=>{
 globalThis.window={__xdCloud:cloud('admin',[
  task('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','working'),
  task('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','review'),
  task('cccccccccccccccccccccccccccccccc','done'),
  task('dddddddddddddddddddddddddddddddd','cancelled',{
   assignee:'',assignedAgentId:'',cancelReason:'Thay đổi hợp đồng',
   cancelledBy:'admin@example.com',cancelledAt:'2026-11-17T06:00:00Z',
   reviewHistory:[{at:'2026-11-17T06:00:00Z',actor:'admin@example.com',
                   decision:'cancel',note:'Thay đổi hợp đồng'}],
  }),
 ])};
 const html=renderCloudPage('tasks');
 assert.match(html,/Thu hồi \/ Hủy giao việc/);
 assert.equal((html.match(/data-workspace-op="task_withdraw"/g)||[]).length,2);
 assert.match(html,/Đã hủy/);
 assert.match(html,/Thay đổi hợp đồng/);
 assert.match(html,/Lịch sử xử lý/);
 assert.match(html,/<button[^>]*disabled[^>]*>↩ Thu hồi \/ Hủy giao việc<\/button>/);
 assert.doesNotMatch(html,/data-workspace-op="task_cancel"/);
});

test('Viewer cannot withdraw or cancel, editor can recall but not cancel submitted',()=>{
 globalThis.window={__xdCloud:cloud('read',[task('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')])};
 let html=renderCloudPage('tasks');
 assert.doesNotMatch(html,/data-workspace-op="task_withdraw"/);
 globalThis.window={__xdCloud:cloud('update',[
  task('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','working'),
  task('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','review'),
 ])};
 html=renderCloudPage('tasks');
 assert.equal((html.match(/data-workspace-op="task_withdraw"/g)||[]).length,1);
});

test('Clicking task withdrawal dispatches workspace task_withdraw, never ai_config',()=>{
 const sent=[];
 globalThis.window={
  __xdCloud:cloud('admin',[task('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')]),
  __xdDriveNonce:'x'.repeat(32),
  parent:{postMessage:msg=>sent.push(msg)},
 };
 let clicked;
 const el={
  dataset:{workspaceOp:'task_withdraw',workspaceTask:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'},
  addEventListener:(name,fn)=>{assert.equal(name,'click');clicked=fn;},
 };
 const root={
  querySelector:()=>null,
  querySelectorAll:sel=>sel==='[data-workspace-op]'?[el]:[],
 };
 bindCloudPage(root,'tasks');
 assert.equal(typeof clicked,'function');
 clicked();
 assert.equal(sent.length,1);
 assert.equal(sent[0].kind,'workspace');
 assert.equal(sent[0].section,'tasks');
 assert.equal(sent[0].op,'task_withdraw');
 assert.equal(sent[0].taskId,'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
 assert.equal(sent[0].projectId,project);
 assert.notEqual(sent[0].kind,'ai_config');
 assert.match(sent[0].actionId,/^[0-9a-f]{32}$/);
});

test('Task creation supersedes stale API Settings dialog, native dismissal clears session state',()=>{
 const st=read('streamlit_app.py');
 assert.match(st,/if action\.get\("kind"\) == "workspace":[\s\S]*?st\.session_state\.drive_in_app_action = None[\s\S]*?handle_workspace_action\(st, action\)/);
 assert.match(st,/else:[\s\S]*?st\.session_state\.xd_workspace_dialog = None[\s\S]*?st\.session_state\.drive_in_app_action = action/);
 assert.match(st,/if not st\.session_state\.get\("drive_in_app_action"\) and st\.session_state\.get\('xd_workspace_dialog'\)/);
 const settings=read('drive_storage/ai_settings_ui.py');
 assert.match(settings,/on_dismiss=lambda: st\.session_state\.pop\("drive_in_app_action", None\)/);
 const workspace=read('drive_storage/workspace_ui.py');
 assert.match(workspace,/on_dismiss=lambda: st\.session_state\.pop\("xd_workspace_dialog", None\)/);
 const backend=read('drive_storage/shared_workspace.py');
 assert.match(backend,/"task\.unassigned"/);
 assert.match(backend,/"task\.cancelled"/);
 assert.equal(read('src/core/cloud_workspace.js'),read('static/src/core/cloud_workspace.js'));
});
