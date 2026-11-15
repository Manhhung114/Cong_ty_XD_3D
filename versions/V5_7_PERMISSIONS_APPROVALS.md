# V5.7 — Phân quyền và phê duyệt theo dự án

- Session 8 giờ có thể thu hồi; mật khẩu PBKDF2 SHA-256; không nhúng mật khẩu hoặc API key trong APK.
- Vai trò: admin, director, project_manager, mep_lead, construction_lead, qa, engineer, viewer.
- Thành viên được gán theo từng dự án và khối chuyên môn. Quyền áp tại backend, không chỉ ẩn nút.
- 3 cấp duyệt liên tiếp: QA/QC → trưởng bộ môn phù hợp → quản lý dự án/giám đốc.
- Người tạo, người gửi báo cáo không được tự duyệt; một người không được duyệt hai cấp của cùng báo cáo; từ chối bắt buộc ghi lý do.
- Lưu báo cáo, kiểm tra bước, người duyệt và thời điểm; nhật ký audit riêng mỗi dự án.
- Quản trị tạo tài khoản, gán dự án, cấu hình Agent provider/model (chưa chạy AI thật).
- Ứng dụng demo cũ trong menu riêng; dữ liệu máy chủ không tự đồng bộ nếu chưa kết nối.
- AI key chỉ trong biến môi trường/secret manager. Endpoint chạy AI trả 501 tới khi triển khai công cụ xác minh thực.

**Chưa nghiệm thu production:** MFA, SSO, quy trình xác minh danh tính ký pháp lý, backup/restore thực, kiểm thử xâm nhập.
