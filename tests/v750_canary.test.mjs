import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

test('V7.5 keeps legacy rooms and adds one separate room per authenticated specialist', async () => {
  const legacy = await import('../src/core/config.js?legacy');
  assert.equal(legacy.AGENTS.length,18);
  const catalog = JSON.parse(await readFile(new URL('../data/agents_v75.json',import.meta.url))).agents;
  globalThis.__xdCloud = {enabled:true,agentsCatalog:catalog};
  try {
    const ui = await import('../src/core/config.js?canary');
    assert.equal(ui.AGENTS.length,20);
    assert.equal(ui.DEPARTMENTS.length,16);
    assert.equal(ui.OFFICE_ROOMS.length,18);
    assert.equal(legacy.OFFICE_ROOMS.length,16);
    assert.deepEqual(ui.roomAgents('director').map(a=>a.id),['CEO','PM']);
    assert.deepEqual(ui.roomAgents('xd_safety').map(a=>a.id),['HSE']);
    assert.deepEqual(ui.roomAgents('legal').map(a=>a.id),['LEG']);
    assert.deepEqual(ui.roomAgents('xd_qc').map(a=>a.id),['QCX']);
    assert.ok(ui.visibleDepartments('mep').some(room=>room.id==='legal'));
    assert.ok(ui.visibleDepartments('construction').some(room=>room.id==='legal'));
    assert.ok(!ui.visibleDepartments('mep').some(room=>room.id==='xd_qc'));
    assert.equal(ui.visibleAgents('mep').some(a=>a.id==='QCX'),false);
    assert.equal(ui.visibleAgents('construction').some(a=>a.id==='QCX'),true);
  } finally {
    delete globalThis.__xdCloud;
  }
});
