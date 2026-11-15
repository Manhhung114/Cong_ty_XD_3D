// Independent official-source metadata owned by Cong_ty_XD_3D; QLDA provided methodology only.
// A GitHub repository is the distribution channel, never the issuing authority.
import {isOfficialUrl,standardKey} from './standards.js';
export const MEP_SOURCE_LOCAL='./data/legal/MEP_XD_official_catalog.json';
export const MEP_SOURCE_REMOTE='https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/MEP_XD_official_catalog.json';
const CACHE_KEY='xd-mep-official-sources-v1';
const GROUPS=['Xây dựng – Quản lý dự án','MEPF – Phòng cháy chữa cháy'];
const LEGAL_NUMBER=/^(?:\d+[\w./-]*\/\d{4}\/[\wÀ-Ỹ.-]+|TCVN\s*\d+(?:-\d+)*:\d{4}|QCVN\s*\d+(?:[-.]\d+)?:\d{4}\/[A-Z]+)$/i;
export function validateMEPCatalog(value){
  if(value?.schema!=='mepxd-official-legal-v1'||!Array.isArray(value.vanBan)||value.vanBan.length>1000)throw Error('Danh mục XD & MEP không đúng cấu trúc.');
  const seen=new Set();const cleaned=[];
  for(const item of value.vanBan){
    const row={...item};const num=String(row.soHieu||'').trim();
    const title=String(row.ten||'').trim();const link=String(row.duongDan||'');
    if(!GROUPS.includes(row.linhVuc)||!LEGAL_NUMBER.test(num)||!title||title.length>450||!isOfficialUrl(link)||/dự thảo|du thao/i.test(`${title} ${row.tinhTrang||''}`))throw Error('Có văn bản không đủ nguồn chính thống hoặc sai số hiệu.');
    if(num.toUpperCase().startsWith('TCVN')&&!['tieuchuan.vsqi.gov.vn','tieuchuanxaydung.vsqi.gov.vn'].includes(new URL(link).hostname))throw Error('TCVN cần dẫn trực tiếp đến VSQI.');
    const key=standardKey({...row,soHieu:num});if(seen.has(key))continue;seen.add(key);
    cleaned.push({...row,soHieu:num,ten:title,tenAnh:String(row.tenAnh||'').slice(0,450),
      kiemChung:String(row.kiemChung||'').slice(0,450),ghiChu:String(row.ghiChu||'').slice(0,700)});
  }
  return {reviewedAt:String(value.reviewedAt||''),vanBan:cleaned};
}
export function getMEPCatalogCache(){try{const raw=localStorage.getItem(CACHE_KEY);return raw?validateMEPCatalog(JSON.parse(raw)):null}catch{return null}}
export async function updateMEPCatalog(fetcher=fetch){
  const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),12000);
  try{
    const r=await fetcher(MEP_SOURCE_REMOTE,{cache:'no-store',signal:ctrl.signal});
    if(!r.ok)throw Error(`HTTP ${r.status}`);
    const data=await r.json();const verified=validateMEPCatalog(data);
    // Atomic write only after every record passes. Invalid remote updates preserve last good catalog.
    localStorage.setItem(CACHE_KEY,JSON.stringify({schema:'mepxd-official-legal-v1',reviewedAt:verified.reviewedAt,vanBan:verified.vanBan}));
    return {count:verified.vanBan.length,reviewedAt:verified.reviewedAt};
  }finally{clearTimeout(timer)}
}

export const MEP_SOURCE_REGISTRY='./data/legal/MEP_XD_source_registry.json';
export const MEP_SOURCE_CANDIDATES='https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/MEP_XD_source_candidates.json';
export const MEP_REFRESH_WORKFLOW='https://github.com/Manhhung114/Cong_ty_XD_3D/actions/workflows/refresh-mep-legal.yml';
export function validateDiscovery(payload){
  if(payload?.schema!=='mepxd-official-discovery-v1'||!Array.isArray(payload.candidates)||payload.candidates.length>2000)throw Error('Danh sách phát hiện chưa đúng định dạng');
  return payload.candidates.filter(x=>typeof x?.soHieu==='string'&&typeof x?.duongDan==='string'&&isOfficialUrl(x.duongDan)).map(x=>({...x,tinhTrang:'Chờ đối chiếu – chưa xác nhận hiệu lực'}));
}
export async function checkMEPDiscoveries(fetcher=fetch){
  const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),12000);
  try{
    const r=await fetcher(MEP_SOURCE_CANDIDATES,{cache:'no-store',signal:ctrl.signal});
    if(!r.ok)throw Error('HTTP '+r.status);
    const d=await r.json(),rows=validateDiscovery(d);
    return {count:rows.length,generatedAt:d.generatedAt||'',rows};
  }finally{clearTimeout(timer)}
}
