import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {isTVPLUrl,validateTVPLCandidates,checkTVPLUpdates,TVPL_SCHEMA} from '../src/core/tvpl_sources.js';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const seed=JSON.parse(read('data/legal/MEP_XD_tvpl_candidates.json'));

test('V5.7.8 TVPL reference links are strictly validated and separated from official domains',()=>{
 assert.equal(isTVPLUrl('https://m.thuvienphapluat.vn/'),true);
 assert.equal(isTVPLUrl('https://thuvienphapluat.vn/van-ban/x.aspx'),true);
 for(const url of ['http://m.thuvienphapluat.vn/','https://m.thuvienphapluat.vn.evil.net/a','https://evil.net/?to=thuvienphapluat.vn','https://user@thuvienphapluat.vn/'])assert.equal(isTVPLUrl(url),false);
 assert.equal(validateTVPLCandidates(seed).candidates.length,4);
});
test('V5.7.8 TVPL rejects draft, spoofed, duplicate or unrelated documents',()=>{
 const base=seed.candidates[0];
 const checked=validateTVPLCandidates({schema:TVPL_SCHEMA,candidates:[base,base,{...base,duongDan:'https://fake.thuvienphapluat.vn/a'},{...base,ten:'Dự thảo Luật Xây dựng'},{...base,soHieu:'unrelated-id'}]});
 assert.equal(checked.candidates.length,1);
 assert.equal(checked.candidates[0].tinhTrang,'Chờ đối chiếu với nguồn chính thống');
});
test('V5.7.8 TVPL only stores candidate cache when remote validation succeeds',async()=>{
 const state=new Map();const store={getItem:k=>state.get(k),setItem:(k,v)=>state.set(k,v)};
 const result=await checkTVPLUpdates(async()=>({ok:true,json:async()=>seed}),store);
 assert.equal(result.count,4);assert.equal(state.size,1);
 await assert.rejects(checkTVPLUpdates(async()=>({ok:true,json:async()=>({schema:'wrong',candidates:[]})}),store));
 assert.equal(state.size,1);
});
test('V5.7.8 UI exposes distinct TVPL refresh button, workflow and pending table',()=>{
 const app=read('src/app.js');
 assert.match(app,/id="legalTVPLUpdate"/);
 assert.match(app,/TVPL_REFRESH_WORKFLOW/);
 assert.match(app,/checkTVPLUpdates\(\)/);
 assert.match(app,/tvplCandidates\.map/);
 assert.ok(/legalStatistics\(legalRecords\)|renderLegalStatistics/.test(app));
 assert.doesNotMatch(app,/legalStatistics\(tvplCandidates\)/);
});
