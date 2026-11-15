import {downloadBlob} from './documents.js';
export function exportJson(data,filename){const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'});downloadBlob(blob,filename);}
