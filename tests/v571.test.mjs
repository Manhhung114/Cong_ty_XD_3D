import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {loadState,removeGeneratedTasks} from '../src/core/storage.js';
import {INITIAL_TASKS,CONSTRUCTION_SAMPLE_TASKS} from '../src/core/config.js';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const memory=new Map();globalThis.localStorage={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v)};
test('V5.7.1 starts with no seeded work or fake approval counts',()=>{
 memory.clear();const state=loadState();assert.deepEqual(state.tasks,[]);assert.deepEqual(state.events,[]);
 assert.equal(state.sampleTasksRemoved,true);
});
test('V5.7.1 removes only generated tasks; retains human evidence and custom entries',()=>{
 const data={tasks:[...structuredClone(INITIAL_TASKS),...structuredClone(CONSTRUCTION_SAMPLE_TASKS),
  {id:'TASK-501',title:'Báo cáo kiểm tra thực tế',dept:'electrical',status:'working'},
  {...INITIAL_TASKS[0],reviewSubmission:{summary:'Kết quả đo điện thực tế và đối chiếu.'}}],
  events:[{kind:'demo',text:'Chạy mô phỏng'},{kind:'activity',text:'Hồ sơ người dùng được lưu'}]};
 removeGeneratedTasks(data);assert.equal(data.tasks.length,2);
 assert(data.tasks.some(t=>t.id==='TASK-501'));
 assert(data.tasks.some(t=>t.reviewSubmission?.summary));
 assert.equal(data.events.length,1);
 const saved=JSON.stringify(data);removeGeneratedTasks(data);assert.equal(JSON.stringify(data),saved);
});
test('V5.7.1 has a single server-backed approval page and no simulator',()=>{
 const app=read('src/app.js'),html=read('index.html'),portal=read('src/portal.js');
 assert.equal((app.match(/id:'reviews'/g)||[]).length,1);
 assert.doesNotMatch(app,/id:'portalApprovals'|function toggleSimulation/);
 assert.doesNotMatch(html,/demoBtn|DỰ ÁN MÔ PHỎNG 001|DEMO/);
 assert.ok(app.includes("reviews:()=>window.__xdCloud?.enabled?renderCloudPage('reviews'):portal.render('reviews')"));
 assert.match(portal,/return kind==='reviews'\?this\.approvalsPage\(\)/);
 assert.match(portal,/this\.canReviewTask\(t\)/);
 assert.doesNotMatch(app,/BOQ_DEMO\.csv/);
});
test('V6.0 uses a server-backed workspace on Streamlit while preserving offline fallback',()=>{
 const app=read('src/app.js'),portal=read('src/portal.js'),local=read('src/local_portal.js');
 assert.match(app,/new LocalProjectPortal/);assert.doesNotMatch(app,/new ProjectPortal\(/);
 for(const tab of ['reviews','tasks','documents'])assert.ok(app.includes(`renderCloudPage('${tab}')`)&&app.includes(`portal.render('${tab}')`),tab);
 assert.match(portal,/if\(!this\.user\)return this\.loginPage\(\)/);assert.doesNotMatch(local,/loginPage\(/);
 assert.match(portal,/canReviewTask/);assert.match(local,/reviewTaskInStore/);
 assert.ok(portal.includes("kind==='documents'?this.documentsPage()"));
});
test('V5.7.1 Android keeps package ID, updates version and omits sample assets',()=>{
 const gradle=read('android/app/build.gradle');const workflow=read('.github/workflows/build-android-apk.yml');
 assert.match(gradle,/applicationId 'vn\.congtyxd3d\.app'/);
 assert.ok(Number(gradle.match(/versionCode (\d+)/)?.[1])>=60,'Android versionCode must not decrease');
 assert.match(workflow,/rm -rf android\/app\/src\/main\/assets\/www\/data\/samples/);
});
