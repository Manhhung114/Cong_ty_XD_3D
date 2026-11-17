"""V7.4 opt-in provider connectors. Keys are NEVER stored in DB or browser.

Existing encrypted OpenAI/Gemini vault remains the default; optional Claude
and local Ollama are available ONLY via explicit worker environment settings,
consent and per-run model allowlist.
"""
from __future__ import annotations
import json
import os
import re
from urllib import request
from urllib.parse import urlparse

MODEL = re.compile(r"^[A-Za-z0-9._:/-]{2,100}$")
MAX_REPLY = 6000


def optional_config():
    vendor=os.getenv("AGENT_RUNTIME_OPTIONAL_PROVIDER","").lower()
    if vendor not in {"anthropic","ollama"}:
        return None
    model=os.getenv("AGENT_RUNTIME_OPTIONAL_MODEL","")
    if not MODEL.fullmatch(model):
        raise ValueError("Model tùy chọn không hợp lệ")
    if vendor=="anthropic" and not os.getenv("AGENT_RUNTIME_ANTHROPIC_KEY",""):
        raise ValueError("Thiếu API key Anthropic trên worker")
    if vendor=="ollama":
        endpoint=os.getenv("AGENT_RUNTIME_OLLAMA_URL","http://127.0.0.1:11434")
        parsed=urlparse(endpoint)
        if parsed.scheme!="http" or parsed.hostname not in {"localhost","127.0.0.1","ollama"}:
            raise ValueError("Ollama chỉ được gọi trên mạng nội bộ")
    return {"provider":vendor,"model":model}


def call_optional(text, *, consent=False, opener=None):
    config=optional_config()
    if config is None:
        raise ValueError("Chưa chọn nhà cung cấp mô hình tùy chọn")
    if not consent:
        raise PermissionError("Chưa đồng ý chia sẻ dữ liệu trích xuất")
    if len(text)>12000:
        raise ValueError("Dữ liệu Agent vượt giới hạn mẫu")
    opener=opener or request.urlopen
    if config["provider"]=="anthropic":
        endpoint="https://api.anthropic.com/v1/messages"
        body={"model":config["model"],"max_tokens":1000,"messages":[
            {"role":"user","content":text}]}
        headers={"x-api-key":os.environ["AGENT_RUNTIME_ANTHROPIC_KEY"],
                 "anthropic-version":"2023-06-01","content-type":"application/json"}
    else:
        endpoint=os.getenv("AGENT_RUNTIME_OLLAMA_URL","http://127.0.0.1:11434").rstrip("/")+"/api/generate"
        body={"model":config["model"],"prompt":text,"stream":False,
              "options":{"num_predict":1000}}
        headers={"content-type":"application/json"}
    req=request.Request(endpoint,data=json.dumps(body).encode(),headers=headers,method="POST")
    try:
        with opener(req,timeout=35) as response:
            payload=json.loads(response.read(65536).decode())
        if config["provider"]=="anthropic":
            reply="\n".join(str(b.get("text","")) for b in payload.get("content",[]) if b.get("type")=="text")
        else:
            reply=str(payload.get("response",""))
    except Exception:
        raise RuntimeError("Lỗi mô hình tùy chọn; xem log bảo mật trên máy chủ") from None
    if not reply:
        raise RuntimeError("Mô hình không trả nội dung")
    return {"provider":config["provider"],"model":config["model"],
            "draft":reply[:MAX_REPLY],"humanReviewRequired":True}
