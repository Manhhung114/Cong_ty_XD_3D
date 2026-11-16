# Kiểm tra lỗi Google OAuth Internal server error (16/11/2026)

## Kết luận từ video
Video 2,43 giây chỉ hiển thị trang trắng và dòng Internal server error.
Không có traceback hoặc HTTP details; không thể khẳng định chính xác lỗi OAuth là gì.
Lỗi này xảy ra ở máy chủ Streamlit khi đăng nhập, trước bước tải tệp lên Drive.

## Đăng nhập chuyển vào Cài đặt
- Văn phòng 3D → Cài đặt → Google Drive · Kho hồ sơ dự án.
- Nút mở https://congtyxd.streamlit.app/?drive=settings trong tab mới.
- Luồng st.login phải chạy ở trang Streamlit top-level, không bên trong iframe.
- Sau khi đăng nhập xong, quay lại Cài đặt → Google Drive để quản lý hồ sơ.

## Kiểm tra nhật ký lỗi thật
1. Vào share.streamlit.io → congtyxd → Manage app → Logs.
2. Bấm đăng nhập Google một lần; lấy traceback tương ứng thời điểm xảy ra lỗi.
3. Che tất cả token, Client Secret, Authorization code và cookie khi gửi log.
4. Nếu thấy redirect_uri_mismatch: cấu hình Web Client redirect đúng https://congtyxd.streamlit.app/oauth2callback.
5. Nếu thấy invalid_client: Client ID/Secret trong [auth] không khớp Web OAuth client.
6. Nếu thấy MismatchingStateError hoặc Missing provider for OAuth callback: kiểm tra cookie/state, thử cửa sổ ẩn danh.
7. Nếu lỗi cấu hình: kiểm tra [auth] trong Streamlit Secrets, lưu và Reboot.

## Quy tắc
- Giao diện kiểm tra thông tin cấu hình không hiển thị bí mật.
- Phiên bản Streamlit được ghim 1.67.0, có vá lỗi OAuth cũ.
- Không đăng thông tin OAuth lên GitHub, tài liệu hay ảnh chụp.
- Client Secret từng hiển thị trong ảnh phải thay mới trước khi dùng thật.
- Chưa xác nhận lỗi Internal server error đã hết nếu không có log và kiểm tra trên Cloud.
