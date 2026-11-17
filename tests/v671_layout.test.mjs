import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {updateCommandShell} from '../src/core/command_shell.js';
const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('approved screenshot: full-width company masthead and image in pinned sidebar',()=>{
 const html=read('static/index.html');
 for(const key of [
  'command-header','command-brand','commandTitle','commandLive',
  'commandNotifications','commandHelp','commandAccount','commandAlertCount',
  'sidebar-visual','data-brand-image','<nav id="nav"','page-body',
  'languageSelect','exportBtn','menuBtn',
 ])assert.ok(html.includes(key),key);
 const css=read('src/polish.css');
 assert.match(css,/\.command-header\s*\{position:fixed/);
 assert.match(css,/\.sidebar-visual\s*\{/);
 assert.match(css,/\.v67-mode \.v67-top-grid/);
 assert.match(css,/\.v67-mode \.v67-middle-grid/);
 assert.match(css,/\.v67-mode \.v67-bottom-grid/);
 assert.match(css,/\.v67-mode \.v67-hero\s*\{display:none/);
 assert.match(css,/@media\(max-width:750px\)/);
 // Do not copy screenshot markup's thick red rectangles into the app.
 assert.doesNotMatch(css,/#ff0000|border:6px solid red|border:8px solid red/);
});
test('approved menu order: specialist controls, handoff, monitor, reports, Admin-only settings',()=>{
 const app=read('src/app.js');
 const index=name=>app.indexOf("name:'"+name+"'");
 const sequence=['Văn phòng 3D','Nhân viên AI','Công việc','Chờ phê duyệt',
  'Quản lý dự án','Kho tài liệu','BOQ / Dự toán','BIM / Mô hình',
  'Phối hợp liên phòng','Giám sát Agent','Báo cáo & Thống kê',
  'Pháp luật & tiêu chuẩn','Nhật ký hoạt động','Cài đặt hệ thống'];
 let last=-1;
 for(const label of sequence){const pos=index(label);assert.ok(pos>last,'Menu sequence '+label);last=pos;}
 assert.match(app,/n\.id==='settings'/);
 assert.match(app,/navSvg\(n\.id\)/);
 assert.match(app,/updateCommandShell\(tab,nav\.name\)/);
 assert.match(app,/reports:/);
});
test('app shell uses only allowed account data and real server alerts',()=>{
 const source=read('src/core/command_shell.js');
 assert.match(source,/__xdAuthRole/);
 assert.match(source,/companyMetrics\?\.alerts/);
 assert.match(source,/window\.__xdAccountEmail/);
 assert.match(source,/Đăng xuất bằng nút Đăng xuất của Streamlit/);
 assert.doesNotMatch(source,/refresh_token|client_secret|cookie_secret/);
 assert.match(source,/OFFICE_IMAGE='\.\/assets\/office_xd_mep_isometric_v5_7.webp'/);
 assert.match(source,/safe\(x\.title\)/);
});
test('app modules and CSS production mirror match exactly',()=>{
 for(const file of [
  'app.js','core/command_shell.js','polish.css','core/monitor_dashboard.js'
 ])assert.equal(read('src/'+file),read('static/src/'+file),file);
 const bundler=read('scripts/build_streamlit_runtime_v2.py');
 assert.match(bundler,/'reports'/);
});
