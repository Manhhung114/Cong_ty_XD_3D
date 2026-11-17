"""V6.7.6: one Admin-owned, encrypted AI credential for all authorized Agents.

The credential is AES-256-GCM encrypted at rest in the configured Drive root.
The encryption key is derived exclusively on the Streamlit server from the
existing high-entropy auth.cookie_secret and root_folder_id. NEVER send the
plaintext, derived key or ciphertext to a browser or app backup.

Unlike localStorage, this survives browser changes and other logins. A
recovery requires restoring the original cookie_secret if it is rotated.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

VAULT_NAME = "_XD_MEP_AI_SHARED_CREDENTIALS_V676.json"
SCHEMA = "XD_MEP_SERVER_AI_V676"
MAX_BYTES = 16000
MAX_KEY = 500
PROVIDERS = {"openai", "gemini"}
MODEL_ID = re.compile(r"^[A-Za-z0-9._-]{3,100}$")


def _validate(provider: str, model: str, api_key: str,
              agent_models: dict | None = None) -> dict:
    provider = str(provider or "").strip().lower()
    model = str(model or "").strip()
    api_key = str(api_key or "").strip()
    if provider not in PROVIDERS:
        raise ValueError("Nhà cung cấp AI phải là OpenAI hoặc Google Gemini")
    if not MODEL_ID.fullmatch(model):
        raise ValueError("Mã model AI không hợp lệ (3–100 ký tự)")
    if not (12 <= len(api_key) <= MAX_KEY) or any(ord(c) < 33 for c in api_key):
        raise ValueError("API key không hợp lệ")
    from drive_storage.company_agents import agents
    catalog = agents()
    clean_models = {}
    for aid, item in (agent_models or {}).items():
        if aid not in catalog or not MODEL_ID.fullmatch(str(item)):
            raise ValueError("Cấu hình model Agent không hợp lệ")
        clean_models[aid] = str(item)
    return {
        "provider": provider, "model": model, "api_key": api_key,
        "agent_models": clean_models,
    }


def _key(secret: str, root_id: str) -> bytes:
    if not isinstance(secret, str) or len(secret) < 32:
        raise RuntimeError("Thiếu [auth].cookie_secret mạnh và ổn định (tối thiểu 32 ký tự)")
    return hashlib.sha256(
        b"XD_MEP_AI_VAULT_V676\0" + root_id.encode() + b"\0" + secret.encode()
    ).digest()


def _aad(root_id: str) -> bytes:
    return (SCHEMA + "\0" + root_id).encode()


def _candidates(storage) -> list[dict]:
    root = storage.root_id
    q = f"'{root}' in parents and name = '{VAULT_NAME}' and trashed = false"
    items = storage.service.files().list(
        q=q, fields="nextPageToken,files(id,name,parents,size,mimeType)",
        pageSize=3,
    ).execute()
    candidates = items.get("files", [])
    if items.get("nextPageToken") or len(candidates) > 1:
        raise RuntimeError("Phát hiện nhiều cấu hình AI dùng chung; dừng để bảo vệ khóa")
    for file in candidates:
        if (root not in file.get("parents", [])
                or file.get("name") != VAULT_NAME
                or file.get("mimeType") != "application/json"
                or int(file.get("size") or 0) > MAX_BYTES):
            raise PermissionError("Tệp cấu hình AI không thuộc thư mục quản lý hợp lệ")
    return candidates


def read_shared(storage, secret: str) -> tuple[str | None, dict | None]:
    """Returns an encrypted Drive document's ID and decrypted server config."""
    records = _candidates(storage)
    if not records:
        return None, None
    fid = records[0]["id"]
    raw = storage.service.files().get_media(fileId=fid).execute()
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise RuntimeError("Không đọc được kho cấu hình AI")
    try:
        wrapper = json.loads(raw.decode("utf8"))
        if wrapper.get("schema") != SCHEMA or wrapper.get("algorithm") != "AES-256-GCM":
            raise ValueError("Định dạng kho AI không hợp lệ")
        nonce = base64.b64decode(wrapper["nonce"], validate=True)
        cipher = base64.b64decode(wrapper["ciphertext"], validate=True)
        if len(nonce) != 12 or not (32 <= len(cipher) <= MAX_BYTES):
            raise ValueError("Dữ liệu mã hóa AI không hợp lệ")
        plain = AESGCM(_key(secret, storage.root_id)).decrypt(
            nonce, cipher, _aad(storage.root_id)
        )
        if len(plain) > MAX_BYTES:
            raise ValueError("Cấu hình AI vượt giới hạn")
        info = json.loads(plain.decode("utf8"))
        checked = _validate(info.get("provider"), info.get("model"),
                            info.get("api_key"), info.get("agent_models"))
        return fid, checked
    except (InvalidTag, UnicodeError, KeyError, TypeError, json.JSONDecodeError,
            ValueError) as exc:
        raise PermissionError(
            "Không giải mã được cấu hình AI trên Drive. Kiểm tra khóa bí mật "
            "của máy chủ; không ghi đè kho đã có."
        ) from exc


def save_shared(storage, secret: str, identity: dict, *,
                provider: str, model: str, api_key: str,
                agent_models: dict | None = None):
    from drive_storage.access_control import can_admin
    if not can_admin(identity):
        raise PermissionError("Chỉ Admin được lưu API dùng chung")
    checked = _validate(provider, model, api_key, agent_models)
    old_id, _ = read_shared(storage, secret)
    nonce = os.urandom(12)
    payload = json.dumps(checked, ensure_ascii=False, separators=(",", ":")).encode("utf8")
    cipher = AESGCM(_key(secret, storage.root_id)).encrypt(
        nonce, payload, _aad(storage.root_id)
    )
    wrapper = {
        "schema": SCHEMA, "algorithm": "AES-256-GCM",
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(cipher).decode(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    encoded = json.dumps(wrapper, separators=(",", ":")).encode("utf8")
    if len(encoded) > MAX_BYTES:
        raise ValueError("Cấu hình AI quá lớn")
    from googleapiclient.http import MediaIoBaseUpload
    media = MediaIoBaseUpload(io.BytesIO(encoded), mimetype="application/json",
                             resumable=False)
    if old_id:
        result = storage.service.files().update(
            fileId=old_id, media_body=media, fields="id,name,parents"
        ).execute()
    else:
        if _candidates(storage):
            raise RuntimeError("Cấu hình AI đã tạo ở phiên khác; vui lòng mở lại")
        result = storage.service.files().create(
            body={"name": VAULT_NAME, "parents": [storage.root_id],
                  "mimeType": "application/json",
                  "description": "Encrypted server-only shared AI credential"},
            media_body=media, fields="id,name,parents",
        ).execute()
    if (storage.root_id not in result.get("parents", [])
            or result.get("name") != VAULT_NAME):
        raise RuntimeError("Drive không xác nhận đã lưu API vào đúng vị trí")
    return result["id"]


def revoke_shared(storage, identity: dict):
    from drive_storage.access_control import can_admin
    if not can_admin(identity):
        raise PermissionError("Chỉ Admin được thu hồi khóa AI")
    records = _candidates(storage)
    if records:
        storage.service.files().delete(fileId=records[0]["id"]).execute()


def effective_config(st, agent_id: str = "") -> dict:
    """Server-only per-request resolution. Shared config wins over legacy Secrets.

    A corrupted shared record FAILS CLOSED, not silently fallback to Secrets.
    """
    from drive_storage.manager import from_streamlit_secrets
    drive = dict(st.secrets.get("drive", {}))
    secret = str(st.secrets.get("auth", {}).get("cookie_secret", ""))
    required = ("root_folder_id", "refresh_token", "client_id", "client_secret")
    if all(drive.get(field) for field in required):
        storage = from_streamlit_secrets(drive)
        _, common = read_shared(storage, secret)
    else:
        common = None
    if common is not None:
        config = dict(common)
        if agent_id:
            config["model"] = common.get("agent_models", {}).get(
                agent_id, common["model"]
            )
        return config
    # Backward-compatible existing server Secrets, never browser localStorage.
    config = dict(st.secrets.get("ai", {}))
    if agent_id and isinstance(config.get("agent_models"), dict):
        config["model"] = config["agent_models"].get(agent_id, config.get("model"))
    return config


def safe_status(st) -> dict:
    """Metadata only; zero credential bytes included in the browser snapshot."""
    from drive_storage.manager import from_streamlit_secrets
    drive = dict(st.secrets.get("drive", {}))
    required = ("root_folder_id", "refresh_token", "client_id", "client_secret")
    if all(drive.get(field) for field in required):
        storage = from_streamlit_secrets(drive)
        secret = str(st.secrets.get("auth", {}).get("cookie_secret", ""))
        _, common = read_shared(storage, secret)
    else:
        common = None
    source = "drive_encrypted" if common else "streamlit_secrets"
    config = common if common is not None else dict(st.secrets.get("ai", {}))
    provider = str(config.get("provider") or "").lower()
    model = str(config.get("model") or "")
    configured = provider in PROVIDERS and bool(config.get("api_key")) and bool(
        MODEL_ID.fullmatch(model)
    )
    return {
        "configured": configured,
        "provider": provider if configured else "none",
        "model": model[:100] if configured else "",
        "source": source if configured else "none",
        "shared": bool(common),
        "mode": "server_only",
    }
