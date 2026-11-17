# V6.7.9 — Đọc tệp kỹ thuật trên Google Drive tối đa 50 MiB

**Ngày:** 17/11/2026 — phạm vi: bộ đọc file được gọi từ dialog **Công việc → Chạy Agent**.

## Phân biệt hai giới hạn

| Công đoạn | Giới hạn | Ghi chú |
|---|---:|---|
| Tải file vào Google Drive | 500 MB | Giữ nguyên; các định dạng đã được cho phép |
| Agent tải file từ Drive để phân tích | **50 MiB** | 52.428.800 byte; trên 50 MiB bị từ chối trước tải |
| Đọc mẫu DXF | 1.500 đối tượng đầu và 300 records | Không phải clash/thiết kế Shop Drawing |
| Đọc mẫu PDF | 12 trang đầu, 300 records | Không OCR ảnh scan |
| Đọc mẫu XLSX/CSV | 350 dòng, 300 cells, tối đa 5 sheet XLSX | Bảo vệ CPU/memory, không đối chiếu toàn bộ BOQ |
| Đọc mẫu IFC | 1.500 IfcProduct đầu | Không geometry engine/clash; mô hình quá phức tạp có thể không xử lý trong Streamlit |

**File hỗ trợ**: PDF, XLSX, CSV, ASCII DXF, IFC. **Không hỗ trợ trực tiếp**: DWG, RVT, NWD, XLS; cần chuyển đổi sang định dạng hỗ trợ hoặc worker CAD/BIM chuyên dụng. Tệp kích thước <=50 MiB vẫn có thể bị từ chối nếu cấu trúc bị lỗi, ZIP nở quá mức, model IFC quá phức tạp, không đủ bộ nhớ/CPU máy chủ hoặc sai quyền/sổ hồ sơ. Không hứa hẹn xử lý toàn bộ nội dung.

## Đường xử lý

1. Tài khoản được cấp quyền đăng nhập Google; tài liệu phải nằm trong folder category đúng dự án và đã có sổ hồ sơ với metadata được ký.
2. Nút **Chạy Agent** chỉ liệt kê file đúng nhóm của Agent, thuộc dự án, chưa lưu trữ và <=50 MiB theo metadata đã đăng ký.
3. Khi chạy thật: server xác minh project ID, user RBAC, file ID, category, parent, kích thước, revision và checksum đã đăng ký; tải file qua Google Drive server-only với trần **50 MiB**.
4. Parser chỉ trích mẫu theo định dạng: DXF >=8 MiB dùng **ezdxf.addons.iterdxf**, tệp tạm tự xóa, giải phóng tài nguyên; XLSX kiểm tra khai báo kích thước giải nén trước khi openpyxl phân tích.
5. Kết quả kèm SHA-256 và nguồn trang/dòng/cell/handle/GlobalId, lưu thành **nháp yêu cầu kỹ sư xác minh**; không tự phê duyệt và không tuyên bố phân tích full-file.
6. Nếu chọn **AI + trích xuất file**, chỉ những mẫu giới hạn được gửi tới Gemini/OpenAI, sau khi người dùng đồng ý. Không gửi file nhị phân gốc.

## Kiểm thử/nghiệm thu thực tế bắt buộc

- [ ] Thử PDF/CSV/XLSX nhỏ hơn 8 MiB: bảo đảm không hồi quy.
- [ ] Thử file đúng bộ môn có kích thước 8–10 MiB: chọn được từ danh sách và có báo cáo có provenance.
- [ ] Thử **DXF ASCII 30–50 MiB** thực, xác nhận mode đọc streaming, giới hạn mẫu 1.500 entity, không hết RAM hoặc timeout.
- [ ] Thử file **chính xác 50 MiB**, xác nhận đúng ngưỡng được nhận; file lớn hơn ngưỡng bị từ chối trước khi tải.
- [ ] Thử PDF scan, XLSX zip bomb, IFC lớn/phức tạp: hệ thống từ chối hoặc cảnh báo phù hợp, không làm nghẽn app.
- [ ] Thử không có hồ sơ, tài liệu sai dự án, sai folder, sai category, thiếu đăng ký, đổi checksum sau ghi sổ.
- [ ] Thử tài khoản Admin/Cập nhật/Chỉ đọc và 2 thiết bị, giữ nguyên dữ liệu và khóa API mã hóa.
- [ ] Đo bộ nhớ CPU của Streamlit khi thực thi đồng thời; nếu không đạt, dùng worker độc lập với hàng đợi, không tăng tiếp memory không có kiểm soát.

**Trạng thái:** mã nguồn + CI thử nghiệm tổng hợp; cần chạy file thật trên Streamlit Cloud trước khi coi là đã nghiệm thu production.
