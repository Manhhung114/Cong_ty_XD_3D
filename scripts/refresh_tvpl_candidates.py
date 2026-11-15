#!/usr/bin/env python3
"""Discover only public TVPL document metadata for XD & MEPF, never full text.

TVPL is a third-party reference source; this output must not enter the verified
legal catalog without human comparison with official publication/VSQI.
No login, paywall or anti-bot bypass. Network/access failure retains old JSON.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/legal/MEP_XD_tvpl_candidates.json'
PAGES = (
    'https://m.thuvienphapluat.vn/',
    'https://thuvienphapluat.vn/page/Tim-Van-Ban.aspx',
)
HOSTS = {'m.thuvienphapluat.vn', 'thuvienphapluat.vn', 'www.thuvienphapluat.vn'}
NUMBER = re.compile(
    r'(?i)\b(?:TCVN\s*\d+(?:-\d+)*\s*:\s*\d{4}'
    r'|QCVN\s*\d+(?:[-.]\d+)?\s*:\s*\d{4}\s*/\s*[A-Z]+'
    r'|\d{1,4}\s*/\s*(?:19|20)\d{2}\s*/\s*(?:QH\d+|NĐ-CP|ND-CP|TT-[A-Z]+|QĐ-[A-Z]+|VBHN-[A-Z0-9/-]+))\b'
)
CONSTRUCTION = re.compile(r'xây dựng|kiến trúc|quản lý dự án|thi công|kết cấu|bê tông|tải trọng|nền móng|hợp đồng xây dựng|dự toán|chất lượng công trình|quy hoạch|đấu thầu', re.I)
MEPF = re.compile(r'pccc|phòng cháy|chữa cháy|cứu nạn|cứu hộ|điện|điều hòa|thông gió|cấp nước|thoát nước|báo cháy|chống sét|chiếu sáng|hệ thống chữa cháy', re.I)
DRAFT = re.compile(r'dự\s*thảo|du\s*thao|draft', re.I)


def allowed_url(url: str) -> bool:
    try:
        u = urlsplit(url)
        return (u.scheme == 'https' and u.hostname in HOSTS and not u.username
                and not u.password and u.port in (None, 443)
                and (u.path.lower().startswith('/van-ban/') or u.path.lower().startswith('/tcvn/')))
    except (TypeError, ValueError):
        return False


def normalize_number(value: str) -> str:
    compact = re.sub(r'\s+', '', value).upper().replace('ND-CP', 'NĐ-CP')
    return re.sub(r'^(TCVN|QCVN)(\d)', r'\1 \2', compact)


def classify(text: str) -> str | None:
    # The two branches are exclusive for candidate deduplication. Shared docs
    # can be tagged after human review rather than auto-counted twice.
    if MEPF.search(text):
        return 'MEPF – Phòng cháy chữa cháy'
    if CONSTRUCTION.search(text):
        return 'Xây dựng – Quản lý dự án'
    return None


def extract(html: str, listing_url: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        target = urljoin(listing_url, a.get('href', ''))
        if not allowed_url(target):
            continue
        label = re.sub(r'\s+', ' ', a.get_text(' ', strip=True))[:350]
        # Only metadata in visible link text is accepted; never infer a document
        # number from an unrelated article or from document body text.
        if len(label) < 12 or DRAFT.search(label):
            continue
        number = NUMBER.search(label)
        if not number:
            continue
        field = classify(label)
        if not field:
            continue
        out.append({
            'linhVuc': field, 'soHieu': normalize_number(number.group()),
            'ten': label, 'duongDan': target,
        })
    return out


def refresh(*, getter=requests.get, pages=PAGES, max_per_page=120) -> dict:
    results: list[dict] = []
    log: dict[str, dict] = {}
    for url in pages:
        try:
            response = getter(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; XDMEP legal-links/1.0; metadata only)'
            })
            response.raise_for_status()
            found = extract(response.text, url)[:max_per_page]
            results.extend(found)
            log[url] = {'status': 'ok', 'found': len(found)}
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            log[url] = {'status': 'unavailable', 'reason': type(exc).__name__}
        time.sleep(0.25)
    unique: dict[tuple[str, str], dict] = {}
    for item in results:
        unique.setdefault((item['linhVuc'], item['soHieu']), item)
    return {
        'schema': 'mepxd-tvpl-discovery-v1',
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': 'TVPL public links, unverified; not an official legal source',
        'sourceLog': log,
        'candidates': list(unique.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    report = refresh()
    print(json.dumps({'status': report['sourceLog'], 'candidates': len(report['candidates'])}, ensure_ascii=False))
    if args.dry_run:
        return 0
    if not report['candidates']:
        print('No public relevant TVPL document links; keeping previously saved candidate file.', file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix('.json.tmp')
    temp.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    temp.replace(args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
