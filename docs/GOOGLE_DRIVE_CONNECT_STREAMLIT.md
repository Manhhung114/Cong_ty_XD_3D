# Cấu hình tải tệp Google Drive – Công ty XD & MEP AI 3D

## Trạng thái
- Đã tạo thư mục gốc thật trên tài khoản Google Drive của chủ sở hữu:
  `https://drive.google.com/drive/folders/1gg32nE2pXd8veKp1YC9njdId0l0q2xas`
- Dự án `S234_SUNSHINE_SKY_CITY` đã có 13 nhóm hồ sơ:
  `https://drive.google.com/drive/folders/14zdIcUORsXh3bX8CfT9-MBi4RX91YKJk`
- Mã web hỗ trợ: **kho Drive trên trang chính** (không phải thanh sidebar ẩn), đăng nhập
  quản trị Google, chọn dự án, chọn loại hồ sơ, tải tệp và tạo revision `_R01`, `_R02`.
- Google Drive kết nối với ChatGPT **không tự cấp token cho Streamlit**.

## A. Chuẩn bị Google Cloud (thực hiện một lần)
1. Mở https://console.cloud.google.com/ và chọn/tạo dự án `XD_MEP_3D`.
2. APIs & Services → Library → bật **Google Drive API**.
3. Google Auth Platform → Branding / Audience / Data Access: cấu hình OAuth consent screen,
   thêm tài khoản của chủ Drive vào **Test users** nếu trạng thái đang Testing.
4. Google Auth Platform → Clients → Create Client → loại **Web application**.
   Tại Authorized redirect URIs nhập chính xác:
   `https://congtyxd.streamlit.app/oauth2callback`
   Lưu riêng Web Client ID và Web Client secret để cấu hình `[auth]`.
5. Create Client lần hai → **Desktop app** để cấp quyền cho dịch vụ Drive.
   Tải JSON client về **máy tính cá nhân**, không đưa lên GitHub/ChatGPT.

## B. Tạo Drive refresh_token trên máy Windows có trình duyệt
Cài Python 3.11+; trong thư mục mã nguồn dự án chạy:

```powershell
py -m pip install google-auth-oauthlib
py scripts/setup_drive_oauth_desktop.py --client-file "C:\\duong_dan\\client_secret_desktop.json" --out "C:\\duong_dan_rieng\\drive_oauth_private.txt"
```

Đăng nhập đúng **Google Drive chủ sở hữu** trong cửa sổ Google do trình duyệt mở,
đồng ý quyền quản lý Drive, sau đó đọc tệp `drive_oauth_private.txt` trên máy của anh.
Nội dung chứa `client_id`, `client_secret`, `refresh_token` thuộc `[drive]`.
Không gửi khóa/tệp này qua chat.

## C. Điền Streamlit Cloud Secrets
Vào https://share.streamlit.io/ → ứng dụng `congtyxd` → Manage app → Settings → Secrets.
Tạo nội dung sau; thay mọi chuỗi PLACEHOLDER bằng giá trị thật (KHÔNG commit GitHub):

```toml
[auth]
redirect_uri = "https://congtyxd.streamlit.app/oauth2callback"
cookie_secret = "GENERATE_RANDOM_SECRET_32_CHARACTERS_OR_LONGER"
client_id = "YOUR_GOOGLE_WEB_CLIENT_ID"
client_secret = "YOUR_GOOGLE_WEB_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[drive]
allowed_email = "YOUR_GOOGLE_DRIVE_ADMIN_EMAIL"
root_folder_id = "1gg32nE2pXd8veKp1YC9njdId0l0q2xas"
client_id = "YOUR_GOOGLE_DESKTOP_CLIENT_ID"
client_secret = "YOUR_GOOGLE_DESKTOP_CLIENT_SECRET"
refresh_token = "YOUR_GOOGLE_DRIVE_REFRESH_TOKEN"
```

Để tạo `cookie_secret` an toàn trên máy tính:
`py -c "import secrets; print(secrets.token_urlsafe(48))"`

**Lưu ý:** `[auth]` dùng Web OAuth client để xác thực tài khoản đăng nhập website;
`[drive]` dùng Desktop OAuth client để tải tệp bằng quyền Google Drive của chính tài khoản đó.

## D. Nghiệm thu
1. Save Secrets, **Reboot** ứng dụng Streamlit rồi mở `https://congtyxd.streamlit.app/`.
2. Trên đầu trang, mở **Google Drive · Kho hồ sơ dự án**.
3. **Đăng nhập với Google**, sử dụng email được phép trong `allowed_email`.
4. **Kiểm tra kết nối Drive**: phải hiện thư mục `CONG_TY_XD_MEP_AI_3D`.
5. Chọn dự án `S234_SUNSHINE_SKY_CITY`, mục `02_BAN_VE / MEP`.
6. Tải một PDF thử không nhạy cảm, xác nhận có tên `_R01.pdf` tại đúng thư mục.
7. Tải lại cùng tên tệp: phải có `_R02.pdf`; tệp R01 vẫn còn.
8. Thử đăng nhập bằng tài khoản Google khác: không được phép tải lên.
9. Tạo một dự án mới và kiểm tra tạo đủ các thư mục trong dự án đó.

## Lưu ý quan trọng
- Trước khi cài OAuth, website Streamlit vẫn chưa thể upload Drive, dù thư mục đã tồn tại.
- Website đang công khai: **chỉ quản trị viên đã đăng nhập** có quyền upload.
- `st.login` dùng Google OIDC; không dùng mật khẩu Google trực tiếp.
- Scope Drive hiện là `https://www.googleapis.com/auth/drive` (quyền rộng). Chỉ cấp
  cho chủ tài khoản tin cậy; khi dùng nhiều nhân sự cần backend và quyền chia sẻ hạn chế hơn.
- Nếu ứng dụng OAuth loại External còn **Testing**, refresh token cấp phạm vi Drive
  có thể hết hạn sau 7 ngày. Khi cần vận hành lâu dài phải xem xét xuất bản OAuth và
  yêu cầu xác minh Google tương ứng.
- Không tải hồ sơ khách hàng bí mật lên web chưa được kiểm thử bảo mật đầy đủ.
- Dữ liệu `localStorage`/`IndexedDB` trong iframe **không tự đồng bộ** lên Google Drive.
  Mục tải lên chỉ chuyển tệp do quản trị chọn bằng nút Streamlit.
- Không xóa dữ liệu cũ/khóa ký APK hoặc gỡ app điện thoại chỉ để thiết lập Drive.

## Tài liệu chính thức
- https://docs.streamlit.io/develop/tutorials/authentication/google
- https://docs.streamlit.io/develop/api-reference/user/st.login
- https://developers.google.com/workspace/drive/api/quickstart/python
- https://developers.google.com/identity/protocols/oauth2
