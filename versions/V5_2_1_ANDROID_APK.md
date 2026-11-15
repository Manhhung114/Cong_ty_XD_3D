# V5.2.1 — Android APK cho Web 3D

- Đóng gói web V5.2 vào native Android WebView (offline assets); 16 phòng ban / 18 Agent demo.
- Android minSdk 24, targetSdk 35; package `vn.congtyxd3d.app`.
- Chọn file qua Android file picker, giữ IndexedDB/localStorage bên trong app.
- GitHub Actions build debug APK và cung cấp qua workflow artifacts.
- Không có AI backend; không có signing release; APK debug chỉ để cài thử.
- Không tự khẳng định đã chạy trên thiết bị thực cho tới khi có log nghiệm thu.

## Kiểm tra nghiệm thu Android
1. APK cài được và ứng dụng mở giao diện, không màn trắng.
2. Chuyển Phối cảnh chi tiết / 3D tương tác; xoay camera, zoom, chọn phòng.
3. MEP / Xây dựng hiển thị đúng từng khối; danh sách AI Agent và công việc.
4. Nhập BOQ CSV bằng file picker; kiểm tra tổng cộng.
5. Upload một hồ sơ mẫu, thêm R02, đóng app/mở lại vẫn còn (IndexedDB).
6. Kiểm tra chức năng xuất tệp: một số `blob:` URL chưa có bridge native nên có thể chưa tải được; báo lỗi để sửa.
7. Xoay màn hình, kiểm tra bố cục và trạng thái được giữ.
8. Kiểm tra RAM/nhiệt/khung hình WebGL trên điện thoại thật.
