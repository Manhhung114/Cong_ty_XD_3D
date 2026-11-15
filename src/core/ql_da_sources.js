// Official-source metadata from QLDA_ver612_VPS, maintained independently of app releases.
// A GitHub repository is the distribution channel, never the issuing authority.
import {isOfficialUrl,standardKey} from './standards.js';
export const QLDA_SOURCE_LOCAL='./data/legal/QLDA_official_catalog_seed.json';
export const QLDA_SOURCE_REMOTE='https://raw.githubusercontent.com/Manhhung114/QLDA_ver612_VPS/main/data/legal/official_catalog.json';
const CACHE_KEY='xd-mep-qlda-official-legal-v1';
const GROUPS=['Xây dựng – Quản lý dự án','MEPF – Phòng cháy chữa cháy'];
const LEGAL_NUMBER=/^(?:\d+[\w./-]*\/\d{4}\/[\wÀ-Ỹ.-]+|TCVN\s*\d+(?:-\d+)*:\d{4}|QCVN\s*\d+(?:[-.]\d+)?:\d{4}\/[A-Z]+)$/i;
export function validateQLDACatalog(value){
  if(value?.schema!=='qlda-official-legal-v1'||!Array.isArray(value.vanBan)||value.vanBan.length>1000)throw Error('Danh mục QLDA không đúng cấu trúc.');
  const seen=new Set();const cleaned=[];
  for(const item of value.vanBan){
    const row={...item};const num=String(row.soHieu||'').trim();
    const title=String(row.ten||'').trim();const link=String(row.duongDan||'');
    if(!GROUPS.includes(row.linhVuc)||!LEGAL_NUMBER.test(num)||!title||title.length>450||!isOfficialUrl(link)||/dự thảo|du thao/i.test(`${title} ${row.tinhTrang||''}`))throw Error('Có văn bản không đủ nguồn chính thống hoặc sai số hiệu.');
    if(num.toUpperCase().startsWith('TCVN')&&new URL(link).hostname!=='tieuchuan.vsqi.gov.vn')throw Error('TCVN cần dẫn trực tiếp đến VSQI.');
    const key=standardKey({...row,soHieu:num});if(seen.has(key))continue;seen.add(key);
    cleaned.push({...row,soHieu:num,ten:title,tenAnh:String(row.tenAnh||'').slice(0,450),
      kiemChung:String(row.kiemChung||'').slice(0,450),ghiChu:String(row.ghiChu||'').slice(0,700)});
  }
  return {reviewedAt:String(value.reviewedAt||''),vanBan:cleaned};
}
export function getQLDACatalogCache(){try{const raw=localStorage.getItem(CACHE_KEY);return raw?validateQLDACatalog(JSON.parse(raw)):null}catch{return null}}
export async function updateQLDACatalog(fetcher=fetch){
  const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),12000);
  try{
    const r=await fetcher(QLDA_SOURCE_REMOTE,{cache:'no-store',signal:ctrl.signal});
    if(!r.ok)throw Error(`HTTP ${r.status}`);
    const data=await r.json();const verified=validateQLDACatalog(data);
    // Atomic write only after every record passes. Invalid remote updates preserve last good catalog.
    localStorage.setItem(CACHE_KEY,JSON.stringify({schema:'qlda-official-legal-v1',reviewedAt:verified.reviewedAt,vanBan:verified.vanBan}));
    return {count:verified.vanBan.length,reviewedAt:verified.reviewedAt};
  }finally{clearTimeout(timer)}
}
