import importlib.util
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'refresh_tvpl_candidates.py'
spec = importlib.util.spec_from_file_location('tvpl_refresh', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = '''<html><body>
<a href="/van-ban/xay-dung-do-thi/luat-xay-dung-123.aspx">Luật Xây dựng số 135/2025/QH15</a>
<a href="https://thuvienphapluat.vn/TCVN/Xay-dung/tcvn-5687-921033.aspx">Tiêu chuẩn TCVN 5687:2024 thông gió điều hòa không khí</a>
<a href="https://evil.example/van-ban/fake">Luật Xây dựng 135/2025/QH15</a>
<a href="/van-ban/xay-dung/draft">Dự thảo Luật Xây dựng 123/2026/QH16</a>
<a href="/van-ban/finance/banking">Quyết định ngân hàng 50/2026/QĐ-NHNN</a>
</body></html>'''

def test_parser_returns_only_public_relevant_law_or_standard_links():
    rows=mod.extract(SAMPLE,'https://m.thuvienphapluat.vn/')
    assert len(rows)==2
    assert rows[0]['soHieu']=='135/2025/QH15'
    assert rows[1]['soHieu']=='TCVN 5687:2024'
    assert all(mod.allowed_url(x['duongDan']) for x in rows)

def test_url_guard():
    assert mod.allowed_url('https://m.thuvienphapluat.vn/van-ban/xay-dung/a.aspx')
    assert not mod.allowed_url('https://evil.net/van-ban/x.aspx')
    assert not mod.allowed_url('https://thuvienphapluat.vn.evil.net/van-ban/x.aspx')
    assert not mod.allowed_url('http://thuvienphapluat.vn/van-ban/x.aspx')

def test_no_records_on_inaccessible_site():
    import requests
    def deny(url, **kwargs):
        raise requests.ConnectionError('blocked')
    payload=mod.refresh(getter=deny,pages=['https://m.thuvienphapluat.vn/'])
    assert payload['candidates']==[]
    assert list(payload['sourceLog'].values())[0]['status']=='unavailable'
