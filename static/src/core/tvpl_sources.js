// TVPL is an independent, third-party discovery reference — NOT an official legal source.
// Never merge these entries into the reviewed catalog, validity statistics or legal conclusions.
export const TVPL_HOME='https://m.thuvienphapluat.vn/';
export const TVPL_SEARCH='https://thuvienphapluat.vn/page/Tim-Van-Ban.aspx';
export const TVPL_CANDIDATES_REMOTE='https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/MEP_XD_tvpl_candidates.json';
export const TVPL_REFRESH_WORKFLOW='https://github.com/Manhhung114/Cong_ty_XD_3D/actions/workflows/refresh-tvpl.yml';
export const TVPL_SCHEMA='mepxd-tvpl-discovery-v1';
const CACHE_KEY='mepxd-tvpl-discovery-cache-v1';
const FIELDS=new Set(['Xây dựng – Quản lý dự án','MEPF – Phòng cháy chữa cháy']);
const NUMBER=/^(?:TCVN\s*\d+(?:-\d+)*:\d{4}|QCVN\s*\d+(?:[-.]\d+)?:\d{4}\/[A-Z]+|\d{1,4}\/(?:19|20)\d{2}\/[\p{L}\d./-]{2,50})$/iu;
export function isTVPLUrl(value){
 try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&(!u.port||u.port==='443')&&['thuvienphapluat.vn','m.thuvienphapluat.vn','www.thuvienphapluat.vn'].includes(u.hostname);}catch{return false;}
}
export function validateTVPLCandidates(payload){
 if(payload?.schema!==TVPL_SCHEMA||!Array.isArray(payload.candidates)||payload.candidates.length>400)throw Error('Định dạng danh mục TVPL không hợp lệ');
 const unique=new Set(),rows=[];
 for(const item of payload.candidates){
  if(!item||typeof item!=='object')continue;
  const soHieu=String(item.soHieu||'').trim(),ten=String(item.ten||'').trim(),duongDan=String(item.duongDan||'').trim();
  if(!FIELDS.has(item.linhVuc)||!NUMBER.test(soHieu)||ten.length<8||ten.length>350||!isTVPLUrl(duongDan)||/dự thảo|du thao|draft/i.test(`${ten} ${item.tinhTrang||''}`))continue;
  const key=item.linhVuc+'|'+soHieu.replace(/\s/g,'').toUpperCase();if(unique.has(key))continue;unique.add(key);
  rows.push({soHieu,ten,duongDan,linhVuc:item.linhVuc,nguon:'Thư Viện Pháp Luật',tinhTrang:'Chờ đối chiếu với nguồn chính thống'});
 }
 return {schema:TVPL_SCHEMA,generatedAt:String(payload.generatedAt||''),status:String(payload.status||'unknown'),source:'TVPL (tham khảo)',candidates:rows};
}
export function getTVPLCache(){try{const raw=localStorage.getItem(CACHE_KEY);return raw?validateTVPLCandidates(JSON.parse(raw)):null;}catch{return null;}}
export async function checkTVPLUpdates(fetcher=fetch,storage=typeof localStorage==='undefined'?null:localStorage){
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),15000);
 try{
  const response=await fetcher(TVPL_CANDIDATES_REMOTE,{cache:'no-store',signal:ctrl.signal});
  if(!response.ok)throw Error('HTTP '+response.status);
  const checked=validateTVPLCandidates(await response.json());
  if(storage)storage.setItem(CACHE_KEY,JSON.stringify(checked));
  return {count:checked.candidates.length,generatedAt:checked.generatedAt,rows:checked.candidates,status:checked.status};
 }finally{clearTimeout(timer);}
}
