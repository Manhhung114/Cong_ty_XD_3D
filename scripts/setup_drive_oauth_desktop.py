"""Run this on the owner's own computer to issue Google Drive refresh token.

The script DOES NOT send credentials to ChatGPT or GitHub. It writes a private
file on the local computer. The owner must paste the values directly into
Streamlit Cloud Secrets, then secure/delete the local file as appropriate.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Google Drive refresh token locally")
    parser.add_argument("--client-file", required=True,
                        help="Path to the Desktop OAuth client JSON downloaded from Google Cloud")
    parser.add_argument("--out", default="drive_oauth_private.txt",
                        help="Private output file (must not already exist)")
    args = parser.parse_args()
    credentials_file = Path(args.client_file).expanduser().resolve()
    output = Path(args.out).expanduser().resolve()
    if not credentials_file.is_file():
        parser.error("Không tìm thấy tệp OAuth Desktop JSON.")
    if output.exists():
        parser.error("Tệp đầu ra đã tồn tại. Không được ghi đè tệp chứa khóa.")

    from google_auth_oauthlib.flow import InstalledAppFlow
    credentials_json = json.loads(credentials_file.read_text(encoding="utf-8"))
    if "installed" not in credentials_json:
        parser.error("Hãy tải OAuth client loại Desktop app, không phải Web application.")
    client = credentials_json["installed"]
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes=SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    if not creds.refresh_token:
        raise RuntimeError("Không nhận được refresh_token. Kiểm tra prompt=consent và trạng thái OAuth.")

    payload = ("[drive]\n"
               f'client_id = {json.dumps(client["client_id"])}\n'
               f'client_secret = {json.dumps(client["client_secret"])}\n'
               f'refresh_token = {json.dumps(creds.refresh_token)}\n')
    fd = os.open(str(output), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(payload)
    try:
        output.chmod(0o600)
    except OSError:
        pass
    print("Đã lưu thông tin Drive OAuth vào tệp riêng trên máy tính:")
    print(str(output))
    print("KHÔNG tải tệp này lên GitHub, ChatGPT hoặc website công khai.")
    print("Copy các dòng [drive] vào Streamlit Secrets, cùng với root_folder_id và allowed_email.")


if __name__ == "__main__":
    main()
