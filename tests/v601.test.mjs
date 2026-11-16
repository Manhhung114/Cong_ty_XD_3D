import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderCloudPage} from '../src/core/cloud_workspace.js';

function setup(role='admin', withInventory=true){
  globalThis.window={
    __xdDriveNonce:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    __xdCloud:{
      enabled:true,role,actor:'owner@example.com',selectedProjectId:'project-folder-000001',
      projects:[{id:'project-folder-000001',code:'S234',name:'SUNSHINE SKY CITY'}],
      tasks:[],events:[],
      documents:[{id:'file-abc-123456789',projectId:'project-folder-000001',
        code:'BOQ-001',filename:'BOM_R01.xlsx',revision:'R01',status:'pending',actor:'owner@example.com'}],
      fileInventory:withInventory?[{
        id:'file-abc-123456789',projectId:'project-folder-000001',
        code:'BOQ-001',filename:'BOM_R01.xlsx',category:'boq_mep',revision:'R01',
        status:'pending',actor:'owner@example.com',sizeBytes:10000,
        latest:true,registered:true,missing:false,createdTime:'2026-11-16T07:00:00Z',
        modifiedTime:'2026-11-16T07:00:00Z',description:'Đang duyệt',
      },{
        id:'file-def-123456789',projectId:'project-folder-000001',code:'OLD_DOC',
        filename:'OLD_DOC_R02.dwg',category:'drawings_mep',revision:'R02',
        status:'unregistered',actor:'',sizeBytes:20000,
        latest:true,registered:false,missing:false,createdTime:'2026-11-15T07:00:00Z',
        modifiedTime:'2026-11-15T07:00:00Z',description:'',
      }]:null,
      fileCounts:{total:2,registered:1,unregistered:1,pending:1,approved:0,missing:0,modified:0},
    },
  };
}

test('V6.0.1 Documents sheet exposes complete live inventory, filters and roles',()=>{
 setup('admin');
 const page=renderCloudPage('documents');
 for(const id of ['v601DocSearch','v601DocCategory','v601DocStatus','v601DocSort',
                   'v601DocLatest','v601DocTableBody','v601DocExport']){
  assert.ok(page.includes(id),'missing document control: '+id);
 }
 assert.match(page,/Kiểm kê toàn bộ file Drive/);
 assert.match(page,/Quản lý hồ sơ/);
 assert.match(page,/CHƯA GHI SỔ/);
 assert.match(page,/CHỜ DUYỆT/);
 assert.match(page,/data-workspace-op="document_manage"/);
});

test('V6.0.1 unscanned inventory has explicit reconciliation action and registered fallback',()=>{
 setup('read',false);
 const page=renderCloudPage('documents');
 assert.match(page,/Nhấn/);
 assert.match(page,/BOM_R01.xlsx/);
 assert.match(page,/Kiểm kê toàn bộ file Drive/);
});

test('V6.0.1 frontend and Streamlit runtime retain same source',()=>{
 const source=fs.readFileSync(new URL('../src/core/cloud_workspace.js',import.meta.url),'utf8');
 const mirror=fs.readFileSync(new URL('../static/src/core/cloud_workspace.js',import.meta.url),'utf8');
 assert.equal(source,mirror);
 assert.match(source,/data-v601-file/);
 assert.match(source,/const h=value/);
 const backend=fs.readFileSync(new URL('../drive_storage/workspace_ui.py',import.meta.url),'utf8');
 assert.match(backend,/xd_doc_inventory_requested/);
 assert.match(backend,/document_manage/);
 const manager=fs.readFileSync(new URL('../drive_storage/manager.py',import.meta.url),'utf8');
 assert.match(manager,/md5Checksum/);
});
