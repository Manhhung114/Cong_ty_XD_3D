import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root=new URL('../',import.meta.url);
const read=p=>fs.readFileSync(new URL(p,root),'utf8');

test('V6.7.2 uses exact approved screenshot crops and matching static mirrors',()=>{
 const js=read('src/core/command_shell.js');
 for(const file of [
  'user_reference_header_v672.webp',
  'user_reference_sidebar_v672.webp',
  'user_reference_foyer_v672.webp',
 ]){
  assert.ok(js.includes(file),file);
  const data=fs.readFileSync(new URL('static/assets/'+file,root));
  assert.equal(data.subarray(8,12).toString('ascii'),'WEBP');
  assert.ok(data.byteLength<25000,'keep lightweight inline asset '+file);
 }
 assert.equal(js,read('static/src/core/command_shell.js'));
 assert.equal(read('src/polish.css'),read('static/src/polish.css'));
});
test('V6.7.2 no artificial width cap, responsive full-height app with artwork layers',()=>{
 const css=read('src/polish.css');
 for(const item of ['width:100%!important;max-width:100%!important',
  'var(--xd-approved-header)','var(--xd-approved-sidebar)',
  'var(--xd-approved-foyer)', 'max-width:none!important','width:100%!important',
  'min-height:100dvh!important','@media(max-width:750px)']){
  assert.ok(css.includes(item),item);
 }
 const py=read('streamlit_app.py');
 assert.match(py,/st\.container\(key="xd_fullwidth_workspace"\)/);
 assert.match(py,/height:calc\(100dvh - 44px\)!important/);
 assert.match(py,/padding:0!important;margin:0!important/);
});
test('V6.7.2 keeps role-based settings and source-backed monitoring intact',()=>{
 const app=read('src/app.js');
 const shell=read('src/core/command_shell.js');
 assert.match(app,/n\.id==='settings'/);
 assert.match(app,/renderMonitorDashboard/);
 assert.match(shell,/__xdAuthRole/);
 assert.match(shell,/companyMetrics\?\.alerts/);
 assert.match(shell,/root\.style\.setProperty\('--xd-approved-foyer'/);
});
