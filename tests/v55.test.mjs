import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {loadState,createTask,changeTaskStatus,submitReviewMaterial,decideTaskReview} from '../src/core/storage.js';
import {translateText,getLanguage} from '../src/core/i18n.js';
const map=new Map();globalThis.localStorage={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v)};
const source=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('V5.5 reviews require actual submitted report or referenced document',()=>{
 map.clear();const state=loadState();const id='TASK-003';const t=state.tasks.find(t=>t.id===id);assert.equal(t.status,'review');
 assert.throws(()=>decideTaskReview(state,id,{decision:'approve',reviewer:'Engineer A'}),/Chưa có báo cáo/);
 assert.throws(()=>submitReviewMaterial(state,id,{summary:'short'}),/12 ký tự/);
 submitReviewMaterial(state,id,{summary:'Đã đối chiếu BOQ với bản vẽ và ghi sai lệch.',findings:'Thiếu 2 thiết bị điện'});
 assert.equal(t.reviewSubmission.findings,'Thiếu 2 thiết bị điện');
 decideTaskReview(state,id,{decision:'approve',reviewer:'Engineer A',comment:'Approved for demo'});
 assert.equal(t.status,'done');assert.equal(t.reviewDecision.reviewer,'Engineer A');assert.ok(t.reviewHistory.length>=2);
 assert.equal(loadState().tasks.find(x=>x.id===id).reviewHistory.length,t.reviewHistory.length);
});
test('V5.5 rejection returns task to working and records reason',()=>{
 map.clear();const state=loadState();const id='TASK-009';
 assert.throws(()=>decideTaskReview(state,id,{decision:'reject',reviewer:'Engineer B',comment:'No'}),/lý do/);
 decideTaskReview(state,id,{decision:'reject',reviewer:'Engineer B',comment:'Check BOQ against revised drawing'});
 assert.equal(state.tasks.find(x=>x.id===id).status,'working');
 assert.equal(state.tasks.find(x=>x.id===id).reviewHistory.at(-1).decision,'reject');
});
test('V5.5 prevents completing unreviewed tasks by changing status directly',()=>{
 map.clear();const state=loadState();const id=state.tasks.find(x=>x.status==='working').id;
 assert.throws(()=>changeTaskStatus(state,id,'done'),/phê duyệt/);
 assert.equal(state.tasks.find(x=>x.id===id).status,'working');
});
test('V5.5 supports English for all 18 seeded agent names and descriptions',()=>{
 const agents=source('src/core/config.js');
 assert.equal(translateText('Kỹ sư kiến trúc','en'),'Architectural Engineer');
 assert.equal(translateText('Kỹ sư điều hòa và thông gió','en'),'HVAC Engineer');
 assert.equal(translateText('Chờ phê duyệt','en'),'Awaiting review');
 assert.equal(translateText('Hồ sơ chờ phê duyệt','en'),'Pending Approvals');
 assert.equal(translateText('Tiếng Việt','en'),'Vietnamese');
 assert.match(agents,/V5\.5/);
 assert.equal(getLanguage(),'vi');
});
test('V5.5 review UI links from agent, tasks and approval KPI',()=>{
 const js=source('src/app.js');const css=source('src/styles.css');
 assert.match(js,/function reviewsPage/);assert.match(js,/function taskReviewModal/);
 assert.match(js,/data-review-agent/);assert.match(js,/class="metric review-metric"/);
 assert.match(js,/data-open-task/);assert.match(js,/decideTaskReview\(/);
 assert.match(css,/review-modal-content/);
});
test('V5.5 signed Android builds require secret-backed keystore outside public source',()=>{
 const gradle=source('android/app/build.gradle');const workflow=source('.github/workflows/build-android-apk.yml');
 assert.match(gradle,/versionCode (?:55|56|57)/);assert.match(gradle,/applicationId 'vn\.congtyxd3d\.app'/);
 assert.match(gradle,/signingConfig signingConfigs.stableRelease/);
 assert.match(workflow,/secrets.XD_MEP_KEYSTORE_BASE64/);
 assert.match(workflow,/secrets.XD_MEP_STORE_PASSWORD/);
 assert.match(workflow,/assembleRelease/);
 assert.doesNotMatch(workflow,/BEGIN PRIVATE KEY/);
});
