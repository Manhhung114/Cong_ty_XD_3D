import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {legalKind,legalStatistics,uniqueLegalRecords} from '../src/core/legal_statistics.js';
import {isOfficialUrl} from '../src/core/standards.js';
import {validateMEPCatalog} from '../src/core/ql_da_sources.js';
const root=new URL('../',import.meta.url);
const read=p=>readFileSync(new URL(p,root),'utf8');
const json=p=>JSON.parse(read(p));

test('V5.7.7 summary classification is based on number rather than ambiguous type',()=>{
 assert.equal(legalKind({soHieu:'TCVN 2737:2023',loai:'Tiêu chuẩn'}),'tcvn');
 assert.equal(legalKind({soHieu:'QCVN 06:2022/BXD',loai:'Quy chuẩn'}),'qcvn');
 assert.equal(legalKind({soHieu:'55/2024/QH15',loai:'Luật'}),'law');
 assert.equal(legalKind({soHieu:'207/2026/NĐ-CP',loai:'Nghị định sửa đổi'}),'decree');
 assert.equal(legalKind({soHieu:'91/2026/VBHN-NĐ-BXD',loai:'Văn bản hợp nhất'}),'consolidated');
});
test('V5.7.7 source catalog statistics deduplicate per sector + document number',()=>{
 const rows=[...json('data/legal/MEP_XD_official_catalog.json').vanBan,...json('data/legal/danh_muc_van_ban_chinh_thong.json').vanBan,...json('data/legal/TCVN_QLDA_VPS_verified.json').vanBan];
 const stat=legalStatistics(rows),unique=uniqueLegalRecords(rows);
 assert.equal(stat.total,unique.length);
 assert.equal(stat.total,42);
 assert.equal(stat.totals.law,2);
 assert.equal(stat.standards,stat.totals.tcvn+stat.totals.qcvn);
 assert.equal(stat.sectors.construction+stat.sectors.mepf,stat.total);
 assert.equal(Object.values(stat.totals).reduce((a,b)=>a+b,0),stat.total);
});
test('V5.7.7 document numbers are separately counted when shared across disciplines',()=>{
 const a={linhVuc:'Xây dựng – Quản lý dự án',soHieu:'TCVN 2737:2023'};
 const b={...a,linhVuc:'MEPF – Phòng cháy chữa cháy'};
 const s=legalStatistics([a,a,b]);assert.equal(s.total,2);assert.equal(s.totals.tcvn,2);
});
test('V5.7.7 sources are official and never interpreted as legal document counts',()=>{
 const registry=json('data/legal/MEP_XD_source_registry.json');
 assert.ok(registry.sites.length>=9);
 assert.ok(registry.sites.every(s=>isOfficialUrl(s.url)));
 assert.ok(registry.sites.some(s=>s.host==='bocongan.gov.vn'));
 assert.ok(registry.sites.some(s=>s.host==='vbpl.moj.gov.vn'));
 assert.ok(registry.sites.some(s=>s.host==='mst.gov.vn'));
 assert.equal(legalStatistics(registry.sites).total,0);
});
test('V5.7.7 UI displays STT and makes summary independent of unreviewed discoveries',()=>{
 const app=read('src/app.js');
 assert.match(app,/legalStatistics\((?:legalRecords|validLegalRecords)\)/);
 assert.match(app,/legal-stat-cards/);
 assert.match(app,/legal-stats-table/);
 assert.match(app,/class="mono legal-stt">\$\{i\+1\}/);
 assert.match(app,/legalSourceSites\.map/);
 assert.match(app,/legalCandidates\.length\?/);
 assert.match(app,/items\.map\(\(d,i\)=>/);
});
