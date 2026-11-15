import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateMEPCatalog,updateMEPCatalog,MEP_SOURCE_REMOTE} from '../src/core/ql_da_sources.js';
const root=new URL('../',import.meta.url);
const read=p=>readFileSync(new URL(p,root),'utf8');
const catalog=JSON.parse(read('data/legal/MEP_XD_official_catalog.json'));
test('V5.7.6 verifies independent official-source catalog for both branches',()=>{
 const rows=validateMEPCatalog(catalog).vanBan;
 assert.ok(rows.some(x=>x.soHieu==='207/2026/NĐ-CP'));
 assert.ok(rows.some(x=>x.soHieu==='TCVN 2737:2023'));
 assert.ok(rows.some(x=>x.soHieu==='TCVN 5687:2024'));
 assert.ok(rows.some(x=>x.linhVuc.startsWith('Xây dựng'))&&rows.some(x=>x.linhVuc.startsWith('MEPF')));
 assert.match(MEP_SOURCE_REMOTE,/Cong_ty_XD_3D\/main\/data\/legal\/MEP_XD_official_catalog.json/);
});
test('V5.7.5 rejects fake official hostname, drafts and bad schema',()=>{
 const fake=structuredClone(catalog);fake.vanBan[0].duongDan='https://congbao.chinhphu.vn.evil.test/abc';assert.throws(()=>validateMEPCatalog(fake));
 fake.vanBan[0].duongDan=catalog.vanBan[0].duongDan;fake.vanBan[0].ten='Dự thảo kế hoạch';assert.throws(()=>validateMEPCatalog(fake));
 assert.throws(()=>validateMEPCatalog({...catalog,schema:'random'}));
});
test('V5.7.5 bad online refresh never erases stored catalog',async()=>{
 const map=new Map();globalThis.localStorage={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v)};
 await updateMEPCatalog(async()=>({ok:true,json:async()=>catalog}));
 const old=map.get('xd-mep-official-sources-v1');
 await assert.rejects(()=>updateMEPCatalog(async()=>({ok:true,json:async()=>({schema:'fake'})})));
 assert.equal(map.get('xd-mep-official-sources-v1'),old);
});
test('V5.7.5 removes duplicative mobile sidebar backdrop overlay and wires new legal source button',()=>{
 const html=read('index.html'),js=read('src/app.js'),css=read('src/polish.css');
 assert.match(html,/polish.css/);assert.match(html,/id="navScrim"/);
 assert.match(js,/legalSourceUpdate/);assert.match(js,/updateMEPCatalog\(/);
 assert.match(js,/navScrim/);assert.match(css,/\.sidebar\.opened \+ \.mobile-nav-scrim/);
});
