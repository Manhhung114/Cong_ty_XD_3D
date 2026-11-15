import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {AGENTS,visibleAgents,visibleDepartments} from '../src/core/config.js';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('Only one Office 3D sidebar tab; divisions remain selectable inside view',()=>{
 const src=read('src/app.js');
 assert.doesNotMatch(src, /id:'construction',icon:/);
 assert.match(src, /id:'overview',icon:/);
 assert.match(src, /divisionToggle\(mode\)/);
 assert.match(src, /data-office-view/);
 assert.match(src, /if\(next==='construction'\)\{next='overview'/);
});
test('Shared leadership appears in both filtered lists and inspector, not counted twice',()=>{
 const shared=['CEO','PM'];
 const mep=visibleAgents('mep'),xd=visibleAgents('construction'),all=visibleAgents('all');
 for(const a of shared){assert.equal(mep.filter(x=>x.id===a).length,1);assert.equal(xd.filter(x=>x.id===a).length,1);}
 assert.equal(mep.length,10);assert.equal(xd.length,10);assert.equal(all.length,18);
 assert.equal(visibleDepartments('mep').length,8);assert.equal(visibleDepartments('construction').length,9);
 assert.equal(AGENTS.filter(a=>a.dept==='director').length,2);
 const app=read('src/app.js');
 assert.match(app,/const people=visibleAgents\(state.officeView\)/);
 assert.match(app,/const memberCount=visibleAgents\(mode\).length/);
 assert.match(app,/Ban điều hành chung/);
});
test('UI keeps Vietnamese and English description for shared executives',()=>{
 const dictionary=read('src/core/i18n.js');
 assert.match(dictionary,/Shared Management/);
 assert.match(dictionary,/Project Management Lead/);
});
