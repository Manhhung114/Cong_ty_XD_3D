import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');

test('V6.7.4 skyline and logo are vector, not upscaled 350px screenshot',()=>{
 const skyline=read('static/assets/premium_skyline_v674.svg');
 const emblem=read('static/assets/premium_emblem_v674.svg');
 assert.match(skyline,/width="3200" height="420"/);
 assert.match(skyline,/preserveAspectRatio/);
 assert.match(skyline,/<linearGradient/);
 assert.match(emblem,/viewBox="0 0 512 512"/);
 assert.ok(skyline.match(/<rect/g).length>300);
 assert.doesNotMatch(skyline,/https:\/\/|<foreignObject|<script/);
 assert.doesNotMatch(emblem,/<script/);
});
test('V6.7.4 premium assets are bundled only after Google login',()=>{
 const shell=read('src/core/command_shell.js');
 assert.match(shell,/PREMIUM_SKYLINE='\.\/assets\/premium_skyline_v674\.svg'/);
 assert.match(shell,/PREMIUM_EMBLEM='\.\/assets\/premium_emblem_v674\.svg'/);
 assert.match(shell,/root\.style\.setProperty\('--xd-premium-skyline'/);
 assert.match(shell,/root\.style\.setProperty\('--xd-premium-emblem'/);
 assert.match(shell,/image\.closest\('\.sidebar-visual'\)\?SIDEBAR_ART:PREMIUM_EMBLEM/);
 assert.equal(shell,read('static/src/core/command_shell.js'));
 const backend=read('streamlit_app.py');
 assert.ok(backend.indexOf('role = require_login(st)')<backend.indexOf('st.iframe(page'));
});
test('V6.7.4 premium header prioritizes readability without stretching artwork',()=>{
 const css=read('src/polish.css');
 const premium=css.slice(css.indexOf('/* V6.7.4 Premium Header'));
 assert.match(premium,/background-size:100% 100%,cover!important/);
 assert.match(premium,/var\(--xd-premium-skyline\)/);
 assert.match(premium,/\.command-brand-logo img[\s\S]*?object-fit:contain!important/);
 assert.match(premium,/\.command-heading strong[\s\S]*?text-shadow:/);
 assert.match(premium,/\.command-online\.is-connected i/);
 assert.match(premium,/@media\(max-width:750px\)/);
 assert.equal(css,read('static/src/polish.css'));
 assert.match(read('static/index.html'),/class="command-version">V6\.7\.6</);
});
