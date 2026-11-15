# V5.0 — Nhánh Xây dựng và trụ sở 3D hai tầng

**Ngày:** 2026-11-15  
**Phạm vi:** Giữ khối MEP và bổ sung 8 phòng Xây dựng/8 Agent, không thay thế dữ liệu cũ.

## Các điểm đã triển khai

- Văn phòng 3D 2 tầng: MEP tầng dưới, Xây dựng tầng trên, có bộ lọc xem toàn công ty/MEP/Xây dựng; hỗ trợ WebGL và SVG dự phòng.
- Ban giám đốc chung và các phòng xây dựng độc lập: Kiến trúc, Kết cấu, BIM xây dựng, QS xây dựng, Kế hoạch, Hiện trường, QA/QC & An toàn, Vật tư.
- 18 Agent mô phỏng; công việc Xây dựng demo độc lập; giữ nguyên nhiệm vụ MEP và bổ sung dữ liệu demo vào bản localStorage cũ theo migration 1 lần.
- Kho hồ sơ: chọn khối trước khi tải tệp; revision phân biệt theo cặp `(division, code)` để không trộn hồ sơ MEP/Xây dựng.
- 2 bảng BOQ CSV demo độc lập; mẫu hồ sơ Xây dựng tách thư mục trong `data/templates` và `project_templates/XD_PROJECT_001`.

## Ranh giới chức năng

- 3D là mô hình thao tác và trạng thái, **không phải ảnh tham khảo đã biến thành mô hình 3D đầy đủ**.
- Agent vẫn chỉ là mô phỏng: chưa gọi LLM, chưa tự đọc DWG, tính kết cấu, phát hiện va chạm IFC hoặc thực thi công việc ngoài web.
- Tệp IndexedDB không tự đồng bộ GitHub hay Google Drive.
- Người quản lý/kỹ sư vẫn phải phê duyệt kết quả trước khi sử dụng cho dự án thực.

## Kiểm thử

- `npm test` (logic, migration, phân khối, revision).
- Kiểm tra cú pháp JS, tải trang web cục bộ và smoke test trình duyệt (nếu có môi trường).
