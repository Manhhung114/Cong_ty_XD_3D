import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {APISettings} from '../src/core/api_settings.js';
import {renderCloudPage} from '../src/core/cloud_workspace.js';

const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
const storage={getItem:()=>null,setItem:()=>{},removeItem:()=>{}};
const proj='project-folder-000001';
const cloud={
 enabled:true,role:'admin',projects:[{id:proj,code:'S234',name:'SUNSHINE SKY CITY'}],
 selectedProjectId:proj,documents:[],events:[],agentRuns:[],
 agentsCatalog:[
  {id:'ELE',title:'Kỹ sư điện AI',department:'electrical'},
  {id:'STR',title:'Kỹ sư kết cấu AI',department:'structure'}
 ],
 tasks:[{id:'a'.repeat(32),projectId:proj,code:'CV-1AB9B47B',
  title:'Đánh giá bản vẽ trên Drive',dept:'electrical',assignee:'',
  assignedAgentId:'ELE',status:'working',priority:'high',
  dueDate:'2026-11-17',reviewHistory:[]}],
 aiStatus:{configured:true,provider:'gemini',model:'gemini-2.5-flash',
  source:'drive_encrypted',shared:true}
};
test('Admin configures centrally and no key entry/local vault exposed in authenticated UI',()=>{
 globalThis.localStorage=storage;
 globalThis.window={__xdCloud:cloud,__xdAuthRole:'admin',__xdDriveConfigured:true,
  __xdAccountEmail:'admin@example.com'};
 const ui=new APISettings({getLanguage:()=> 'vi',onChange:()=>{},notify:()=>{}});
 const html=ui.render();
 assert.match(html,/API & 18 Agent/);
 assert.match(html,/data-drive-kind="ai_config"/);
 assert.match(html,/Google Drive \(mã hóa AES-256-GCM\)/);
 assert.match(html,/data-drive-kind="access"/);
 assert.doesNotMatch(html,/id="apiKey"/);
 assert.doesNotMatch(html,/id="apiEncryptSave"/);
 assert.doesNotMatch(html,/name="passphrase"/);
 assert.doesNotMatch(html,/SHARED_KEY|refresh_token/);
});
test('Task UI clearly separates work started, human unassigned, assigned agent, real run',()=>{
 globalThis.window={__xdCloud:cloud,__xdDriveNonce:'x'.repeat(32)};
 const html=renderCloudPage('tasks');
 assert.match(html,/CV-1AB9B47B/);
 assert.match(html,/Chưa giao/);
 assert.match(html,/Đang thực hiện/);
 assert.match(html,/Chuyên gia được giao/);
 assert.match(html,/Kỹ sư điện AI/);
 assert.match(html,/Agent chưa chạy/);
 assert.match(html,/data-workspace-op="task_assign"/);
 assert.match(html,/data-agent-run-task="/);
 assert.match(html,/data-agent-run-id="ELE"/);
 assert.doesNotMatch(html,/Đã tạo 1 báo cáo/);
});
test('Assigned does not mean finished; signed report creates visible draft only',()=>{
 globalThis.window={__xdCloud:{
  ...cloud,agentRuns:[{
   id:'b'.repeat(32),taskId:'a'.repeat(32),projectId:proj,
   agentId:'ELE',agentTitle:'Kỹ sư điện AI',mode:'preflight',
   at:'2026-11-17T02:00:00Z',actor:'staff@example.com',
   result:'KIỂM TRA CHỈ DỰA TRÊN METADATA',
  }]
 }};
 const html=renderCloudPage('tasks');
 assert.match(html,/Đã tạo 1 báo cáo nháp/);
 assert.match(html,/chờ kỹ sư kiểm chứng/);
 assert.match(html,/Chưa giao/);
});
test('Bridge, secure role and same source/static modules retained',()=>{
 const bridge=read('drive_storage/in_app.py');
 assert.match(bridge,/\["access","ai_config"\]/);
 assert.match(bridge,/can_admin\(identity_for\(st\)\)/);
 const server=read('streamlit_app.py');
 assert.match(server,/ai_settings_dialog\(st\)/);
 assert.ok(server.indexOf('role = require_login(st)')<server.indexOf('st.iframe(page'));
 const work=read('drive_storage/company_ui.py');
 assert.match(work,/effective_config\(st, agent_id\)/);
 const settings=read('src/core/api_settings.js');
 assert.equal(settings,read('static/src/core/api_settings.js'));
 assert.equal(read('src/core/cloud_workspace.js'),read('static/src/core/cloud_workspace.js'));
 for(const path of ['src/core/cloud_workspace.js','src/core/company_suite.js'])
  assert.equal(read(path),read(path.replace('src/','static/src/')));
});
