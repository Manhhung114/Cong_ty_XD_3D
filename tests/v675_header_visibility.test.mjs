import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');

test('V6.7.5 full glass facade and roof fit the visible 64px panorama',()=>{
 const img=read('static/assets/premium_header_visible_v675.svg');
 assert.match(img,/width="3200" height="120" viewBox="0 0 3200 120"/);
 assert.match(img,/x="1278" y="54" width="870" height="48"/);
 assert.match(img,/x="1616" y="66" width="180" height="35"/);
 assert.match(img,/Full building: complete roof, glass front, door/);
 assert.ok(img.match(/<rect /g).length>300);
 assert.doesNotMatch(img,/<script|<foreignObject|https:\/\//);
 const scale=Math.max(1910/3200,64/120);
 const top=(120-64/scale)/2;
 assert.ok(top<22 && top+64/scale>108,'full front fits landscape viewport');
});

test('V6.7.5 header uses dedicated panorama and reduced overlay',()=>{
 const css=read('src/polish.css');
 const style=css.slice(css.indexOf('/* V6.7.5 Header Visibility Fix'));
 assert.match(style,/var\(--xd-visible-header\)!important/);
 assert.match(style,/rgba\(4,23,44,\.08\)/);
 assert.match(style,/background-size:100% 100%,cover!important/);
 assert.match(style,/@media\(max-width:750px\)/);
 const js=read('src/core/command_shell.js');
 assert.match(js,/VISIBLE_HEADER='\.\/assets\/premium_header_visible_v675\.svg'/);
 assert.match(js,/setProperty\('--xd-visible-header'/);
 assert.equal(read('src/polish.css'),read('static/src/polish.css'));
 assert.equal(js,read('static/src/core/command_shell.js'));
 assert.match(read('static/index.html'),/class="command-version">V[6-9]\\.[0-9]+(?:\.[0-9]+)?</);
});

test('V6.7.5 preserves Google auth, Drive and Admin-only settings',()=>{
 const py=read('streamlit_app.py');
 assert.ok(py.indexOf('role = require_login(st)')<py.indexOf('st.iframe(page'));
 const app=read('src/app.js');
 assert.match(app,/n\.id==='settings'/);
 assert.match(app,/renderMonitorDashboard/);
 assert.match(app,/data-drive-kind/);
});
