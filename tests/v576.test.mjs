import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateMEPCatalog,validateDiscovery,checkMEPDiscoveries,MEP_SOURCE_CANDIDATES} from '../src/core/ql_da_sources.js';
const base=new URL('../',import.meta.url),read=p=>readFileSync(new URL(p,base),'utf8');
test('V5.7.6 source registry has official sites and independent MEP source URL',()=>{
 const r=JSON.parse(read('data/legal/MEP_XD_source_registry.json'));
 assert.equal(r.schema,'mepxd-official-source-registry-v1');
 assert.ok(r.sites.some(s=>s.host==='vbpl.vn'));
 assert.ok(r.sites.some(s=>s.host==='tieuchuan.vsqi.gov.vn'));
 assert.match(MEP_SOURCE_CANDIDATES,/Cong_ty_XD_3D/);
});
test('V5.7.6 pending discoveries are not approved effective laws',async()=>{
 const original=JSON.parse(read('data/legal/MEP_XD_official_catalog.json'));
 const old=validateMEPCatalog(original).vanBan[0];
 const r=await checkMEPDiscoveries(async()=>({ok:true,json:async()=>({
 schema:'mepxd-official-discovery-v1',candidates:[{soHieu:old.soHieu,ten:'Unverified',duongDan:old.duongDan,tinhTrang:'Còn hiệu lực'}]
 })}));
 assert.equal(r.count,1);assert.match(r.rows[0].tinhTrang,/Chờ đối chiếu/);
 assert.equal(validateMEPCatalog(original).vanBan[0].ten,old.ten);
});
test('V5.7.6 updater cannot auto-modify reviewed legal catalog',()=>{
 const workflow=read('.github/workflows/refresh-mep-legal.yml');
 assert.match(workflow,/git add data\/legal\/MEP_XD_source_candidates\.json/);
 assert.doesNotMatch(workflow,/git add data\/legal\/MEP_XD_official_catalog\.json/);
});
