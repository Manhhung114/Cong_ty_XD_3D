# Google Drive – lưu hồ sơ theo dự án và theo sheet

## Cấu trúc Drive đã tạo (16/11/2026)

Thư mục gốc: `CONG_TY_XD_MEP_AI_3D`. Bên trong:

- `00_DUNG_CHUNG/01_PHAP_LUAT_TCVN_QCVN`, `02_MAU_BIEU_HO_SO`, `03_QUAN_TRI_NOI_BO`.
- `01_DU_AN/<MA_DU_AN>_<TEN_DU_AN>/` – mỗi dự án một thư mục.
- `99_SAO_LUU/01_BACKUP_DU_AN`, `02_BACKUP_DANH_MUC`.

Mỗi dự án có `01_THONG_TIN_DU_AN`, `02_BAN_VE`, `03_BOQ_DU_TOAN`, `04_BIM_MO_HINH`, `05_PCCC`, `06_CONG_VIEC`, `07_PHE_DUYET`, `08_BAO_CAO`, `09_HOP_DONG`, `10_PHAP_LY_DU_AN`, `11_TIEN_DO_THI_CONG`, `12_HINH_ANH_HIEN_TRUONG`, `13_NHAT_KY`.

Các thư mục BẢN VẼ / BOQ / BIM / BÁO CÁO được chia MEP và XÂY DỰNG; báo cáo còn có Ban Điều hành. Những thư mục mới được tạo đúng dự án khi tải tệp, không lẫn qua dự án khác.

## Trạng thái tích hợp

- Thư mục đã **được tạo thật** qua tài khoản Google Drive kết nối với ChatGPT.
- Phần mềm `drive_storage/` và giao diện quản trị Streamlit đã có code chuẩn bị.
- **Chưa tự động kết nối** trình duyệt Streamlit với Google Drive. Kết nối ChatGPT Google Drive không cung cấp OAuth token cho app công khai.
- Để bật chức năng tải lên từ Streamlit, phải cấu hình Google OpenID Connect và Drive OAuth theo hướng dẫn dưới đây.
- Khi chưa có bí mật `auth` và `drive`, giao diện quản trị Google Drive được ẩn và ứng dụng gốc vẫn hoạt động bình thường.

## Kích hoạt an toàn trên Streamlit Community Cloud

1. Google Cloud Console: tạo hoặc chọn project, bật **Google Drive API**. Thiết lập OAuth consent screen cho tài khoản quản trị, tạo OAuth client cho web OIDC Streamlit và một OAuth client Desktop để cấp refresh token cho Drive. Nếu app đang ở chế độ Testing, refresh token có thể hết hạn sớm; cần quản lý chu kỳ gia hạn.
2. Dùng công cụ OAuth Desktop của Google với scope `https://www.googleapis.com/auth/drive`, lấy một lần `refresh_token` cho tài khoản chủ sở hữu Drive. Phải lấy từ quy trình đồng ý chính thức, không dùng mật khẩu Google, không gửi token cho người khác.
3. Streamlit Cloud → App → Settings → Secrets; nhập các giá trị theo mẫu bên dưới, thay toàn bộ placeholder bằng dữ liệu thật. **Không commit thông tin bí mật lên GitHub**.
4. Reboot Streamlit; đăng nhập đúng tài khoản email được phép; sidebar xuất hiện **Google Drive · Kho hồ sơ**. Chọn mã/tên dự án, nhóm hồ sơ và tệp tải lên. Mỗi lần tải tạo revision `_R01`, `_R02`… mới, không ghi đè file gốc.
5. Thử với một PDF không nhạy cảm; kiểm tra tệp xuất hiện trong thư mục đúng dự án và bộ môn.

```toml
[auth]
redirect_uri = "https://<ten-app>.streamlit.app/oauth2callback"
cookie_secret = "<chuoi_ngau_nhien_it_nhat_32_ky_tu>"
client_id = "<google_oidc_client_id>"
client_secret = "<google_oidc_client_secret>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[drive]
allowed_email = "<tai_khoan_quan_tri>@gmail.com"
root_folder_id = "<id_thu_muc_CONG_TY_XD_MEP_AI_3D>"
client_id = "<google_drive_oauth_desktop_client_id>"
client_secret = "<google_drive_oauth_desktop_client_secret>"
refresh_token = "<refresh_token_drive_khong_chia_se>"
```

## Quy tắc bảo mật

- **Không bao giờ** đặt OAuth token, mật khẩu, API key trong `src/`, `static/`, file JSON công khai hoặc GitHub.
- Cấu hình lưu Drive cần đăng nhập Google OIDC và email được xác minh, khớp `allowed_email` mới hiện uploader.
- Mã dự án được kiểm tra, tên tệp và phần mở rộng bị hạn chế, dung lượng tối đa 25 MB mỗi tệp.
- Không ghi đè revision cũ; không thao tác sửa hoặc xóa tệp khác trên Drive.
- OAuth scope `drive` có quyền rộng đối với toàn bộ Drive của chủ tài khoản. Nếu dùng cho nhiều nhân viên, nên chuyển sang backend riêng, phân quyền nhiều người dùng, giới hạn quyền Google và triển khai nhật ký audit/backup trước khi dùng hồ sơ khách hàng.
- Dữ liệu trong iframe (localStorage/IndexedDB) **chưa tự động đồng bộ** vào Drive. Trình tải trong Streamlit là chức năng quản trị riêng; đồng bộ tự động theo mỗi sheet cần backend có xác thực và được nghiệm thu thêm.

## Kiểm thử

`python -m unittest discover -s tests -p test_drive_storage.py -v`

Kiểm thử này không sử dụng token thực, không tải file thật và không tạo thư mục mới trên Drive.
