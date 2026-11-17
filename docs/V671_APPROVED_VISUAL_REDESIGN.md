# V6.7.1 — Hoàn thiện giao diện theo hình mẫu được duyệt

Ngày cập nhật: 17/11/2026. Bản này **thay đổi cách trình bày**, không thay đổi cơ sở dữ liệu, hệ thống Google OAuth, chữ ký HMAC, các công cụ kỹ thuật V6.4–V6.6 hay logic tính KPI V6.7.

## 1. Phần tương ứng với ảnh mẫu

| Khu vực hình mẫu | Triển khai trong ứng dụng |
|---|---|
| Thanh tiêu đề ngang trên cùng | Header mới cố định toàn chiều rộng, ảnh công trình, tên công ty, phiên bản, nhịp heartbeat, tên sheet |
| Nhãn online bên phải | Chỉ hiện trạng thái **Google Drive đã xác thực** hoặc **Gần thời gian thực · 15 giây**; không gán nhãn WebSocket |
| Chuông 3 thông báo | Chuông hiển thị **số cảnh báo thực** từ dữ liệu được cấp quyền, bằng 0 thì không có số đỏ |
| Biểu tượng ? | Panel hướng dẫn công việc và màn hình Giám sát |
| Avatar / Admin | Avatar ký hiệu và vai trò xác thực Admin / Cập nhật / Chỉ đọc, xem tài khoản qua panel |
| Sidebar trái | 14 mục công việc sắp xếp theo ảnh mẫu, SVG line icons; chọn Giám sát Agent tô cyan |
| Ảnh công trình cuối sidebar | Dùng ảnh công trình/isometric đã có trong repo, không tải từ nguồn ngoài hoặc trích ảnh có markup đỏ |
| Sáu KPI | Từ event ledger / task / handoff thật; không sao chép các số 256, 138, 27, 86,3% của ảnh minh họa |
| Line / donut / bar | Căn chỉnh gọn, có tooltip số lần theo mốc thời gian khi rê chuột |
| Sankey / network / timeline | Dùng phiếu phối hợp MEP và XD thật, gồm chiều MEP → XD và XD → MEP |
| Top Agent / bottleneck / alerts | Thống kê theo số lượt chạy/phiếu tồn; màu cảnh báo có ý nghĩa |
| Báo cáo & Thống kê | Trang chỉ đọc mới: số công việc, trạng thái, bảng theo bộ môn và theo dự án |
| Pháp luật, Kho tài liệu, BOQ, BIM, Cài đặt | Giữ nguyên chức năng trước; Admin-only Settings và thao tác server-side không thay đổi |

**Nét đỏ** trong hình người dùng gửi là nét đánh dấu khu vực cần chỉnh, **không phải màu thiết kế**. Theme chính là xanh đen, cyan, tím, lục, vàng và đỏ chỉ dành cho cảnh báo.

## 2. Quy tắc điều khiển

- Tất cả nút trong thanh mới đều có hành động: **chuông** mở cảnh báo thật, **trợ giúp** mở hướng dẫn, **tài khoản** hiện vai trò/email khi được máy chủ cung cấp.
- Để không làm mất chức năng đăng xuất khi chưa có luồng logout mới trong bridge, nút **Đăng xuất** Streamlit phía trên iframe vẫn được giữ. Không hiển thị logout giả.
- Menu trên desktop có thể cuộn, ảnh công trình nằm cố định ở đáy. Ở mobile menu dạng drawer được giữ lại và offset bên dưới thanh tiêu đề.
- Biểu đồ SVG không tải thư viện qua CDN; nhân viên có thể xem dữ liệu trực tiếp trong iframe đã xác thực.
- Kết quả kỹ thuật của Agent vẫn là nháp cần kỹ sư thẩm tra; dashboard chỉ mô tả sự kiện Agent đã **hoàn tất**, không mô phỏng trạng thái đang xử lý.

## 3. Checklist nghiệm thu

1. Ở độ phân giải **1648×928**, header ngang và sidebar phải sát bố cục hình mẫu, sáu KPI cùng hàng, 3 hàng chart có viền mảnh.
2. Ở **1366×768**, KPI chia hàng hợp lý, Sidebar có thanh cuộn và ảnh công trình không đè các menu.
3. Ở **390×844**, icon và chữ không tràn, biểu đồ một cột, menu mobile mở dưới header.
4. Chọn MEP, XD, phối hợp chéo kiểm tra chuỗi phiếu hai chiều ở dashboard vẫn đúng.
5. Khi không có sự kiện phải hiện 0/—/chưa có dữ liệu, không được hiển thị số trên ảnh minh họa.
6. Chuông phải hiện số cảnh báo được tính từ dữ liệu thật và mở panel; nút ? mở hướng dẫn.
7. Nhân viên **Chỉ đọc** không nhìn thấy **Cài đặt hệ thống**, Admin nhìn thấy và kiểm tra quyền vẫn ở backend.
8. Vào Báo cáo & Thống kê thấy bảng tổng hợp từ dự án được cấp quyền, không có nút ghi hoặc xóa giả.
9. Cập nhật giám sát mỗi 15 giây vẫn thực hiện với Google Drive, giữ bộ lọc sau rerun.
10. Văn phòng 3D, Kho tài liệu, upload Drive, BOQ, BIM, phê duyệt và logout Streamlit không hồi quy.
11. Kiểm tra responsive, zoom 125%, định dạng tiếng Việt và tiếng Anh.
12. Nghiệm thu trực tiếp trên Streamlit Cloud; kết quả GitHub Actions PASS không thay thế browser QA.

## 4. Lưu ý mở rộng

Bản UI vẫn hiển thị trạng thái gần thời gian thực theo polling. Để có thông báo push, trạng thái Agent RUNNING, lịch sử không giới hạn và chuẩn hóa số liệu theo phòng ban cần worker heartbeat, PostgreSQL và event streaming trong phiên bản tiếp theo.
