import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const read = p => fs.readFileSync(new URL('../' + p, import.meta.url), 'utf8');

function clickHarness(role = 'admin', nonce = 'N'.repeat(32)) {
  const source = read('static/src/app.js');
  const match = source.match(/function attachDriveToolbarEvents\(\)\{[\s\S]*?\n\}\nfunction bindGlobal/);
  assert.ok(match, 'Find the actual event-dispatch function from the deployed bundle');
  const code = match[0].replace(/\nfunction bindGlobal$/, '');
  const handlers = [], messages = [];
  const window = {
    __xdDriveNonce: nonce,
    __xdAuthRole: role,
    __xdCloud: {enabled: true, selectedProjectId: 'folder-1',
      projects: [{id: 'folder-1', code: 'S234'}]},
    parent: {postMessage: (payload, target) => messages.push({payload, target})},
  };
  const document = {addEventListener: (name, handler) => {
    assert.equal(name, 'click'); handlers.push(handler);
  }};
  const ctx = {document, window, portal: {currentProject: {code: 'S234'}}};
  vm.runInNewContext(code, ctx);
  ctx.attachDriveToolbarEvents();
  function click(kind, section) {
    let prevented = false;
    const button = {getAttribute: name => name === 'data-drive-kind' ? kind : section};
    const event = {target: {closest: selector => {
      assert.equal(selector, '[data-drive-kind]'); return button;
    }}, preventDefault: () => {prevented = true;}};
    if (handlers.length) handlers[0](event);
    return prevented;
  }
  return {click, handlers, messages, window};
}

test('Admin Settings API button actually posts ai_config to native Streamlit dialog bridge', () => {
  assert.equal(read('src/app.js'), read('static/src/app.js'), 'deployed static mirror must match source');
  const h = clickHarness();
  assert.equal(h.handlers.length, 1);
  assert.equal(h.click('ai_config', 'settings'), true, 'button must be handled');
  assert.equal(h.messages.length, 1);
  assert.equal(h.messages[0].payload.kind, 'ai_config');
  assert.equal(h.messages[0].payload.section, 'settings');
  assert.equal(h.messages[0].payload.projectCode, 'S234');
  assert.equal(h.messages[0].payload.nonce, 'N'.repeat(32));
  assert.equal(h.messages[0].payload.channel, 'XD_MEP_DRIVE_V1');
  assert.equal(h.messages[0].target, '*');

  assert.equal(h.click('access', 'settings'), true, 'existing access dialog still opens');
  assert.equal(h.messages[1].payload.kind, 'access');
  assert.equal(h.click('browse', 'documents'), true, 'Drive actions still work');
  assert.equal(h.messages[2].payload.kind, 'browse');
});

test('Settings bridge rejects non-admin and unexpected action, and nonce is required', () => {
  const staff = clickHarness('update');
  assert.equal(staff.click('ai_config', 'settings'), false);
  assert.equal(staff.click('access', 'settings'), false);
  assert.equal(staff.messages.length, 0);
  const admin = clickHarness();
  assert.equal(admin.click('unknown', 'settings'), false);
  assert.equal(admin.click('ai_config', 'documents'), false);
  assert.equal(admin.messages.length, 0);
  const offline = clickHarness('admin', '');
  assert.equal(offline.handlers.length, 0, 'offline app must not request native dialogs');
});
