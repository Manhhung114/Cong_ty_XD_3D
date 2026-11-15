import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {getLanguage,translateText,LANGUAGES} from '../src/core/i18n.js';
import {validateStandards,mergeStandards,isOfficialUrl,standardKey,STANDARDS_REMOTE} from '../src/core/standards.js';
const root=new URL('../',import.meta.url);
const read=(file)=>readFileSync(new URL(file,root),'utf8');
const base=JSON.parse(read('data/legal/danh_muc_van_ban_chinh_thong.json')).vanBan;
const extra=JSON.parse(read('data/legal/TCVN_QLDA_VPS_verified.json'));
test('V5.4 provides reviewed official VSQI entries in both MEPF and Construction',()=>{
 const rows=validateStandards(extra);
 assert.equal(rows.length,16);
 assert.ok(rows.every(r=>new URL(r.duongDan).hostname==='tieuchuan.vsqi.gov.vn'));
 assert.ok(rows.some(r=>r.linhVuc.startsWith('MEPF')));
 assert.ok(rows.some(r=>r.linhVuc.startsWith('Xây dựng')));
 assert.ok(rows.every(r=>r.tenAnh));
 assert.ok(rows.some(r=>r.soHieu==='TCVN 9362:2026'));
 assert.ok(rows.some(r=>r.soHieu==='TCVN 9362:2012'&&r.tinhTrang.includes('Hết hiệu lực')));
});
test('V5.4 rejects untrusted domains and draft standards',()=>{
 const x=structuredClone(extra.vanBan[0]);x.duongDan='https://tieuchuan.vsqi.gov.vn.evil.test/path';
 assert.equal(isOfficialUrl(x.duongDan),false);
 assert.throws(()=>validateStandards([x]));
 x.duongDan=extra.vanBan[0].duongDan;x.ten='Dự thảo tiêu chuẩn';
 assert.throws(()=>validateStandards([x]));
});
test('V5.4 merges by discipline and exact TCVN number, retaining legacy law documents',()=>{
 const rows=mergeStandards(base,validateStandards(extra));
 assert.ok(rows.length>=base.length);
 assert.ok(rows.some(r=>r.soHieu==='135/2025/QH15'));
 assert.ok(rows.filter(r=>r.soHieu==='TCVN 2737:2023').length===1);
 assert.equal(rows.find(r=>r.soHieu==='TCVN 9362:2026').tinhTrang,'Còn hiệu lực (VSQI)');
});
test('V5.4 manual imports do not override an official reviewed standard',()=>{
 const standard=validateStandards(extra).find(x=>x.soHieu==='TCVN 2737:2023');
 const local={...standard,ten:'Unverified local entry',tinhTrang:'Chờ đối chiếu nguồn'};
 const merged=mergeStandards([], [standard], [local]);
 assert.equal(merged.length,1);
 assert.equal(merged[0].ten,standard.ten);
});
test('V5.4 English display is non-destructive and defaults to Vietnamese',()=>{
 assert.deepEqual(LANGUAGES,['vi','en']);
 assert.equal(getLanguage(),'vi');
 assert.equal(translateText('Kho tài liệu','en'),'Document Library');
 assert.equal(translateText('Pháp luật & tiêu chuẩn','en'),'Laws & Standards');
 assert.equal(translateText('Kho tài liệu','vi'),'Kho tài liệu');
 assert.equal(translateText('TCVN 9362:2026','en'),'TCVN 9362:2026');
});
test('V5.4 app wires language switch, standard refresh and manual import',()=>{
 const html=read('index.html'), app=read('src/app.js');
 assert.match(html,/id="languageSelect"/);assert.match(app,/function rebuildLegal/);
 assert.match(app,/checkRemoteStandards/);assert.match(app,/saveManualStandards/);
 assert.match(app,/translateDom\(document\.getElementById\('app'\),language\)/);
 assert.match(read('android/app/build.gradle'),/versionCode 54/);
 assert.match(STANDARDS_REMOTE,/Cong_ty_XD_3D\/main/);
});
