import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import {createProjectInStore,addTaskInStore,submitTaskInStore,reviewTaskInStore} from '../src/local_portal.js';
import {encryptAPIKey,decryptAPIKey,safeConfig} from '../src/core/api_settings.js';
import {nextRevision} from '../src/core/documents.js';
import {AGENTS} from '../src/core/config.js';
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const store=()=>({projects:[],tasks:[],events:[],selectedProjectId:null});
const file=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');

test('V5.7.3 creates independent project spaces without login',()=>{
 const s=store();const a=createProjectInStore(s,{code:'DA-001',name:'Chung cư A'});
 const b=createProjectInStore(s,{code:'DA-002',name:'Nhà xưởng B'});
 assert.notEqual(a.id,b.id);assert.equal(s.projects.length,2);
 assert.throws(()=>createProjectInStore(s,{code:'da-001',name:'Duplicate'}),/tồn tại/);
 const ta=addTaskInStore(s,{projectId:a.id,dept:'electrical',title:'Kiểm tra tải điện'});
 const tb=addTaskInStore(s,{projectId:b.id,dept:'structure',title:'Kiểm tra cột thép'});
 assert.notEqual(ta.projectId,tb.projectId);
 assert.equal(s.tasks.filter(t=>t.projectId===a.id).length,1);
});
test('V5.7.3 local approval requires report and records reviewer',()=>{
 const s=store(),p=createProjectInStore(s,{code:'DA-Q',name:'Dự án Q'});
 const t=addTaskInStore(s,{projectId:p.id,dept:'qa',title:'Kiểm tra chất lượng'});
 assert.throws(()=>submitTaskInStore(s,t.id,{summary:'short'}),/12 ký tự/);
 submitTaskInStore(s,t.id,{summary:'Đã rà soát toàn bộ hồ sơ kiểm tra chất lượng.'});
 assert.throws(()=>reviewTaskInStore(s,t.id,{decision:'reject',reviewer:'B',comment:'Không'}),/người kiểm tra/);
 reviewTaskInStore(s,t.id,{decision:'reject',reviewer:'Kỹ sư A',comment:'Cần bổ sung tài liệu'});
 assert.equal(t.status,'working');assert.equal(t.reviewHistory.at(-1).decision,'reject');
 submitTaskInStore(s,t.id,{summary:'Đã bổ sung hồ sơ và đối chiếu bản vẽ gốc.'});
 reviewTaskInStore(s,t.id,{decision:'approve',reviewer:'Kỹ sư B'});
 assert.equal(t.status,'done');assert.equal(t.reviewHistory.length,4);
});
test('Revisions are independent for project and discipline',()=>{
 const docs=[{project:'DA-001',code:'DRW-001',revision:1,division:'mep'},
  {project:'DA-002',code:'DRW-001',revision:1,division:'mep'},
  {project:'DA-001',code:'DRW-001',revision:2,division:'construction'}];
 assert.equal(nextRevision(docs,'DRW-001','mep','DA-001'),2);
 assert.equal(nextRevision(docs,'DRW-001','mep','DA-002'),2);
 assert.equal(nextRevision(docs,'DRW-001','construction','DA-001'),3);
});
test('API config is allowlisted and never persists raw key',()=>{
 const cfg=safeConfig({provider:'bad',model:'hello',agentOverrides:{ELE:{provider:'openai',model:'model-test'},WRONG:{provider:'gemini',model:'x'}}});
 assert.equal(cfg.provider,'none');assert.equal(cfg.agentOverrides.ELE.provider,'openai');assert.equal(cfg.agentOverrides.WRONG,undefined);
 assert.equal(AGENTS.length,18);
 const app=file('src/app.js'),html=file('index.html'),settings=file('src/core/api_settings.js');
 assert.match(app,/new LocalProjectPortal/);assert.match(app,/id:'settings'/);
 assert.doesNotMatch(app,/id:'portalAdmin'/);assert.doesNotMatch(html,/Đăng nhập để quản lý công việc/);
 assert.match(settings,/AES-256-GCM/);assert.match(settings,/this\.keys=\{\}/);
 assert.match(settings,/checkProviderKey/);
});
test('API key encrypted vault needs correct passphrase and stores only ciphertext',async()=>{
 const key='sk-testing-string-that-is-not-an-api-key';
 const record=await encryptAPIKey(key,'long-safe-passphrase!');
 const serialized=JSON.stringify(record);
 assert.ok(!serialized.includes(key));assert.equal(await decryptAPIKey(record,'long-safe-passphrase!'),key);
 await assert.rejects(()=>decryptAPIKey(record,'wrong-password-xxx'),/Sai mật khẩu/);
});
test('Android retains package ID and increases update version',()=>{
 const gradle=file('android/app/build.gradle');
 assert.match(gradle,/applicationId 'vn\.congtyxd3d\.app'/);assert.ok(Number(gradle.match(/versionCode (\d+)/)?.[1])>=60,'Android versionCode must not decrease');
 assert.match(gradle,/versionName '5\.7\.4'/);
});
