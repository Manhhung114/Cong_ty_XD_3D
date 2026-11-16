import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {DEPARTMENTS,AGENTS} from '../src/core/config.js';
const load=p=>readFileSync(new URL(p,import.meta.url),'utf8');
test('V5.2 keeps 16 departments and 18 agents without creating a fake executive AI',()=>{
 assert.equal(DEPARTMENTS.length,16);assert.equal(AGENTS.length,18);
 const scene=load('../src/3d/scene.js');
 assert.match(scene,/real three-storey cutaway/);
 assert.match(scene,/setCameraPreset\(/);
 assert.match(scene,/setQuality\(/);
 assert.match(scene,/zoomBy\(/);
});
test('V5.2 page offers actual WebGL camera controls and legacy illustrated mode',()=>{
 const app=load('../src/app.js');
 for(const control of ['isometric','front','top','mep','construction'])assert.ok(app.includes(`data-camera=\\"${control}\\"`)||app.includes(`data-camera="${control}"`),control);
 assert.match(app,/data-office-render=\\"live\\"|data-office-render="live"/);
 assert.match(app,/office-camera-bar/);
});
test('V5.2 has deployment workflow and preserves document/database modules',()=>{
 assert.ok(existsSync(new URL('../.github/workflows/pages.yml',import.meta.url)));
 assert.ok(existsSync(new URL('../src/core/documents.js',import.meta.url)));
 assert.ok(existsSync(new URL('../src/core/storage.js',import.meta.url)));
 const manifest=JSON.parse(load('../VERSION_MANIFEST.json'));
 assert.match(manifest.current_version,/^V(?:5\.[2-9](?:\.[0-9]+)?|6\.0(?: \(Streamlit cloud workflow\))?)$/);
 assert.equal(manifest.backend.postgresql_deployed,false);
 assert.ok(manifest.warnings.includes('No real AI agents connected'));
});
