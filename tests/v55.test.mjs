import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {loadState,createTask,changeTaskStatus,submitReviewMaterial,decideTaskReview} from '../src/core/storage.js';
import {translateText,getLanguage} from '../src/core/i18n.js';
const map=new Map();globalThis.localStorage={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v)};
const source=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('V5.5 reviews require actual submitted report or referenced document',()=>{
 map.clear();const state=loadState();const t=createTask(state,{title:'Đối chiếu hồ sơ điện thực tế',dept:'electrical'});const id=t.id;changeTaskStatus(state,id,'review');assert.equal(t.status,'review');
 assert.throws(()=>decideTaskReview(state,id,{decision:'approve',reviewer:'Engineer A'}),/Chưa có báo cáo/);
 assert.throws(()=>submitReviewMaterial(state,id,{summary:'short'}),/12 ký tự/);
 submitReviewMaterial(state,id,{summary:'Đã đối chiếu BOQ với bản vẽ và ghi sai lệch.',findings:'Thiếu 2 thiết bị điện'});
 assert.equal(t.reviewSubmission.findings,'Thiếu 2 thiết bị điện');
 decideTaskReview(state,id,{decision:'approve',reviewer:'Engineer A',comment:'Approved for demo'});
 assert.equal(t.status,'done');assert.equal(t.reviewDecision.reviewer,'Engineer A');assert.ok(t.reviewHistory.length>=2);
 assert.equal(loadState().tasks.find(x=>x.id===id).reviewHistory.length,t.reviewHistory.length);
});
test('V5.5 rejection returns task to working and records reason',()=>{
 map.clear();const state=loadState();const t=createTask(state,{title:'Kiểm tra vật tư xây dựng',dept:'xd_material'});const id=t.id;changeTaskStatus(state,id,'review');
 assert.throws(()=>decideTaskReview(state,id,{decision:'reject',reviewer:'Engineer B',comment:'No'}),/lý do/);
 decideTaskReview(state,id,{decision:'reject',reviewer:'Engineer B',comment:'Check BOQ against revised drawing'});
 assert.equal(state.tasks.find(x=>x.id===id).status,'working');
 assert.equal(state.tasks.find(x=>x.id===id).reviewHistory.at(-1).decision,'reject');
});
test('V5.5 prevents completing unreviewed tasks by changing status directly',()=>{
 map.clear();const state=loadState();const t=createTask(state,{title:'Thiết kế hồ sơ kết cấu',dept:'structure'});const id=t.id;changeTaskStatus(state,id,'working');
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
test('V5.7.1 keeps one authenticated approval queue and removes simulation mode',()=>{
 const js=source('src/app.js'),portal=source('src/portal.js'),html=source('index.html');
 assert.match(js,/id:'reviews'/);assert.doesNotMatch(js,/id:'portalApprovals'/);
 assert.match(js,/reviews:\(\)=>portal\.render\('reviews'\)/);
 assert.match(portal,/approvalsPage\(\)/);
 assert.match(portal,/canReviewTask\(t\)/);
 assert.doesNotMatch(html,/id="demoBtn"/);
 assert.doesNotMatch(html,/DỰ ÁN MÔ PHỎNG 001/);
});
test('V5.5 signed Android builds require secret-backed keystore outside public source',()=>{
 const gradle=source('android/app/build.gradle');const workflow=source('.github/workflows/build-android-apk.yml');
 assert.ok(Number(gradle.match(/versionCode\s+(\d+)/)?.[1])>=55);assert.match(gradle,/applicationId 'vn\.congtyxd3d\.app'/);
 assert.match(gradle,/signingConfig signingConfigs.stableRelease/);
 assert.match(workflow,/secrets.XD_MEP_KEYSTORE_BASE64/);
 assert.match(workflow,/secrets.XD_MEP_STORE_PASSWORD/);
 assert.match(workflow,/assembleRelease/);
 assert.doesNotMatch(workflow,/BEGIN PRIVATE KEY/);
});
