import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('V6.7.3 stretches approved skyline to full-width and keeps in-app scroll',()=>{
 const css=read('src/polish.css');
 assert.match(css,/\/\* V6\.7\.3 — fill the device viewport/);
 assert.match(css,/\.command-header:before\s*\{[\s\S]*?background-size:100% 100%,100% 100%!important/);
 assert.match(css,/#app\s*\{[\s\S]*?min-height:100dvh!important/);
 assert.match(css,/#body:has\(\.overview-grid\)>\.lower-grid/);
 assert.match(css,/min-height:clamp\(275px,34dvh,520px\)/);
 assert.match(css,/@media\(max-width:750px\)/);
 assert.equal(css,read('static/src/polish.css'));
});
test('V6.7.3 does not weaken sign-in or in-sheet Drive actions',()=>{
 const source=read('streamlit_app.py');
 assert.ok(source.indexOf('role = require_login(st)') <
           source.indexOf('st.iframe(page'));
 assert.match(source,/mount_bridge\(st\)/);
 assert.match(source,/load_snapshot\(st\)/);
 assert.match(source,/access_management_dialog\(st\)/);
 assert.match(source,/st\.logout\(\)/);
 const app=read('src/app.js');
 assert.match(app,/n\.id==='settings'/);
 assert.match(app,/renderMonitorDashboard/);
 assert.match(app,/data-drive-kind/);
});
test('V6.7.3 parent Streamlit viewport is bounded; dashboard stays responsive',()=>{
 const source=read('streamlit_app.py');
 assert.match(source,/data-testid="stAppViewContainer"\]:has\(\.st-key-xd_fullwidth_workspace\)/);
 assert.match(source,/overflow-y:hidden!important/);
 assert.match(source,/--xd-auth-height:46px/);
 assert.match(source,/--xd-auth-height:50px/);
 assert.match(source,/height:calc\(100dvh - var\(--xd-auth-height\)\)!important/);
});
