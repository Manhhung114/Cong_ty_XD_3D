# V5.5 — Phê duyệt có nội dung, tiếng Anh toàn diện, chữ ký APK ổn định

## Thay đổi

- Menu **Chờ phê duyệt / Pending Approvals** mới, lọc theo nhân viên và mở chi tiết nhiệm vụ.
- Từ thẻ nhân viên đang chờ duyệt hoặc bảng công việc có nút **Xem và duyệt**.
- Chi tiết gồm tên công việc, nhân viên, trạng thái, hồ sơ theo mã và revision, nội dung báo cáo, phát hiện và lịch sử các lần duyệt.
- Chưa có báo cáo hoặc tệp liên quan: **không thể bấm Phê duyệt**. Cho phép gửi báo cáo thực hiện hoặc tải hồ sơ theo mã; bác/trả lại bắt buộc lý do.
- Tên người duyệt được ghi vào lịch sử localStorage, không phải hệ thống xác thực/chữ ký số có giá trị pháp lý.
- Chặn thao tác chuyển thẳng nhiệm vụ sang `done` bằng dropdown; bắt buộc đi qua phần duyệt.
- Thêm dịch tiếng Anh của tên/vai trò/mô tả các Agent, nhiệm vụ mẫu, danh mục hồ sơ, tiêu chuẩn, trang BIM/BOQ/lộ trình và các trang trạng thái.
- Sửa chuyển đổi VI ↔ EN hai chiều cho cả phần tử giao diện tĩnh; không đổi mã TCVN, mã hồ sơ và tệp do người dùng cung cấp.
- Chuẩn bị cấu hình Android release signing lấy khóa từ GitHub Secrets; không lưu khóa trên GitHub công khai.

## Giới hạn / Hướng dẫn nghiệm thu

1. Đây là nguyên mẫu **không có AI thực hoặc backend đa người dùng**. Báo cáo được người dùng nhập, không phải sản phẩm do AI tự tạo.
2. Kiểm thử nội dung duyệt, đóng/gỡ, trả lại, lịch sử và dữ liệu cũ trên trình duyệt và Android.
3. Chỉ bản release ký bằng cùng keystore qua các phiên bản và `versionCode` tăng dần mới cài đè không gỡ. Bản debug V5.4 trước đó không bảo đảm cùng chữ ký.
4. Cần bổ sung đăng nhập, phân quyền, nhật ký không thể sửa và quy trình duyệt kỹ thuật thật ở phiên bản backend.
5. Nguyên văn tài liệu/tiêu chuẩn và nội dung người dùng nhập vẫn giữ nguyên. Bản dịch tiếng Anh là phần trình bày, không thay đổi văn bản pháp lý.
