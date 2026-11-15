import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
import {DEPARTMENTS} from '../src/core/config.js';
import {OFFICE_POINTS,OFFICE_UNMAPPED,OFFICE_EXTRA_WORKSTATIONS} from '../src/3d/illustrated.js';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('V5.7 all sixteen departments have unique clickable positions',()=>{
 assert.equal(DEPARTMENTS.length,16);
 assert.equal(Object.keys(OFFICE_POINTS).length,16);
 assert.deepEqual(OFFICE_UNMAPPED,[]);
 const unique=new Set(Object.values(OFFICE_POINTS).map(p=>p.join(',')));
 assert.equal(unique.size,16);
 for(const d of DEPARTMENTS)assert.ok(OFFICE_POINTS[d.id],d.id);
 for(const id of ['qa','xd_site','xd_safety','xd_material'])assert.ok(OFFICE_POINTS[id]);
 assert.equal(Object.keys(OFFICE_EXTRA_WORKSTATIONS).length,3);
 assert.ok(existsSync(new URL('../assets/office_xd_mep_isometric_v5_7.webp',import.meta.url)));
});
test('V5.7 UI has distinct online projects, approval and account pages',()=>{
 const app=read('src/app.js'),portal=read('src/portal.js'),html=read('index.html');
 for(const id of ['projects','reviews','portalAdmin'])assert.ok(app.includes(`id:'${id}'`));
 for(const x of ['/api/projects','/api/auth/login','/tasks','/review','/documents','/members','/api/admin/agents'])assert.ok(portal.includes(x),x);
 assert.match(portal,/HTTPS required/);
 assert.match(portal,/sessionStorage/);
 assert.match(html,/portal.css/);
 assert.doesNotMatch(portal,/sk-[A-Za-z0-9]{20}/);
});
test('V5.7 build remains update-compatible with same applicationId and signing secret names',()=>{
 const gradle=read('android/app/build.gradle'),action=read('.github/workflows/build-android-apk.yml');
 assert.match(gradle,/applicationId 'vn\.congtyxd3d\.app'/);
 assert.match(gradle,/versionCode 59/);
 assert.match(action,/secrets.XD_MEP_KEYSTORE_BASE64/);
 assert.match(action,/python -m pytest backend\/tests/);
});
