"""Authenticated server-to-server requests: no API key or service secret enters iframe."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import time

HEX_ID = re.compile(r"^[0-9a-f]{32}$")
GOOGLE_ID = re.compile(r"^[A-Za-z0-9_-]{12,160}$")
AGENT_ID = re.compile(r"^[A-Z0-9]{2,6}$")
MODES = {"preflight", "expert", "llm", "expert_llm"}
COST_ESTIMATE = {"preflight": 0.0, "expert": 0.0, "llm": 0.06, "expert_llm": 0.09}
PERMITTED_ROLES = {"update", "admin"}


def must_secret(secret: str) -> bytes:
    if len(secret or "") < 32:
        raise RuntimeError("AGENT_RUNTIME_SECRET phải có tối thiểu 32 ký tự")
    return secret.encode("utf8")


def signature(secret: str, timestamp: int, method: str, path: str, data: bytes) -> str:
    payload = str(timestamp).encode() + b"\n" + method.upper().encode() + b"\n" + path.encode() + b"\n" + data
    return hmac.new(must_secret(secret), payload, hashlib.sha256).hexdigest()


def verify_request(secret: str, timestamp: str, signature_hex: str, method: str, path: str,
                   data: bytes, now: int | None = None) -> bool:
    try:
        ts = int(timestamp)
        valid = bool(re.fullmatch(r"[0-9a-f]{64}", signature_hex))
        clock = int(time.time() if now is None else now)
        return (valid and abs(clock - ts) <= 60 and
                hmac.compare_digest(signature(secret, ts, method, path, data), signature_hex))
    except (TypeError, ValueError, RuntimeError):
        return False


def validate_request(body: dict) -> dict:
    project = str(body.get("projectId") or "")
    task = str(body.get("taskId") or "")
    agent = str(body.get("agentId") or "")
    job_id = str(body.get("jobId") or "")
    mode = str(body.get("mode") or "")
    file_id = str(body.get("fileId") or "")
    identity = body.get("identity") or {}
    if (not GOOGLE_ID.fullmatch(project) or not HEX_ID.fullmatch(task)
        or not HEX_ID.fullmatch(job_id) or not AGENT_ID.fullmatch(agent)
        or mode not in MODES):
        raise ValueError("Nhiệm vụ/Agent/mã lượt chạy không hợp lệ")
    if mode in {"expert", "expert_llm"} and not GOOGLE_ID.fullmatch(file_id):
        raise ValueError("Phân tích chuyên gia cần file Google Drive hợp lệ")
    if file_id and not GOOGLE_ID.fullmatch(file_id):
        raise ValueError("File ID không hợp lệ")
    email = str(identity.get("email") or "").casefold()
    role = str(identity.get("role") or "")
    projects = identity.get("projects") or []
    if (not re.fullmatch(r"[^\s@]{1,64}@[^\s@]{1,253}", email)
        or role not in PERMITTED_ROLES or not isinstance(projects, list)
        or len(projects) > 200 or
        (role != "admin" and "*" not in projects and project not in projects)):
        raise PermissionError("Không có quyền phân tích trong dự án")
    if mode in {"llm", "expert_llm"} and body.get("consent") is not True:
        raise PermissionError("Cần xác nhận gửi trích xuất mẫu đến AI")
    note = str(body.get("note") or "")
    if len(note) > 700 or len(json.dumps(body, ensure_ascii=False)) > 6000:
        raise ValueError("Yêu cầu vượt giới hạn")
    return {
        "job_id": job_id, "project_id": project, "task_id": task,
        "agent_id": agent, "file_id": file_id, "mode": mode,
        "identity": {"email": email, "role": role, "projects": projects},
        "note": note, "consent": body.get("consent") is True,
        "estimated_usd": COST_ESTIMATE[mode],
    }
