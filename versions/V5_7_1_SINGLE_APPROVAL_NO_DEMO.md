# V5.7.1 — Một luồng phê duyệt, không dữ liệu giả

## Thay đổi

- Xóa mục menu **Duyệt dự án thật**. Mục **Chờ phê duyệt** gọi duy nhất backend có xác thực và phân quyền.
- Bỏ công tắc chạy mô phỏng, biểu ngữ demo, dự án demo, bộ số liệu/BOQ tự điền và 12 nhiệm vụ tự tạo.
- Trang Công việc, Kho tài liệu và Nhật ký đọc từ dự án trên máy chủ; chưa kết nối thì yêu cầu đăng nhập thay vì hiển thị dữ liệu giả.
- Phần nhân viên AI nêu rõ **Chưa kết nối AI**, không giả lập trạng thái đang làm.
- Giữ nguyên hồ sơ người dùng đã tải trong IndexedDB và nhiệm vụ người dùng tạo trong localStorage. Bộ 12 nhiệm vụ tự sinh được dọn một lần, chỉ giữ trường hợp đã có báo cáo/ý kiến do người dùng bổ sung.
- Mục Kho tài liệu cung cấp nút tải hồ sơ gốc còn lưu trên thiết bị để người dùng sao lưu trước khi chuyển sang máy chủ.
- APK giữ `applicationId vn.congtyxd3d.app`, nâng `versionCode` lên 58 và chỉ ký release khi được cấu hình khóa riêng trong GitHub Secrets.

## Hạn chế

- Backend cần máy chủ hoạt động. Không có máy chủ, các màn hình công việc/phê duyệt/hồ sơ máy chủ hiển thị đăng nhập và không tự sinh dữ liệu.
- Phần AI chưa kết nối API/công cụ thực và BIM chưa có trình xem IFC.
- Dữ liệu lưu cục bộ cũ không tự động biến thành dự án máy chủ; cần nhập nhiệm vụ có xác nhận và tải hồ sơ nhị phân riêng.

## Nghiệm thu

1. Khởi chạy mới: không có nhiệm vụ/BOQ giả và nút chạy mô phỏng.
2. Chỉ có một menu Chờ phê duyệt; duyệt từ đó đi qua API kiểm tra vai trò.
3. Người không đủ quyền xem được trạng thái nhưng không có nút phê duyệt; backend trả 403 nếu gọi API trái phép.
4. Hai ngôn ngữ hiển thị nhãn tương ứng.
5. Tệp cục bộ do người dùng tải vẫn có thể tải về.
