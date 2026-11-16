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
MAX_FILE_SIZE = 500 * 1024 * 1024
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

    def _child_projects(self, projects_id: str) -> list[dict]:
        """List direct project folders, paging through all entries."""
        query = (f"'{_quote(projects_id)}' in parents and "
                 "mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        items, token = [], None
        while True:
            response = self.service.files().list(
                q=query, fields="nextPageToken,files(id,name,appProperties)",
                pageSize=100, pageToken=token,
            ).execute()
            items.extend(response.get("files", []))
            token = response.get("nextPageToken")
            if not token:
                return items

    def list_projects(self) -> list[dict]:
        """Only projects directly inside this app's configured Drive root."""
        projects = self.folder(self.root_id, ROOT_SUBDIR)
        return sorted(self._child_projects(projects), key=lambda f: f["name"].casefold())

    def project(self, code: str, project_name: str) -> str:
        expected = validated_project_folder(code, project_name)
        normalized_code = code.strip().upper()
        projects = self.folder(self.root_id, ROOT_SUBDIR)
        children = self._child_projects(projects)
        # Match project names case-insensitively to avoid parallel folders like
        # S234_SUNSHINE_SKY_CITY versus S234_Sunshine_Sky_City.
        matches = [x for x in children if x["name"].casefold() == expected.casefold()]
        if len(matches) != 1 and matches:
            raise RuntimeError("Có nhiều thư mục dự án trùng tên. Kiểm tra Google Drive trước khi tiếp tục.")
        if matches:
            return matches[0]["id"]
        # Same code with another name is an unsafe collision: never mix projects.
        collisions = [x for x in children if (
            str((x.get("appProperties") or {}).get("projectCode", "")).upper() == normalized_code
            or x["name"].upper().startswith(normalized_code + "_")
        )]
        if collisions:
            raise ValueError("Mã dự án đã có thư mục khác trên Drive. Hãy chọn dự án hiện có thay vì tạo bản trùng.")
        return self.folder(projects, expected)

    def ensure_project_tree(self, code: str, project_name: str) -> str:
        """Create the complete 13-category tree once; idempotent on repeated calls."""
        project_id = self.project(code, project_name)
        for category_path in sorted(set(FOLDER_CATEGORIES.values())):
            parent = project_id
            for sub in category_path:
                parent = self.folder(parent, sub)
        return project_id

    def project_by_id(self, project_id: str) -> dict:
        """Resolve only direct child folders; never accept arbitrary Drive IDs."""
        if not re.fullmatch(r"[\w-]{12,160}", project_id or ""):
            raise ValueError("ID dự án không hợp lệ")
        projects = self.list_projects()
        matches = [p for p in projects if p["id"] == project_id]
        if len(matches) != 1:
            raise ValueError("Dự án không thuộc thư mục gốc của ứng dụng")
        return matches[0]

    def destination_by_id(self, project_id: str, category: str) -> str:
        if category not in FOLDER_CATEGORIES:
            raise ValueError("Nhóm hồ sơ không hợp lệ")
        parent = self.project_by_id(project_id)["id"]
        for sub in FOLDER_CATEGORIES[category]:
            parent = self.folder(parent, sub)
        return parent

    def destination(self, code: str, project_name: str, category: str) -> str:
        if category not in FOLDER_CATEGORIES:
            raise ValueError("Nhóm hồ sơ không hợp lệ")
        parent = self.project(code, project_name)
        for sub in FOLDER_CATEGORIES[category]:
            parent = self.folder(parent, sub)
        return parent

    def verify_connection(self) -> dict:
        """Confirm this OAuth identity can access the configured Drive root."""
        profile = self.service.about().get(fields="user(emailAddress)").execute()
        folder = self.service.files().get(
            fileId=self.root_id,
            fields="id,name,mimeType,trashed,capabilities(canAddChildren)",
        ).execute()
        if (folder.get("mimeType") != "application/vnd.google-apps.folder"
                or folder.get("trashed")):
            raise PermissionError("Thư mục gốc Google Drive không hợp lệ hoặc đã bị xóa")
        if folder.get("capabilities", {}).get("canAddChildren") is False:
            raise PermissionError("Tài khoản Drive không có quyền thêm tệp vào thư mục gốc")
        return {"email": profile.get("user", {}).get("emailAddress", ""),
                "root_name": folder.get("name", ""), "root_id": folder["id"]}

    def _upload_to_parent(self, *, parent: str, project_code: str,
                          category: str, filename: str, data: bytes) -> dict:
        if not data or len(data) > MAX_FILE_SIZE:
            raise ValueError("Tệp phải có dung lượng từ 1 byte đến 500 MB")
        original = safe_filename(filename)
        extension = PurePath(original).suffix
        stem = original[:-len(extension)]
        stem = re.sub(r"_R\d{2,4}$", "", stem, flags=re.I)
        for revision in range(1, 1000):
            candidate = f"{stem}_R{revision:02d}{extension}"
            query = (f"'{_quote(parent)}' in parents and "
                     f"name = '{_quote(candidate)}' and trashed = false")
            matches = self.service.files().list(q=query, fields="files(id)", pageSize=2).execute().get("files", [])
            if not matches:
                break
        else:
            raise RuntimeError("Đã đạt giới hạn phiên bản tệp")
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(io.BytesIO(data),
                                  mimetype=mimetypes.guess_type(candidate)[0] or "application/octet-stream",
                                  resumable=True)
        result = self.service.files().create(
            body={"name": candidate, "parents": [parent], "appProperties": {
                "projectCode": project_code, "category": category,
                "originalName": original, "revision": str(revision),
            }},
            media_body=media,
            fields="id,name,mimeType,size,webViewLink,parents",
        ).execute()
        if parent not in result.get("parents", []):
            raise RuntimeError("Drive trả về vị trí lưu không khớp. Cần kiểm tra tệp vừa tải lên.")
        return result

    def upload(self, *, code: str, project_name: str, category: str,
               filename: str, data: bytes) -> dict:
        parent = self.destination(code, project_name, category)
        return self._upload_to_parent(parent=parent, project_code=code.strip().upper(),
                                      category=category, filename=filename, data=data)

    def upload_to_project(self, *, project_id: str, category: str,
                          filename: str, data: bytes) -> dict:
        record = self.project_by_id(project_id)
        parent = self.destination_by_id(project_id, category)
        code = (record.get("appProperties") or {}).get("projectCode") or record["name"].split("_", 1)[0]
        return self._upload_to_parent(parent=parent, project_code=code.upper(),
                                      category=category, filename=filename, data=data)


    def list_category_files(self, *, project_id: str, category: str) -> list[dict]:
        """List only regular files in a verified project/category folder."""
        parent = self.destination_by_id(project_id, category)
        q = (f"'{_quote(parent)}' in parents and trashed = false "
             "and mimeType != 'application/vnd.google-apps.folder'")
        items, token = [], None
        while True:
            response = self.service.files().list(
                q=q, fields="nextPageToken,files(id,name,size,mimeType,modifiedTime,webViewLink,webContentLink,parents)",
                pageSize=100, pageToken=token,
            ).execute()
            items.extend(x for x in response.get("files", []) if parent in x.get("parents", [parent]))
            token = response.get("nextPageToken")
            if not token:
                return sorted(items, key=lambda f: f.get("modifiedTime", ""), reverse=True)

    def upload_stream_to_project(self, *, project_id: str, category: str,
                                 filename: str, stream, size: int,
                                 progress=None) -> dict:
        """Resumable 8 MiB-chunk Drive upload, avoiding a second in-memory 500 MB copy."""
        if not isinstance(size, int) or not 0 < size <= MAX_FILE_SIZE:
            raise ValueError("Tệp phải có dung lượng từ 1 byte đến 500 MB")
        original = safe_filename(filename)
        record = self.project_by_id(project_id)
        parent = self.destination_by_id(project_id, category)
        extension = PurePath(original).suffix
        stem = re.sub(r"_R\d{2,4}$", "", original[:-len(extension)], flags=re.I)
        for revision in range(1, 1000):
            name = f"{stem}_R{revision:02d}{extension}"
            q = (f"'{_quote(parent)}' in parents and "
                 f"name = '{_quote(name)}' and trashed = false")
            matches = self.service.files().list(
                q=q, fields="files(id)", pageSize=2,
            ).execute().get("files", [])
            if not matches:
                break
        else:
            raise RuntimeError("Đã đạt giới hạn phiên bản tệp")
        from googleapiclient.http import MediaIoBaseUpload
        stream.seek(0)
        media = MediaIoBaseUpload(
            stream,
            mimetype=mimetypes.guess_type(name)[0] or "application/octet-stream",
            chunksize=8 * 1024 * 1024,
            resumable=True,
        )
        code = ((record.get("appProperties") or {}).get("projectCode")
                or record["name"].split("_", 1)[0]).upper()
        request = self.service.files().create(
            body={"name": name, "parents": [parent], "appProperties": {
                "projectCode": code, "category": category,
                "originalName": original, "revision": str(revision),
            }},
            media_body=media,
            fields="id,name,mimeType,size,webViewLink,parents",
        )
        result = None
        while result is None:
            status, result = request.next_chunk(num_retries=3)
            if status is not None and progress is not None:
                progress(min(1.0, float(status.progress())))
        if parent not in result.get("parents", []):
            raise RuntimeError("Drive trả về vị trí lưu không khớp")
        if progress is not None:
            progress(1.0)
        return result

    def download_small_file(self, *, project_id: str, category: str,
                            file_id: str, max_bytes: int = 40 * 1024 * 1024) -> bytes:
        """Server download only after validating the requested file belongs to the category."""
        if not re.fullmatch(r"[\w-]{12,160}", file_id or ""):
            raise ValueError("ID tệp không hợp lệ")
        files = self.list_category_files(project_id=project_id, category=category)
        matches = [f for f in files if f["id"] == file_id]
        if len(matches) != 1:
            raise PermissionError("Tệp không thuộc dự án và mục hồ sơ đã chọn")
        size = int(matches[0].get("size") or 0)
        if size > max_bytes:
            raise ValueError("Tệp lớn: hãy dùng liên kết mở Google Drive để tải trực tiếp")
        from googleapiclient.http import MediaIoBaseDownload
        output = io.BytesIO()
        downloader = MediaIoBaseDownload(
            output,
            self.service.files().get_media(fileId=file_id),
            chunksize=8 * 1024 * 1024,
        )
        done = False
        while not done:
            _, done = downloader.next_chunk(num_retries=3)
            if output.tell() > max_bytes:
                raise ValueError("Tệp vượt giới hạn tải qua trình duyệt")
        return output.getvalue()


def from_streamlit_secrets(config: dict) -> DriveStorage:
    required = ("root_folder_id", "client_id", "client_secret", "refresh_token")
    if any(not config.get(key) for key in required):
        raise RuntimeError("Thiếu Google Drive OAuth trong Streamlit Secrets")
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    credentials = Credentials(token=None,refresh_token=config["refresh_token"],client_id=config["client_id"],client_secret=config["client_secret"],token_uri="https://oauth2.googleapis.com/token",scopes=["https://www.googleapis.com/auth/drive"])
    return DriveStorage(build("drive", "v3", credentials=credentials, cache_discovery=False), config["root_folder_id"])
