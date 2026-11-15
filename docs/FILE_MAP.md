# BẢNG QUẢN LÝ TỆP THEO CHỨC NĂNG

| Hạng mục sửa/cập nhật | Tệp nguồn | Mẫu hồ sơ | Quy tắc cập nhật |
|---|---|---|---|
| Công ty 3D / nội thất | `src/3d/scene.js` | — | Thêm đối tượng 3D, giữ chức năng click và camera |
| Tên/phòng ban/nhân viên AI | `src/core/config.js` | `data/samples/AGENTS_DEMO.json` | Giữ `id` ổn định để không mất liên kết nhiệm vụ |
| Quy trình giao việc | `src/core/storage.js` | — | Bổ sung status có migration cho dữ liệu cũ |
| Bản vẽ | `src/core/documents.js` | `data/templates/DRAWING_REGISTER_TEMPLATE.csv` | Mã `DRW-*`, revision từng lần tải |
| BOQ/dự toán | `src/core/boq.js` | `data/templates/BOQ_MEP_TEMPLATE.csv` | Mã `BOQ-*`, lưu original file, phân tích CSV riêng |
| BIM/IFC | `src/core/bim.js` | `data/templates/BIM_REGISTER_TEMPLATE.csv` | Mã `BIM-*`, chưa mở mô hình |
| PCCC | `src/core/documents.js` | `data/templates/PCCC_CHECKLIST_TEMPLATE.csv` | Mã `FIR-*`, giữ lịch sử, chưa chứng nhận đạt |
| Báo cáo | `src/core/documents.js` | `data/templates/REPORT_REGISTER_TEMPLATE.csv` | Mã `RPT-*` |
| Hợp đồng | `src/core/documents.js` | `data/templates/CONTRACT_REGISTER_TEMPLATE.csv` | Mã `CON-*`, chưa có ký số |
| Dashboard và giao diện | `src/app.js`, `src/styles.css` | — | Giữ mapping trang và test regression |
| Nhật ký phiên bản | `versions/*.md`, `CHANGELOG.md` | — | Bổ sung thay đổi, không viết đè nội dung lịch sử |

**Đáng chú ý:** `data/templates/` là file mẫu phát hành trong ZIP. **Các tệp người dùng tải lên** được lưu trong IndexedDB, không ghi lên thư mục hệ thống. Để lưu hồ sơ trong kho chung phải triển khai backend và kho object storage.
