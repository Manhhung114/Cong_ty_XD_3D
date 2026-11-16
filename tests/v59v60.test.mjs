import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderCloudPage} from '../src/core/cloud_workspace.js';

const project={id:'project-folder-000001',code:'S234',name:'Sunshine Sky City',client:'A'};
const task={id:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',projectId:project.id,code:'CV-A',
  title:'Kiểm tra <script>alert(1)</script>',dept:'electrical',assignee:'A',status:'review',
  report:'Đã đối chiếu khối lượng và hồ sơ',findings:'',reviewHistory:[]};

function setup(role='admin'){
 globalThis.window={
  __xdCloud:{enabled:true,selectedProjectId:project.id,actor:'actor@example.com',role,
    projects:[project],tasks:[task],documents:[{
      id:'document-file-000001',projectId:project.id,code:'BOQ-001',
      filename:'BOM_R01.xlsx',revision:'R01',category:'boq_mep',actor:'editor@example.com',
    }],events:[]},
  __xdDriveNonce:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
 };
}

test('V5.9 user workspace renders authorized server state, escaping project input',()=>{
 setup('update');
 const html=renderCloudPage('tasks');
 assert.match(html,/Dữ liệu dùng chung/);
 assert.match(html,/data-workspace-op="task_create"/);
 assert.doesNotMatch(html,/data-workspace-op="task_review"/);
 assert.match(html,/&lt;script&gt;/);
 assert.doesNotMatch(html,/<script>alert/);
});

test('V6.0 review actions are admin-only in UI and document registry is visible',()=>{
 setup('admin');
 assert.match(renderCloudPage('reviews'),/data-workspace-op="task_review"/);
 assert.match(renderCloudPage('documents'),/BOQ-001/);
 setup('read');
 assert.doesNotMatch(renderCloudPage('reviews'),/data-workspace-op="task_review"/);
 assert.doesNotMatch(renderCloudPage('tasks'),/data-workspace-op="task_submit"/);
 assert.doesNotMatch(renderCloudPage('projects'),/data-workspace-op="project_create"/);
});

test('V5.9 server replaces local project sheets without removing legacy source',()=>{
 const app=fs.readFileSync(new URL('../src/app.js',import.meta.url),'utf8');
 const backend=fs.readFileSync(new URL('../drive_storage/workspace_ui.py',import.meta.url),'utf8');
 assert.match(app,/renderCloudPage\('projects'\)/);
 assert.match(app,/renderCloudPage\('tasks'\)/);
 assert.match(app,/renderCloudPage\('reviews'\)/);
 assert.match(app,/renderCloudPage\('documents'\)/);
 assert.match(app,/renderCloudPage\('activity'\)/);
 assert.match(app,/new LocalProjectPortal/);
 assert.match(backend,/identity_for\(st\)/);
 assert.match(backend,/server.review_task\(actor/);
 const mirror=fs.readFileSync(new URL('../static/src/core/cloud_workspace.js',import.meta.url),'utf8');
 assert.equal(fs.readFileSync(new URL('../src/core/cloud_workspace.js',import.meta.url),'utf8'),mirror);
});
