# XD & MEP AI Company 3D — Android APK V5.2 DEMO

## Mục đích
- APK WebView chứa bản web V5.2 hiện có, chạy giao diện không cần máy chủ Internet.
- ID package: `vn.congtyxd3d.app`.
- Android tối thiểu 7.0 (API 24), thiết bị có Android System WebView hiện đại.
- Cho phép nhập tệp CSV/BOQ và hồ sơ qua hộp chọn tệp của Android.

## Build
`GitHub Actions → Build Android APK - XD MEP AI 3D → Run workflow` hoặc build tự động khi mã Android thay đổi.
APK debug: `android/app/build/outputs/apk/debug/app-debug.apk`.
Tải trong artifact của workflow thành công (có thể cần đăng nhập GitHub).

## Cài đặt
1. Chuyển APK sang điện thoại.
2. Trong Files / My Files, bấm APK và cấp quyền "Cài ứng dụng không rõ nguồn" cho trình quản lý tệp nếu Android yêu cầu.
3. Cài ứng dụng, mở **XD & MEP AI 3D**.

## Giới hạn quan trọng
- Đây là APK **debug cho mục đích kiểm tra**, không phải bản phát hành Google Play. Các APK build khác nhau bởi GitHub runners có thể dùng khóa debug khác nhau; cần gỡ bản cũ để cài bản mới nếu khác chữ ký. Khi cần nâng cấp không mất dữ liệu, thiết lập một signing keystore riêng an toàn ở GitHub Secrets, không lưu trong repository công khai.
- Web app vẫn mô phỏng Agent, chưa kết nối backend AI, chưa kiểm tra kỹ thuật tự động.
- Hồ sơ IndexedDB/localStorage chỉ nằm trên máy và bị xóa khi gỡ app hoặc xóa dữ liệu ứng dụng. Sao lưu dữ liệu cần xử lý trước khi gỡ app.
- Một số liên kết tải `blob:` trong WebView có thể không hoạt động đầy đủ như Chrome; cần test trên Android và bổ sung cầu nối xuất tệp native nếu phát hiện lỗi.
- Không lưu hồ sơ dự án thật/nhạy cảm trong APK demo.
- Vẫn cần test trên điện thoại Android thực, đặc biệt WebGL, cập nhật revision và tải tệp từ thiết bị.

## Bảo mật
- Không nhúng khóa API hoặc dữ liệu khách hàng trong APK.
- Tệp web được nạp qua `WebViewAssetLoader` HTTPS origin nội bộ, không dùng `file://`.
- Điều hướng sang host ngoài bị chặn.
