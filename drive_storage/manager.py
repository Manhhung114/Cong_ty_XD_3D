"""Google Drive folder and upload service. NEVER import in the browser.

Only call after verifying the signed-in Google identity in the Streamlit server.
Credentials are loaded from Streamlit secrets (not stored in repository).
"""
from __future__ import annotations

import io
import mimetypes
import re
from pathlib import PurePath
from dataclasses import dataclass

ROOT_SUBDIR = "01_DU_AN"
FOLDER_CATEGORIES = {
    "info": ("01_THONG_TIN_DU_AN",),
    "drawings_mep": ("02_BAN_VE", "MEP"),
    "drawings_xd": ("02_BAN_VE", "XAY_DUNG"),
    "boq_mep": ("03_BOQ_DU_TOAN", "MEP"),
    "boq_xd": ("03_BOQ_DU_TOAN", "XAY_DUNG"),
    "bim_mep": ("04_BIM_MO_HINH", "MEP"),
    "bim_xd": ("04_BIM_MO_HINH", "XAY_DUNG"),
    "fire": ("05_PCCC",),
    "tasks": ("06_CONG_VIEC",),
    "approvals": ("07_PHE_DUYET",),
    "reports_mep": ("08_BAO_CAO", "MEP"),
    "reports_xd": ("08_BAO_CAO", "XAY_DUNG"),
    "reports_management": ("08_BAO_CAO", "BAN_DIEU_HANH"),
    "contracts": ("09_HOP_DONG",),
    "legal": ("10_PHAP_LY_DU_AN",),
    "schedule": ("11_TIEN_DO_THI_CONG",),
    "photos": ("12_HINH_ANH_HIEN_TRUONG",),
    "audit": ("13_NHAT_KY",),
}
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".doc", ".docx", ".dwg", ".dxf", ".ifc", ".rvt", ".nwd", ".png", ".jpg", ".jpeg", ".txt", ".json", ".zip"}
MAX_FILE_SIZE = 25 * 1024 * 1024
CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,49}$")


def validated_project_folder(code: str, name: str) -> str:
    code = code.strip().upper()
    if not CODE_PATTERN.fullmatch(code):
        raise ValueError("Mã dự án: 2–50 ký tự, chỉ chữ A–Z, số, dấu - và _")
    name = re.sub(r"[\\/\x00-\x1f]+", " ", name.strip())
    name = re.sub(r"\s+", "_", name).strip(" ._")
    if len(name) < 2 or len(name) > 80:
        raise ValueError("Tên dự án phải từ 2 đến 80 ký tự")
    if name.upper().startswith(code + "_"):
        return name
    return f"{code}_{name}"


def safe_filename(filename: str) -> str:
    name = re.sub(r"[\\/\x00-\x1f]+", "_", filename.strip())
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name or len(name) > 180 or PurePath(name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Tên tệp hoặc phần mở rộng không hợp lệ")
    return name


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


@dataclass
class DriveStorage:
    service: object
    root_id: str

    def __post_init__(self):
        if not re.fullmatch(r"[\w-]{12,160}", self.root_id or ""):
            raise ValueError("Cấu hình Drive root_folder_id không hợp lệ")

    def _folders_named(self, parent_id: str, folder_name: str) -> list[dict]:
        q = f"'{_quote(parent_id)}' in parents and name = '{_quote(folder_name)}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        items = []
        token = None
        while True:
            result = self.service.files().list(q=q,fields="nextPageToken,files(id,name,mimeType)",pageSize=100,pageToken=token).execute()
            items.extend(result.get("files", []))
            token = result.get("nextPageToken")
            if not token:
                return items

    def folder(self, parent_id: str, folder_name: str) -> str:
        found = self._folders_named(parent_id, folder_name)
        if len(found) > 1:
            raise RuntimeError("Phát hiện nhiều thư mục cùng tên. Cần kiểm tra trên Drive trước khi tải lên.")
        if found:
            return found[0]["id"]
        result = self.service.files().create(
            body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
            fields="id,name",
        ).execute()
        return result["id"]

    def project(self, code: str, project_name: str) -> str:
        projects = self.folder(self.root_id, ROOT_SUBDIR)
        return self.folder(projects, validated_project_folder(code, project_name))

    def destination(self, code: str, project_name: str, category: str) -> str:
        if category not in FOLDER_CATEGORIES:
            raise ValueError("Nhóm hồ sơ không hợp lệ")
        parent = self.project(code, project_name)
        for sub in FOLDER_CATEGORIES[category]:
            parent = self.folder(parent, sub)
        return parent

    def upload(self, *, code: str, project_name: str, category: str, filename: str, data: bytes) -> dict:
        if not data or len(data) > MAX_FILE_SIZE:
            raise ValueError("Tệp phải có dung lượng từ 1 byte đến 25 MB")
        original = safe_filename(filename)
        parent = self.destination(code, project_name, category)
        stem, ext = original[: -len(PurePath(original).suffix)], PurePath(original).suffix
        stem = re.sub(r"_R\d{2,4}$", "", stem, flags=re.I)
        # Never overwrite the previous approved revision. A new upload creates a new file.
        for revision in range(1, 1000):
            candidate = f"{stem}_R{revision:02d}{ext}"
            q = f"'{_quote(parent)}' in parents and name = '{_quote(candidate)}' and trashed = false"
            matches = self.service.files().list(q=q,fields="files(id)",pageSize=2).execute().get("files", [])
            if not matches:
                break
        else:
            raise RuntimeError("Đã đạt giới hạn phiên bản tệp")
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mimetypes.guess_type(candidate)[0] or "application/octet-stream",resumable=True)
        result = self.service.files().create(
            body={"name":candidate,"parents":[parent],"appProperties":{"projectCode":code.strip().upper(),"category":category,"originalName":original,"revision":str(revision)}},
            media_body=media,
            fields="id,name,mimeType,size,webViewLink,parents",
        ).execute()
        return result


def from_streamlit_secrets(config: dict) -> DriveStorage:
    required = ("root_folder_id", "client_id", "client_secret", "refresh_token")
    if any(not config.get(key) for key in required):
        raise RuntimeError("Thiếu Google Drive OAuth trong Streamlit Secrets")
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    credentials = Credentials(token=None,refresh_token=config["refresh_token"],client_id=config["client_id"],client_secret=config["client_secret"],token_uri="https://oauth2.googleapis.com/token",scopes=["https://www.googleapis.com/auth/drive"])
    return DriveStorage(build("drive", "v3", credentials=credentials, cache_discovery=False), config["root_folder_id"])
