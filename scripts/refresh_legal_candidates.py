#!/usr/bin/env python3
"""Only Cong_ty_XD_3D: discover official legal links. Never modify QLDA data."""
from __future__ import annotations
import argparse,json,re,sys,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY=ROOT/'data/legal/MEP_XD_source_registry.json'
DEFAULT_OUTPUT=ROOT/'data/legal/MEP_XD_source_candidates.json'
NUM=re.compile(r'(?i)\b(?:TCVN\s*\d+(?:-\d+)*\s*:\s*\d{4}|QCVN\s*\d+(?:[-.]\d+)?\s*:\s*\d{4}\s*/\s*[A-Z]+|\d{1,4}\s*/\s*20\d{2}\s*/\s*(?:QH\d+|NĐ-CP|ND-CP|TT-[A-Z]+|QĐ-[A-Z]+|VBHN-[A-Z]+))\b')
DRAFT=re.compile(r'dự\s*thảo|du\s*thao|draft',re.I)
MEP=re.compile(r'điện|cơ điện|cấp nước|thoát nước|thông gió|điều hòa|pccc|báo cháy|chữa cháy|hvac|electrical|plumbing',re.I)
XD=re.compile(r'xây dựng|công trình|kết cấu|móng|cọc|bê tông|dự án|hợp đồng|thi công|nghiệm thu|vật liệu',re.I)
DETAIL={'vbpl.vn':('vbpq-','vbpq-toanvan'),'vanban.chinhphu.vn':('van-ban/','van-ban-phap-luat'),
'congbao.chinhphu.vn':('/van-ban/',),'www.moc.gov.vn':('/vanban','/van-ban','pages/chitiet'),
'tieuchuan.vsqi.gov.vn':('/tieuchuan/','/tieu-chuan/'),
'tieuchuanxaydung.vsqi.gov.vn':('/tieuchuan/','/tieu-chuan/','/chitiet')}

def allowed_url(link,hosts):
    try:
        u=urlsplit(link)
        return u.scheme=='https' and not u.username and not u.password and u.port in (None,443) and u.hostname in hosts
    except (TypeError,ValueError):return False

def extract_candidates(html,listing,site,hosts):
    result=[]
    for a in BeautifulSoup(html,'html.parser').select('a[href]'):
        href=a.get('href') or ''
        if href.startswith(('javascript:','data:','#')):continue
        link=urljoin(listing,href)
        if not allowed_url(link,hosts):continue
        u=urlsplit(link)
        if not any(p in (u.path+'?'+u.query).casefold() for p in DETAIL.get(u.hostname,())):continue
        text=a.get_text(' ',strip=True)
        parent=a.parent.get_text(' ',strip=True)[:450] if a.parent and len(text)<=15 else text
        title=text if len(text)>15 else parent
        if DRAFT.search(title+' '+link):continue
        hit=NUM.search(title) or NUM.search(parent) or NUM.search(link.replace('%3A',':'))
        if not hit:continue
        num=re.sub(r'\s+','',hit.group()).upper().replace('ND-CP','NĐ-CP')
        mep=bool(MEP.search(title));xd=bool(XD.search(title))
        fields=site.get('fields',[])
        tags=[k for k in ('construction','mepf') if k in fields] if mep and xd else (['mepf'] if mep and 'mepf' in fields else ['construction'] if xd and 'construction' in fields else fields[:1])
        for tag in tags:
            result.append({'linhVuc':'MEPF – Phòng cháy chữa cháy' if tag=='mepf' else 'Xây dựng – Quản lý dự án',
              'soHieu':num,'ten':re.sub(r'\s+',' ',title)[:350],'duongDan':link,
              'nguon':site['name'],'tinhTrang':'Chờ đối chiếu nguồn và hiệu lực',
              'kiemChung':'Chỉ phát hiện liên kết trên trang nguồn, chưa xác minh hiệu lực'})
    return result

def refresh(registry,get=None):
    getter=get or requests.Session().get
    hosts={s['host'] for s in registry['sites']};found=[];status={}
    for site in registry['sites']:
        try:
            response=getter(site['url'],headers={'User-Agent':'Cong_ty_XD_3D legal-source/1.0'},timeout=12)
            response.raise_for_status()
            rows=extract_candidates(response.text,site['url'],site,hosts)[:120]
            found+=rows;status[site['id']]={'status':'ok','found':len(rows)}
        except (requests.RequestException,ValueError,RuntimeError) as exc:
            status[site['id']]={'status':'unavailable','reason':type(exc).__name__}
        time.sleep(.2)
    unique={}
    for r in found:unique.setdefault((r['linhVuc'],r['soHieu']),r)
    return {'schema':'mepxd-official-discovery-v1','generatedAt':datetime.now(timezone.utc).isoformat(),
      'sources':status,'method':'Unverified official-site links only','candidates':list(unique.values())}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources',type=Path,default=DEFAULT_REGISTRY)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    registry=json.loads(args.sources.read_text(encoding='utf8'))
    if registry.get('schema')!='mepxd-official-source-registry-v1':sys.exit('Invalid source registry')
    data=refresh(registry)
    if args.dry_run:
        print(json.dumps({'sources':data['sources'],'found':len(data['candidates'])},ensure_ascii=False,indent=2));return 0
    if not data['candidates']:
        print('No indexed links; previous candidate list remains untouched',file=sys.stderr);return 3
    args.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=args.output.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    tmp.replace(args.output)
    print('Discovered',len(data['candidates']),'candidate links, not effective-law determinations')
    return 0
if __name__=='__main__':raise SystemExit(main())
