# HỢP ĐỒNG KỸ THUẬT TÍCH HỢP AI THẬT (CHƯA CÀI ĐẶT)

Đây là thiết kế API đề xuất cho phiên bản sản xuất, không phải API đang chạy.

## Luồng dữ liệu

`UI 3D → FastAPI Backend → Task Queue/Agent Orchestrator → MEP Tools → QA Review → Human Approval → Artifact Storage`.

## Đề xuất endpoint

| Method | Path | Ý nghĩa |
|---|---|---|
| GET | `/api/projects/:id/summary` | Tổng hợp dự án, Agent/task, trạng thái |
| GET | `/api/tasks` | Danh sách task và người phụ trách |
| POST | `/api/tasks` | Tạo task và lưu nhật ký |
| POST | `/api/tasks/:id/execute` | Gửi vào hàng đợi AI có kiểm soát |
| GET | `/api/tasks/:id/events` | Lấy log step/tool, nguồn tham chiếu |
| POST | `/api/tasks/:id/approve` | Kỹ sư được phân quyền duyệt |
| GET | `/api/documents?category=drawings` | Lấy metadata, mã hồ sơ và revision |
| POST | `/api/documents` | Upload binary vào kho riêng theo tenant/project |
| GET | `/api/documents/:id/download` | Kiểm soát quyền tải tệp |
| GET | `/api/bim/:id/model` | Mở model IFC (sau tích hợp) |

## Quy định bắt buộc khi triển khai

1. Cơ chế SSO/password và role-based access theo phòng ban/dự án.
2. Khóa API chỉ ở server, không nhúng vào frontend.
3. File scan malware + mime validation + quotas + isolation.
4. File revision immutable, hash SHA-256 và audit log ai/sửa gì/khi nào.
5. Chỉ AI được thao tác trên bản sao tài liệu đã duyệt quyền; không tự xuất bản hoặc ký hồ sơ.
6. Output có dẫn nguồn và bằng chứng; kết quả tính toán được xác minh bằng tool khoa học/tiêu chuẩn áp dụng đúng phiên bản.
7. Thẩm tra độc lập và ký duyệt bởi người có thẩm quyền.
8. Kiểm thử chống prompt injection trong file người dùng.
9. Tách file storage (S3/MinIO/Drive) và SQL metadata. Có backup-restore và checksum.
10. Quy trình bảo mật dữ liệu dự án khách hàng trước khi đưa vào cloud LLM.
