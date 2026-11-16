import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const load=(p)=>readFileSync(new URL('../'+p,import.meta.url),'utf8');

test('V5.7.9 removes visible release notes and version markers, keeps navigation',()=>{
 const html=load('index.html'),app=load('src/app.js');
 assert.doesNotMatch(html,/class="app-footer"/);
 assert.doesNotMatch(html,/V5\.7\.8/);
 assert.doesNotMatch(app,/<small>\$\{n\.version\}<\/small>/);
 assert.doesNotMatch(app,/id:'roadmap'.*name:'Các phiên bản'/);
 assert.match(app,/id:'legal'/);
 assert.match(app,/id:'reviews'/);
});
test('V5.7.9 mobile dock navigates key pages without duplicating task actions',()=>{
 const html=load('index.html'),app=load('src/app.js');
 for(const p of ['overview','projects','tasks','reviews','menu']) assert.match(html,new RegExp(`data-dock="${p}"`));
 assert.match(app,/switchTab\(b\.dataset\.dock\)/);
 assert.doesNotMatch(app,/<small>\$\{n.version\}<\/small>/);
});
test('V5.7.9 keeps backup, source indicators, legal statuses and API security functions',()=>{
 const html=load('index.html'),app=load('src/app.js');
 assert.match(html,/id="exportBtnSidebar"/);
 assert.match(app,/exportData/);
 assert.match(app,/legalTVPLUpdate/);
 const settings=load('src/core/api_settings.js');
 assert.match(settings,/encryptAPIKey/);
 assert.match(settings,/decryptAPIKey/);
});
test('V5.7.9 adds English translations for the new mobile navigation',()=>{
 const i18n=load('src/core/i18n.js');
 for(const item of ["'Văn phòng':'Office'","'Dự án':'Projects'","'Phê duyệt':'Approvals'","'Thêm':'More'"]) assert.ok(i18n.includes(item),item);
});
test('V5.7.9 Android package ID and monotonically increasing version code',()=>{
 const android=load('android/app/build.gradle');
 assert.match(android,/applicationId 'vn\.congtyxd3d\.app'/);
 assert.match(android,/versionCode 64/);
 assert.match(android,/versionName '5\.7\.9'/);
 assert.match(load('package.json'),/"version": "0\.5\.7\.9"/);
});
