# V5.7.3 — Chế độ cục bộ, không đăng nhập và Cài đặt API
Ngày: 15/11/2026 · nhánh `main`

## Phạm vi hoàn thành

- Ẩn mục **Tài khoản & quyền** khỏi menu và thay bằng **Cài đặt**.
- Tạm bỏ kiểm tra đăng nhập/role ở **Quản lý dự án, Công việc, Chờ phê duyệt, Kho tài liệu, Nhật ký** trên phiên bản giao diện chạy offline.
- Quản lý nhiều dự án ở `localStorage` (mỗi nhiệm vụ có `projectId`), tệp gốc trong `IndexedDB` và revision phân biệt theo `(project, division, code)`.
- Không tự sinh dự án demo hoặc nhiệm vụ giả; giữ nguyên công việc người dùng tạo trong dữ liệu V5.5 nếu có. Tạo `LEGACY-LOCAL` để bảo toàn chúng khi cần.
- Bảng điều khiển hiển thị số việc và hồ sơ đang có trên thiết bị; không còn số liệu đòi máy chủ.
- Phê duyệt nội bộ một cấp theo người ghi tên, có báo cáo tối thiểu, nhận xét và lịch sử. **Không xác thực danh tính người duyệt và không có giá trị phê duyệt pháp lý**.
- Cài đặt: OpenAI/Gemini, chọn model theo từng Agent (18 Agent, Giám đốc + QLDA chỉ có một bản cấu hình dùng chung), kiểm tra danh sách model qua nhà cung cấp.
- Khóa API chỉ giữ trong RAM khi đang dùng; người dùng có thể chọn lưu ciphertext AES-256-GCM qua WebCrypto/PBKDF2 với mật khẩu riêng. Không có khóa và mật khẩu nào lưu trong mã nguồn, repository hay bản APK.
- Chữ ký phát hành Android và `applicationId=vn.congtyxd3d.app` không đổi; tăng `versionCode` lên 60. APK release vẫn cần bí mật ký GitHub Actions được cấu hình riêng.

## Điều chưa triển khai / giới hạn

1. **Chưa có AI Agent tự thực hiện nhiệm vụ.** Kiểm tra API chỉ đọc danh sách model; khi có backend cần bổ sung trình điều phối Agent có giới hạn quyền và chi phí.
2. **Không có đồng bộ máy chủ hoặc phân quyền bảo mật** trong chế độ này; bất cứ ai mở thiết bị đều có thể xem/sửa các mục cục bộ.
3. Kết quả phê duyệt chỉ là dấu vết công việc nội bộ, **không phải chữ ký số**. Backend phân quyền V5.7 vẫn giữ trong `backend/` và `src/portal.js` nhưng không được khởi động từ giao diện V5.7.3.
4. Khóa API được mở khóa trong JavaScript luôn có rủi ro lộ nếu thiết bị hoặc webview bị xâm nhập. **Nên dùng khóa có hạn mức thấp**; sau này chuyển khóa lên máy chủ.
5. Bản sao JSON qua nút Sao lưu **không bao gồm blob tệp gốc và không bao gồm API key**. Cần tải riêng tệp quan trọng.
6. Chức năng upload hồ sơ IndexedDB cần kiểm tra thêm trên điện thoại Android thật; có thể mất dữ liệu khi xóa dữ liệu ứng dụng/gỡ app.

## Các tệp chính

- `src/local_portal.js`: xử lý đa dự án và công việc/duyệt nội bộ.
- `src/core/api_settings.js`: settings providers/model/API keys, mã hóa tùy chọn.
- `src/app.js`: menu, kết nối các màn hình, chỉ số cục bộ, nút xuất dữ liệu.
- `src/core/documents.js`: revision theo dự án.
- `src/core/i18n.js`, `src/core/config.js`: song ngữ và lộ trình.
- `server.mjs`: chỉ phục vụ tài nguyên frontend, không rò dữ liệu backend hoặc file nhạy cảm.
- `tests/v573.test.mjs`: kiểm thử logic dữ liệu dự án, review, revision, mã hóa, ứng dụng Android.

## Tiêu chí nghiệm thu

- Mở không cần đăng nhập; tạo 2 dự án, mỗi dự án xem đúng nhiệm vụ riêng.
- Gửi báo cáo, duyệt/trả lại, xem lịch sử trong một dự án.
- Gán nhà cung cấp và model cho Agent, đổi ngôn ngữ Việt/Anh.
- API key không xuất hiện trong localStorage dưới dạng rõ; có thể mở bằng đúng mật khẩu.
- Giữ 16 vị trí trên phối cảnh, 18 Agent và Ban điều hành dùng chung.
- Build APK bằng GitHub Actions, cài/kiểm tra dữ liệu thực trước khi nghiệm thu Android.
