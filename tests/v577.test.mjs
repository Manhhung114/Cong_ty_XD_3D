import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {legalKind,legalStatistics} from '../src/core/legal_statistics.js';
import {isOfficialUrl} from '../src/core/standards.js';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const data=p=>JSON.parse(read(p));
test('V5.7.7 classifies legal entries by number and type',()=>{
 assert.equal(legalKind({soHieu:'TCVN 2737:2023',loai:'Tiêu chuẩn'}),'tcvn');
 assert.equal(legalKind({soHieu:'QCVN 18:2021/BXD',loai:'Quy chuẩn'}),'qcvn');
 assert.equal(legalKind({soHieu:'135/2025/QH15',loai:'Luật'}),'law');
 assert.equal(legalKind({soHieu:'91/2026/VBHN-NĐ-BXD',loai:'Văn bản hợp nhất'}),'consolidated');
});
test('V5.7.7 statistics deduplicate within each division',()=>{
 const docs=[
   ...data('data/legal/MEP_XD_official_catalog.json').vanBan,
   ...data('data/legal/danh_muc_van_ban_chinh_thong.json').vanBan,
   ...data('data/legal/TCVN_QLDA_VPS_verified.json').vanBan
 ];
 const s=legalStatistics(docs);
 assert.equal(s.total,42);
 assert.equal(s.sectors.construction,20);
 assert.equal(s.sectors.mepf,22);
 assert.equal(s.totals.law,2);
 assert.equal(s.totals.decree,10);
 assert.equal(s.totals.tcvn,22);
 assert.equal(s.totals.qcvn,2);
});
test('V5.7.7 registry has nine traceable official portals',()=>{
 const cfg=data('data/legal/MEP_XD_source_registry.json');
 assert.equal(cfg.sites.length,9);
 assert.ok(cfg.sites.every(s=>isOfficialUrl(s.url)));
 assert.ok(cfg.sites.some(s=>s.host==='vbpl.moj.gov.vn'));
 assert.ok(cfg.sites.some(s=>s.host==='bocongan.gov.vn'));
 assert.ok(cfg.sites.some(s=>s.host==='mst.gov.vn'));
});
test('V5.7.7 UI has STT for filtered legal records and summaries',()=>{
 const app=read('src/app.js');
 assert.match(app,/renderLegalSummary\(legalRecords,language\)/);
 assert.match(app,/renderLegalSources\(legalSourceSites,language\)/);
 assert.match(app,/class="mono legal-stt">\$\{i\+1\}/);
 assert.match(app,/items.map\(\(d,i\)=>/);
});
