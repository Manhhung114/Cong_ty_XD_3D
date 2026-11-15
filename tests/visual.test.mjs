import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {OFFICE_ILLUSTRATION,OFFICE_POINTS,OFFICE_UNMAPPED} from '../src/3d/illustrated.js';
import {DEPARTMENTS,visibleDepartments} from '../src/core/config.js';
import {loadState} from '../src/core/storage.js';

const mem=new Map();
globalThis.localStorage={getItem:key=>mem.get(key)||null,setItem:(key,v)=>mem.set(key,v)};
test('V5.3 only maps visually identifiable departments and offers unmapped selector',()=>{
 assert.equal(Object.keys(OFFICE_POINTS).length,14);
 assert.deepEqual(OFFICE_UNMAPPED,['qa','xd_site']);
 assert.ok(DEPARTMENTS.every(d=>Boolean(OFFICE_POINTS[d.id])!==OFFICE_UNMAPPED.includes(d.id)));
 for(const p of Object.values(OFFICE_POINTS))assert.ok(p[0]>=5&&p[0]<=95&&p[1]>=20&&p[1]<=70);
 assert.equal(visibleDepartments('construction').length,8);
 assert.ok(existsSync(new URL('../'+OFFICE_ILLUSTRATION.replace('./',''),import.meta.url)));
});
test('V5.1 preserves existing tasks when migrating display mode',()=>{
 const state=loadState();assert.equal(state.officeRenderMode,'illustrated');
 state.tasks.push({id:'TASK-999',title:'Giữ hồ sơ cũ',dept:'electrical',status:'todo',assignee:'ELE'});
 state.officeRenderMode='live';localStorage.setItem('mep-ai-company3d.v1',JSON.stringify(state));
 const restored=loadState();assert.equal(restored.officeRenderMode,'live');
 assert.ok(restored.tasks.some(t=>t.id==='TASK-999'));
});
