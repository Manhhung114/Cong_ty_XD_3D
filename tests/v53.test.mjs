import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {AGENTS,DEPARTMENTS} from '../src/core/config.js';
import {OFFICE_POINTS,OFFICE_UNMAPPED} from '../src/3d/illustrated.js';
const root=new URL('../',import.meta.url);
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('V5.3 hotspot positions never put QA MEP into central meeting room',()=>{
 assert.equal(DEPARTMENTS.length,16);assert.equal(Object.keys(OFFICE_POINTS).length,16);assert.deepEqual(OFFICE_UNMAPPED,[]);
 for(const [id,pos] of Object.entries(OFFICE_POINTS)){
  assert.ok(pos[0]>=0&&pos[0]<=100&&pos[1]>=0&&pos[1]<=100,id);
  if(['electrical','hvac','plumbing','fire','bim','qs'].includes(id))assert.ok(pos[0]<35,id);
 }
});
test('V5.3 all visible staff names are in Vietnamese',()=>{
 assert.equal(AGENTS.length,18);
 for(const a of AGENTS)assert.match(a.name,/[À-ỹ]/u,a.id);
 const html=read('index.html');assert.match(html,/KHÔNG GIAN/);assert.doesNotMatch(html,/WORKSPACE|OPERATIONS CENTER|AI COMPANY/);
});
test('V5.3 legal registry is sourced from government and official standards portal',()=>{
 const l=JSON.parse(read('data/legal/danh_muc_van_ban_chinh_thong.json'));
 assert.equal(l.vanBan.length,29);
 assert.equal(l.vanBan.filter(x=>x.linhVuc.startsWith('MEPF')).length,16);
 assert.equal(l.vanBan.filter(x=>x.linhVuc.startsWith('Xây dựng')).length,13);
 for(const item of l.vanBan){
   const host=new URL(item.duongDan).hostname;
   assert.ok(['vanban.chinhphu.vn','moc.gov.vn','www.moc.gov.vn','tieuchuan.vsqi.gov.vn','dns2.moc.gov.vn'].includes(host),item.soHieu);
   assert.ok(item.ghiChu&&item.ngayRaSoat==='2026-11-15',item.soHieu);
 }
 assert.match(l.vanBan.find(x=>x.soHieu==='TCVN 5738:2021').tinhTrang,/Hết hiệu lực/);
 assert.ok(existsSync(new URL('../data/legal/Thu_vien_phap_luat_MEPF_PCCC_Xay_dung_QLDA_2026.xlsx',import.meta.url)));
});
test('V5.3 library web interface includes navigation, filter, search and download',()=>{
 const app=read('src/app.js');assert.match(app,/id:'legal'/);assert.match(app,/function legalPage\(/);
 for(const id of ['legalField','legalType','legalSearch'])assert.ok(app.includes(id));
 assert.match(app,/Tải bảng Excel/);
});
