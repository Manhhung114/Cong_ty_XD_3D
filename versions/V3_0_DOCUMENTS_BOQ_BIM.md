# V3.0 — TÀI LIỆU, BOQ VÀ BIM

**Tình trạng:** Quản lý hồ sơ phiên bản + BOQ CSV demo. **BIM viewer chưa triển khai.**

## Đã có

- 6 loại hồ sơ: bản vẽ, BOQ, BIM/IFC, PCCC, báo cáo, hợp đồng.
- Nhập file trên trình duyệt, lưu nội dung và metadata trong IndexedDB, code giữ cố định, revision R01/R02/R03.
- Lịch sử phiên bản, tải tệp gốc từng revision, xóa tệp có xác nhận.
- Nhập BOQ CSV, tính tổng tiền theo dòng và tổng dự toán minh họa.
- Mẫu CSV tách riêng theo loại trong `data/templates/`.

## File riêng phụ trách

- `src/core/documents.js`: lưu trữ và phiên bản.
- `src/core/boq.js`: xử lý BOQ.
- `src/core/bim.js`: công khai giới hạn BIM.
- `data/templates/*.csv`: mẫu độc lập, có thể thay.
- `project_templates/MEP_PROJECT_001/`: thư mục lưu file gốc bên ngoài web.

## Chưa có

- Trích xuất số liệu từ DWG, PDF, IFC, Excel XLSX.
- Viewer IFC/BIM, đánh dấu clash và tự cập nhật mô hình.
- Tự đồng bộ Google Drive hoặc server.
