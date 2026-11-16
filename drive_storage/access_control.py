"""Google-OIDC access control backed by a server-side Google Drive manifest.

Inspired by QLDA's Admin/Update/Read roles, but no second password database.
Google Drive credentials and role policy never enter the embedded 3D frontend.
"""
from __future__ import annotations

import io
import json
import re
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Any

POLICY_NAME = "_XD_MEP_ACCESS_ROLES_V1.json"
MAX_POLICY_BYTES = 256 * 1024
ROLES = ("read", "update", "admin")
ROLE_NAMES = {"read": "Chỉ đọc", "update": "Cập nhật", "admin": "Admin"}
EMAIL_PATTERN = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,253}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{12,160}$")


def clean_email(value: Any) -> str:
    email = str(value or "").strip().casefold()
    if not EMAIL_PATTERN.fullmatch(email) or len(email) > 254:
        raise ValueError("Email người dùng không hợp lệ")
    return email


def empty_policy() -> dict:
    return {"version": 1, "users": {}, "audit": []}


def validate_policy(data: Any) -> dict:
    """Never silently interpret corrupted/mismatched policy as an empty allowlist."""
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Định dạng phân quyền trên Drive không hợp lệ")
    source = data.get("users")
    if not isinstance(source, dict) or len(source) > 500:
        raise ValueError("Danh sách người dùng không hợp lệ")
    users = {}
    for email, row in source.items():
        normalized = clean_email(email)
        if normalized in users or not isinstance(row, dict):
            raise ValueError("Tài khoản trùng hoặc dữ liệu người dùng lỗi")
        role = str(row.get("role") or "")
        if role not in ROLES:
            raise ValueError("Vai trò người dùng không hợp lệ")
        projects = row.get("projects", ["*"])
        if not isinstance(projects, list) or len(projects) > 200 or any(
            not isinstance(p, str) or (p != "*" and not ID_PATTERN.fullmatch(p)) for p in projects
        ):
            raise ValueError("Phạm vi dự án không hợp lệ")
        users[normalized] = {
            "name": str(row.get("name") or "")[:160],
            "role": role,
            "active": row.get("active", True) is True,
            "projects": ["*"] if "*" in projects else list(dict.fromkeys(projects)),
            "updated_at": str(row.get("updated_at") or "")[:48],
        }
    audit = data.get("audit", [])
    if not isinstance(audit, list):
        raise ValueError("Nhật ký phân quyền không hợp lệ")
    return {"version": 1, "users": users, "audit": audit[-100:]}


def _policy_candidates(storage) -> list:
    rid = storage.root_id
    q = f"'{rid}' in parents and name = '{POLICY_NAME}' and trashed = false"
    found = storage.service.files().list(
        q=q, fields="nextPageToken,files(id,name,parents,mimeType,size)",
        pageSize=100,
    ).execute()
    if found.get("nextPageToken"):
        raise RuntimeError("Nhiều tệp phân quyền: cần Admin kiểm tra trên Drive")
    records = [
        x for x in found.get("files", [])
        if x.get("name") == POLICY_NAME
        and rid in x.get("parents", [])
        and x.get("mimeType") == "application/json"
    ]
    if len(records) != len(found.get("files", [])) or len(records) > 1:
        raise RuntimeError("Phát hiện cấu hình phân quyền không nhất quán")
    return records


def _signature(payload: dict, secret: str) -> str:
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("Thiếu khóa xác thực phân quyền của máy chủ")
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def read_policy(storage, secret: str = "") -> tuple[str | None, dict | None]:
    """None policy means not initialized; transport/corrupt-file errors are fatal."""
    entries = _policy_candidates(storage)
    if not entries:
        return None, None
    rec = entries[0]
    if int(rec.get("size") or 0) > MAX_POLICY_BYTES:
        raise ValueError("File phân quyền vượt giới hạn")
    raw = storage.service.files().get_media(fileId=rec["id"]).execute()
    if not isinstance(raw, bytes) or len(raw) > MAX_POLICY_BYTES:
        raise ValueError("Không đọc được dữ liệu phân quyền")
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Chính sách phân quyền không hợp lệ")
    supplied = str(data.pop("_signature", ""))
    checked = validate_policy(data)
    if not supplied or not hmac.compare_digest(supplied, _signature(checked, secret)):
        raise PermissionError("Chữ ký chính sách phân quyền không hợp lệ")
    return rec["id"], checked


def legacy_policy(members: Any) -> dict:
    """One-time import of older [access].members when the Drive file is absent."""
    policy = empty_policy()
    if isinstance(members, (list, tuple)):
        for item in members:
            try:
                email = clean_email(item)
            except ValueError:
                continue
            policy["users"][email] = {
                "name": "", "role": "update", "active": True,
                "projects": ["*"], "updated_at": "",
            }
    return policy


def write_policy(storage, policy: dict, existing_id: str | None, secret: str = "") -> str:
    """Write only the role manifest, not any OAuth credential or document."""
    checked = validate_policy(policy)
    signed = {**checked, "_signature": _signature(checked, secret)}
    payload = json.dumps(signed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_POLICY_BYTES:
        raise ValueError("Danh sách quyền quá lớn")
    from googleapiclient.http import MediaIoBaseUpload

    media = MediaIoBaseUpload(io.BytesIO(payload), mimetype="application/json", resumable=False)
    if existing_id:
        # Check the ID belongs to our configured Drive root before replacing it.
        known = _policy_candidates(storage)
        if len(known) != 1 or known[0]["id"] != existing_id:
            raise PermissionError("Tệp phân quyền đã đổi, vui lòng tải lại")
        result = storage.service.files().update(
            fileId=existing_id, media_body=media, fields="id,name,parents"
        ).execute()
    else:
        if _policy_candidates(storage):
            raise RuntimeError("Phân quyền đã được tạo ở một phiên khác, tải lại trước khi lưu")
        result = storage.service.files().create(
            body={
                "name": POLICY_NAME,
                "mimeType": "application/json",
                "parents": [storage.root_id],
                "description": "XD MEP server-managed application permissions",
            },
            media_body=media, fields="id,name,parents"
        ).execute()
    if storage.root_id not in result.get("parents", []):
        raise RuntimeError("Lưu phân quyền vào thư mục gốc không thành công")
    return str(result["id"])


def set_user(policy: dict, *, email: str, name: str, role: str,
             projects: list[str], active: bool, actor: str, owner: str) -> dict:
    email, owner, actor = clean_email(email), clean_email(owner), clean_email(actor)
    if email == owner:
        raise PermissionError("Tài khoản Admin gốc được bảo vệ bằng Streamlit Secrets")
    if role not in ROLES:
        raise ValueError("Quyền hệ thống không hợp lệ")
    if not isinstance(projects, list):
        raise ValueError("Phạm vi dự án không hợp lệ")
    if email == actor and (role != "admin" or active is not True):
        raise PermissionError("Admin không được tự hạ quyền hoặc tự khóa tài khoản")
    copied = validate_policy(policy)
    copied["users"][email] = {
        "name": str(name or "").strip()[:160],
        "role": role,
        "active": active is True,
        "projects": ["*"] if "*" in projects else list(dict.fromkeys(projects)),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    copied = validate_policy(copied)
    copied["audit"].append({"actor": actor, "target": email, "action": "upsert",
                            "role": role, "at": datetime.now(timezone.utc).isoformat()})
    copied["audit"] = copied["audit"][-100:]
    return copied


def revoke_user(policy: dict, *, email: str, actor: str, owner: str) -> dict:
    email, owner, actor = clean_email(email), clean_email(owner), clean_email(actor)
    if email == owner or email == actor:
        raise PermissionError("Không thể xóa Admin gốc hoặc tự thu hồi quyền")
    copied = validate_policy(policy)
    if email not in copied["users"]:
        raise ValueError("Không tìm thấy người dùng")
    del copied["users"][email]
    copied["audit"].append({"actor": actor, "target": email, "action": "revoke",
                            "at": datetime.now(timezone.utc).isoformat()})
    copied["audit"] = copied["audit"][-100:]
    return copied


def verified_email(st) -> str:
    if not getattr(st.user, "is_logged_in", False):
        return ""
    if st.user.get("email_verified") is not True:
        return ""
    try:
        return clean_email(st.user.get("email", ""))
    except ValueError:
        return ""


def identity_for(st) -> dict | None:
    """Fail closed for nonowners when Drive policy is unreadable.

    Owner identity is grounded in the existing verified Google OIDC allowlist.
    Legacy Secrets members work only until a managed Drive policy exists.
    """
    email = verified_email(st)
    try:
        drive_cfg = dict(st.secrets.get("drive", {}))
        owner = clean_email(drive_cfg.get("allowed_email"))
        members = st.secrets.get("access", {}).get("members", [])
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    if not email:
        return None
    if email == owner:
        return {"email": email, "role": "admin", "name": "Chủ hệ thống",
                "projects": ["*"], "active": True}

    required = ("root_folder_id", "client_id", "client_secret", "refresh_token")
    if all(drive_cfg.get(k) for k in required):
        try:
            from drive_storage.manager import from_streamlit_secrets
            storage = from_streamlit_secrets(drive_cfg)
            secret = str(st.secrets.get("auth", {}).get("cookie_secret", ""))
            _, saved = read_policy(storage, secret)
        except Exception:
            return None
        policy = saved if saved is not None else legacy_policy(members)
    else:
        # Compatibility path for tests or installations lacking Drive.
        # It never grants roles outside the already configured Secrets allowlist.
        policy = legacy_policy(members)

    record = policy["users"].get(email)
    if not record or not record["active"]:
        return None
    return {"email": email, **record}


def allows_project(identity: dict | None, project_id: str) -> bool:
    if not identity:
        return False
    return identity.get("role") == "admin" or "*" in identity.get("projects", []) or project_id in identity.get("projects", [])


def can_upload(identity: dict | None) -> bool:
    return bool(identity and identity.get("role") in {"update", "admin"})


def can_admin(identity: dict | None) -> bool:
    return bool(identity and identity.get("role") == "admin")
