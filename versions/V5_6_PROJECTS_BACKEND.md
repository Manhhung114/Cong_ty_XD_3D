# V5.6 — Backend & đa dự án

- FastAPI `backend/main.py`, SQLAlchemy `backend/models.py`, PostgreSQL production hoặc SQLite local.
- Dự án riêng biệt với `project_id` cho nhiệm vụ, revision, hồ sơ và nhật ký.
- Truy vấn theo thành viên được cấp quyền; tài khoản không thuộc dự án nhận 403.
- Web và Android có nút kết nối API HTTPS và bảng chọn dự án. Web server chạy đồng thời frontend và `/api`.
- Migrate localStorage bằng nút xác nhận riêng: nhiệm vụ cũ chuyển sang `todo`, không lấy trạng thái duyệt giả; không xóa dữ liệu cũ.
- Upload tệp nhị phân riêng trên server, lưu SHA-256 và revision theo `(project, division, code)`.
- Phối cảnh có đủ 16 phòng/điểm chọn; các khu làm việc bổ sung được minh họa trên mặt ảnh.

**Chưa nghiệm thu production:** chống malware khi tải tệp, sao lưu database/object storage, tổ chức nhiều tenant, SSO, hiệu năng, Android thực tế.
