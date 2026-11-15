import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root=new URL('../', import.meta.url);
const source=p=>readFileSync(new URL(p,root),'utf8');
const html=source('index.html'),app=source('src/app.js'),portal=source('src/local_portal.js');
const methodLine=name=>portal.split('\n').find(line=>line.startsWith(' '+name+'()'));
test('V5.7.4: no global create-work button across sheets',()=>{
 assert.doesNotMatch(html,/newTaskBtn|＋ Công việc/);
 assert.doesNotMatch(app,/newTaskBtn/);
});
test('V5.7.4: project management only creates projects and summarizes',()=>{
 const line=methodLine('projectPage');assert.ok(line);
 assert.match(line,/this\.projectForm\(\)/);
 assert.doesNotMatch(line,/this\.taskForm\(\)|this\.taskRows\(\)/);
});
test('V5.7.4: tasks remains the only screen with creation and processing',()=>{
 const line=methodLine('taskPage');assert.ok(line);
 assert.match(line,/this\.taskForm\(\)/);
 assert.match(line,/this\.taskRows\(\)/);
 assert.match(portal,/addTaskInStore\(this\.store/);
 assert.match(portal,/submitTaskInStore\(this\.store/);
});
test('V5.7.4: approvals still review decisions without task form',()=>{
 const line=methodLine('approvalsPage');assert.ok(line);
 assert.doesNotMatch(line,/this\.taskForm\(\)/);
 assert.match(portal,/reviewTaskInStore\(this\.store/);
});
test('V5.7.4: office and auxiliary sheets have no duplicate assignment button',()=>{
 assert.doesNotMatch(app,/id="addDeptTask"|\$\('addDeptTask'\)/);
 assert.match(app,/function agentsPage\(/);
 assert.match(app,/function boqPage\(/);
 assert.match(app,/function legalPage\(/);
});
