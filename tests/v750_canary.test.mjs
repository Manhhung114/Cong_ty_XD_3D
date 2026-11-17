import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

test('V7.5 changes only the authenticated canary catalog and seats three distinct occupants', async () => {
  const legacy = await import('../src/core/config.js?legacy');
  assert.equal(legacy.AGENTS.length,18);
  const catalog = JSON.parse(await readFile(new URL('../data/agents_v75.json',import.meta.url))).agents;
  globalThis.__xdCloud = {enabled:true,agentsCatalog:catalog};
  try {
    const ui = await import('../src/core/config.js?canary');
    assert.equal(ui.AGENTS.length,20);
    assert.equal(ui.DEPARTMENTS.length,16);
    assert.deepEqual(ui.roomAgents('director').map(a=>a.id),['CEO','PM','LEG']);
    assert.deepEqual(ui.roomAgents('xd_safety').map(a=>a.id),['HSE','QCX']);
    const x=ui.roomAgents('director').map((_,i)=>ui.seatOffset(i,3));
    assert.ok(x[1]-x[0]>1.65 && x[2]-x[1]>1.65);
    assert.equal(ui.visibleAgents('mep').some(a=>a.id==='QCX'),false);
    assert.equal(ui.visibleAgents('construction').some(a=>a.id==='QCX'),true);
  } finally {
    delete globalThis.__xdCloud;
  }
});
