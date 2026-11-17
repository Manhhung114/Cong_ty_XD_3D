"""Server-only, read-only API connectivity check for the Admin AI settings.

Checks access to configured model metadata, NOT text generation. No prompts,
tokens, API keys, provider error bodies, or exception details enter the UI/log.
"""
from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from drive_storage.ai_vault import _validate


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an Authorization or x-goog-api-key header elsewhere.
        return None


def _open(request: Request):
    return build_opener(_NoRedirects).open(request, timeout=8)


def probe_ai_connection(provider: str, model: str, api_key: str) -> dict:
    """Perform one authenticated GET for an exact known provider/model.

    Returns only public provider/model names, a boolean and a safe Vietnamese
    message. Fail closed for unknown input, network problems and HTTP failures.
    No token-consuming inference is performed and nothing is persisted.
    """
    config = _validate(provider, model, api_key)
    provider = config["provider"]
    model = config["model"]
    if provider == "openai":
        url = "https://api.openai.com/v1/models/" + model
        headers = {"Authorization": "Bearer " + config["api_key"]}
    else:
        url = "https://generativelanguage.googleapis.com/v1beta/models/" + model
        headers = {"x-goog-api-key": config["api_key"]}
    req = Request(url, headers=headers, method="GET")
    try:
        with _open(req) as response:
            status = response.getcode()
    except HTTPError as exc:
        status = exc.code
    except (URLError, OSError, TimeoutError):
        return {"ok": False, "provider": provider, "model": model,
                "message": "Không liên hệ được nhà cung cấp AI (mạng, DNS hoặc hết thời gian)."}
    if status == 200:
        return {"ok": True, "provider": provider, "model": model,
                "message": "Đã xác thực API key và truy cập được thông tin model."}
    errors = {
        400: "Yêu cầu kiểm tra không được nhà cung cấp chấp nhận (HTTP 400).",
        401: "API key không hợp lệ hoặc đã bị thu hồi (HTTP 401).",
        403: "API key không có quyền hoặc dịch vụ chưa được bật (HTTP 403).",
        404: "Không tìm thấy hoặc không được truy cập model đã chọn (HTTP 404).",
        429: "Nhà cung cấp đang giới hạn yêu cầu hoặc hạn mức (HTTP 429).",
    }
    message = errors.get(status, "Nhà cung cấp AI chưa phản hồi thành công.")
    return {"ok": False, "provider": provider, "model": model,
            "message": message}
