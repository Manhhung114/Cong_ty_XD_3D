// V5.4: official-source standards catalog inspired by QLDA_ver612_VPS's
// standards backfill/search approach; it does not scrape, redistribute or
// imply that a GitHub repository itself is an authoritative legal source.
export const STANDARDS_FILE = './data/legal/TCVN_QLDA_VPS_verified.json';
export const STANDARDS_REMOTE = 'https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/TCVN_QLDA_VPS_verified.json';
export const STANDARDS_TEMPLATE = './data/legal/TCVN_UPDATE_TEMPLATE.json';
const CACHE_KEY = 'xd-mep-standards-v54-repository-cache';
const MANUAL_KEY = 'xd-mep-standards-v54-manual';
const OFFICIAL_HOSTS = [
  'tieuchuan.vsqi.gov.vn','vbpl.vn','vanban.chinhphu.vn','moc.gov.vn',
  'bxd.gov.vn','moj.gov.vn','bocongan.gov.vn','congbao.chinhphu.vn',
];
export function isOfficialUrl(value){
  try {const u=new URL(String(value||''));return u.protocol==='https:'&&OFFICIAL_HOSTS.some(x=>u.hostname===x||u.hostname.endsWith('.'+x));}
  catch{return false;}
}
export const standardKey = d => `${String(d.linhVuc||'').trim().toLocaleLowerCase('vi-VN')}:${String(d.soHieu||'').replace(/\s+/g,'').toUpperCase()}`;
export function validateStandards(payload,{unverified=false}={}){
  const rows=Array.isArray(payload)?payload:payload?.vanBan;
  if(!Array.isArray(rows)||rows.length>1000)throw Error('Danh mục JSON phải chứa vanBan là mảng, tối đa 1000 mục.');
  const good=[];const bad=[];
  for(const [i,x] of rows.entries()){
    if(!x||typeof x!=='object'||Array.isArray(x)){bad.push(i+1);continue;}
    const number=String(x.soHieu||'').trim().slice(0,100);
    const title=String(x.ten||'').trim().slice(0,320);
    const field=String(x.linhVuc||'').trim();
    const url=String(x.duongDan||'').trim();
    const text=[x.ten,x.ghiChu,x.loai].join(' ').toLowerCase();
    if(!/^(?:TCVN\s*\d+(?:-\d+)*:\d{4}|QCVN\s*\d+(?:[-.]\d+)?:\d{4}\/\w+)$/i.test(number)||!title||!['MEPF – Phòng cháy chữa cháy','Xây dựng – Quản lý dự án'].includes(field)||!isOfficialUrl(url)||/dự thảo|du thao/.test(text)){bad.push(i+1);continue;}
    // TCVN entries need a traceable standard listing, not third-party copies.
    if(/^TCVN/i.test(number)&&new URL(url).hostname!=='tieuchuan.vsqi.gov.vn'){bad.push(i+1);continue;}
    const row={...x,id:String(x.id||`LOCAL-${i+1}`).slice(0,80),linhVuc:field,soHieu:number,ten:title,
      tenAnh:String(x.tenAnh||'').slice(0,320),nhom:String(x.nhom||'Khác').slice(0,100),loai:String(x.loai||'Tiêu chuẩn TCVN').slice(0,100),
      duongDan:url,nguon:String(x.nguon||'VSQI').slice(0,100),ghiChu:String(x.ghiChu||'').slice(0,700)};
    if(unverified){row.tinhTrang='Chờ đối chiếu nguồn';row.kiemChung='Chưa xác thực thủ công';row.ngayRaSoat='';}
    good.push(row);
  }
  if(bad.length)throw Error(`Có ${bad.length} dòng không đạt quy tắc nguồn chính thống/số hiệu hoặc là dự thảo (vị trí: ${bad.slice(0,8).join(', ')}).`);
  return good;
}
export function mergeStandards(base=[],verified=[],manual=[],remote=[]){
  const result=new Map();
  for(const row of [...base,...verified,...remote]){const key=standardKey(row);if(key&&row.soHieu)result.set(key,row);}
  // Manual records never silently override reviewed official data.
  for(const row of manual){const key=standardKey(row);if(key&&!result.has(key))result.set(key,row);}
  return [...result.values()];
}
function read(key){try{const v=localStorage.getItem(key);return v?JSON.parse(v):null;}catch{return null;}}
function write(key,value){localStorage.setItem(key,JSON.stringify(value));}
export function getStandardsCache(){return {remote:read(CACHE_KEY),manual:read(MANUAL_KEY)};}
export function saveManualStandards(payload){const newRows=validateStandards(payload,{unverified:true});const old=read(MANUAL_KEY)?.vanBan||[];const list=[...old];for(const n of newRows){const i=list.findIndex(x=>standardKey(x)===standardKey(n));if(i>=0)list[i]=n;else list.push(n);}write(MANUAL_KEY,{updatedAt:new Date().toISOString(),vanBan:list});return {added:newRows.length,total:list.length};}
export async function checkRemoteStandards(fetcher=fetch){
  const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),12000);
  try{
    const response=await fetcher(STANDARDS_REMOTE,{cache:'no-store',signal:ctrl.signal});
    if(!response.ok)throw Error('HTTP '+response.status);
    const payload=await response.json();const rows=validateStandards(payload);
    write(CACHE_KEY,{updatedAt:new Date().toISOString(),reviewedAt:payload.reviewedAt||'',vanBan:rows});
    return {count:rows.length,reviewedAt:payload.reviewedAt||''};
  } finally{clearTimeout(timer);}
}
export function clearImportedStandards(){localStorage.removeItem(MANUAL_KEY);localStorage.removeItem(CACHE_KEY);}
