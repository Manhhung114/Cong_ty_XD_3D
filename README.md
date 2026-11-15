# MEP AI COMPANY 3D — Prototype V1.0–V4.0

**Bản bàn giao:** 2026-11-15  
**Loại:** Ứng dụng web 3D chạy cục bộ, không cần Node package, npm hoặc API key.  
**Trạng thái:** Demo chức năng. **Chưa** kết nối AI Agent thực sự, Google Drive, BIM engine hoặc cơ sở dữ liệu máy chủ.

## Chạy phần mềm

### Windows

1. Giải nén ZIP vào một thư mục **không** chứa mã nguồn sản xuất cũ.
2. Nhấp đúp `RUN_WEB_3D.bat` (máy cần có Node.js hoặc Python 3).
3. Trình duyệt mở `http://localhost:8766`. Nếu không tự mở, nhập địa chỉ đó.
4. Giữ cửa sổ dòng lệnh đang chạy khi sử dụng ứng dụng. Muốn dừng, nhấn `Ctrl+C`.

### macOS / Linux

Mở Terminal trong thư mục dự án, chạy:

```bash
sh RUN_WEB_3D.sh
```

Mở `http://localhost:8766`.

### Nếu máy chỉ có Python

```bash
python -m http.server 8766
```

**Không mở trực tiếp bằng cách nhấp đôi `index.html`**. Trình duyệt có thể chặn ES modules và `fetch` khi chạy dạng `file://`.

## Chức năng sẵn có

| Mốc | Tính năng hiện có | Chưa có |
|---|---|---|
| V1.0 | WebGL 3D, 8 phòng, 10 nhân viên avatar; click phòng/Agent, xoay, zoom; SVG isometric dự phòng | Mô hình nội thất 3D chất lượng thương mại, hoạt cảnh thực tế cao |
| V2.0 | Tạo nhiệm vụ, giao Agent theo phòng ban, chuyển trạng thái, mô phỏng luồng và nhật ký | LLM API, thuật toán kỹ thuật, quy trình agent tự thực thi |
| V3.0 | Nhóm hồ sơ, tải tệp và giữ revision bằng IndexedDB, mẫu bản vẽ/BOQ/BIM/PCCC; CSV BOQ có tính tổng | Đọc DWG/RVT/IFC, Excel XLSX trực tiếp, tách khối lượng từ mô hình |
| V4.0 | KPI, màn hình tiến độ, sự kiện và xuất JSON metadata | CSDL đa người dùng, SSO, quyền duyệt, sao lưu máy chủ, dashboard số liệu thực |

## Cấu trúc thư mục tách biệt

```text
mep_ai_company_3d/
├── index.html                          # Điểm khởi chạy web
├── server.mjs                          # Web server Node.js thuần
├── RUN_WEB_3D.bat/.sh                  # Mở ứng dụng
├── src/
│   ├── app.js                          # Điều hướng, giao diện, form, sự kiện
│   ├── styles.css                      # Theme và responsive
│   ├── 3d/scene.js                     # WebGL & fallback isometric
│   └── core/
│       ├── config.js                   # Phòng ban, Agent, danh mục, roadmap
│       ├── storage.js                  # Nhiệm vụ + nhật ký, localStorage
│       ├── documents.js                # Upload, download, revision, IndexedDB
│       ├── boq.js                      # Phân tích BOQ CSV, tổng giá
│       ├── bim.js                      # Khai báo khả năng BIM (chưa tích hợp)
│       └── export.js                   # Xuất metadata JSON
├── data/
│   ├── samples/                        # Dữ liệu DEMO, có thể xóa khi đưa vào sản xuất
│   └── templates/                      # Từng mẫu nghiệp vụ độc lập
├── project_templates/MEP_PROJECT_001/  # 6 thư mục dành cho hồ sơ thực tế sau này
├── versions/                           # Ghi chú V1.0, V2.0, V3.0, V4.0 riêng
├── docs/                               # Hướng dẫn, kiểm thử và quy ước cập nhật
└── tests/                              # Bộ kiểm thử core bằng Node built-in
```

## Quy tắc cập nhật hồ sơ

1. Mỗi tài liệu có **mã cố định** như `DRW-E-001`, `BOQ-MEP-001`, `BIM-MEP-001`.
2. Tải tệp lần đầu tạo `R01`. Khi thay đổi, tải tệp mới **cùng mã**, hệ thống tạo `R02`, `R03`… (không ghi đè tệp cũ).
3. Ghi mô tả thay đổi; ở màn hình hồ sơ, bấm **Lịch sử** để xem revision và tải từng tệp gốc.
4. Các loại hồ sơ khác nhau có thể có cùng phiên bản R01 nhưng mã hồ sơ khác nhau. **Hệ thống không tự so sánh nội dung DWG/PDF/XLSX.**
5. Tệp upload hiện lưu trong **IndexedDB của trình duyệt hiện tại**, không tự đi vào `data/` hoặc `project_templates/`, cũng không tự đồng bộ lên Google Drive. Xóa dữ liệu trang web có thể làm mất file đã upload. Cần giữ file gốc bên ngoài ứng dụng.

## BOQ CSV

Tệp ví dụ: `data/samples/BOQ_DEMO.csv`.

5 cột bắt buộc/khuyến nghị: `code,description,unit,quantity,unitPrice`. Cần `quantity` và `unitPrice` để tính. Ứng dụng hỗ trợ phân cách dấu phẩy hoặc chấm phẩy, số thập phân kiểu Việt Nam. Thành tiền = khối lượng × đơn giá; **chưa** tính VAT, chiết khấu hay kiểm tra đơn giá thực tế.

Nhập CSV qua **BOQ / Dự toán → Đọc CSV**. Nếu muốn lưu nguyên tệp dưới dạng hồ sơ có revision, tiếp tục dùng **Kho tài liệu → BOQ / Dự toán**.

## Kiểm thử đã thực hiện

- Lệnh `npm test` (không cần cài gói): 6/6 test logic PASS.
- Kiểm tra cú pháp JS bằng `node --check`: PASS.
- Kiểm tra giao diện mô phỏng bằng trình duyệt giới hạn: phần UI, điều hướng, tạo nhiệm vụ, chọn phòng, mở form upload, BOQ mẫu và SVG isometric dự phòng có thể hiển thị; không phát hiện lỗi JS trong lần thử đó.
- **Chưa xác minh** khởi tạo WebGL trên thiết bị thực, tải IndexedDB trên trình duyệt có origin thông thường, và độ ổn định khi nhiều file lớn. Các chức năng này cần kiểm thử trên thiết bị đích trước nghiệm thu.

## Điều kiện để chuyển thành công ty MEP AI thật

Cần bổ sung backend, khóa API lưu phía server, điều phối Agent, công cụ tính toán kỹ thuật đã kiểm định, kho tệp phía server, phân quyền theo dự án, phê duyệt bởi kỹ sư, nhật ký bất biến và kết nối BIM. Xem `docs/AI_BACKEND_CONTRACT.md`.

**Bảo mật:** Mã nguồn demo chạy hoàn toàn trên trình duyệt và không gửi tệp lên server. Không lưu hồ sơ dự án bảo mật hoặc thông tin cá nhân trong demo. Mọi dữ liệu trong `data/samples` đều là minh họa, không dùng cho thiết kế hoặc nghiệm thu.
