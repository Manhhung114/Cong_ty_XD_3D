"""Streamlit server-only HTTPS client for the isolated background Agent runtime."""
from __future__ import annotations
import json
import os
import time
from urllib import request, error, parse
from .security import signature


class RuntimeClient:
    def __init__(self, url: str, secret: str, opener=None):
        self.url = (url or "").rstrip("/")
        self.secret = secret
        self.opener = opener or request.urlopen
        internal = os.getenv("AGENT_RUNTIME_ALLOW_DOCKER_HTTP") == "1" and (
            self.url.startswith("http://agent-api:8082"))
        if not (self.url.startswith("https://") or internal or
                self.url.startswith("http://127.0.0.1:") or
                self.url.startswith("http://localhost:")):
            raise ValueError("Runtime API cần HTTPS hoặc localhost")
        from .security import must_secret
        must_secret(secret)

    def send(self, path: str, data: dict, *, timeout=10):
        raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        ts = int(time.time())
        endpoint = self.url + path
        http = request.Request(endpoint, data=raw, method="POST", headers={
            "Content-Type": "application/json",
            "X-XD-Timestamp": str(ts),
            "X-XD-Signature": signature(self.secret, ts, "POST", path, raw),
        })
        try:
            with self.opener(http, timeout=timeout) as response:
                result = json.loads(response.read(400000).decode("utf8"))
        except error.HTTPError as exc:
            # Do not echo private backend URL, server trace or any credentials.
            if exc.code in (401,403):
                raise PermissionError("Runtime từ chối xác thực/ACL (HTTP " + str(exc.code) + ")") from None
            if exc.code == 503:
                raise RuntimeError("Worker/Redis chưa sẵn sàng (HTTP 503)") from None
            raise RuntimeError("Không thể hoàn tất Runtime API (HTTP " + str(exc.code) + ")") from None
        except (error.URLError, TimeoutError):
            raise RuntimeError("Chưa kết nối được runtime worker") from None
        if not isinstance(result, dict):
            raise RuntimeError("Phản hồi runtime không hợp lệ")
        return result


def configured_client(st):
    try:
        block = dict(st.secrets.get("runtime", {}))
        url = str(block.get("api_url") or os.getenv("XD_RUNTIME_API_URL") or "").strip()
        secret = str(block.get("internal_secret") or os.getenv("AGENT_RUNTIME_SECRET") or "").strip()
        if not url and not secret:
            return None
        return RuntimeClient(url, secret)
    except (KeyError, ValueError, RuntimeError, TypeError):
        return None


def public_jobs(st, identity, project_id):
    client = configured_client(st)
    if client is None:
        return {"enabled": False, "jobs": [], "message": "Chưa kết nối runtime V7.4"}
    try:
        result = client.send("/api/runtime/jobs/query", {
            "projectId": project_id, "identity": identity,
        })
        return {"enabled": True, "jobs": result.get("jobs", [])[:150], "message": ""}
    except (PermissionError, RuntimeError) as exc:
        return {"enabled": False, "jobs": [], "message": str(exc)}
