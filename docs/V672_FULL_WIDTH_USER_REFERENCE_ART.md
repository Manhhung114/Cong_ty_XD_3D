# V6.7.2 — Toàn màn hình, bỏ viền đen và dùng đúng ảnh mẫu

Ngày cập nhật: 17/11/2026. Áp dụng cho ứng dụng Streamlit `congtyxd.streamlit.app` và giao diện HTML/CSS đã xác thực Google.

## Mục tiêu

1. Khắc phục hai dải đen hai bên trên desktop do khung nội dung Streamlit mặc định chừa `padding-inline` và `max-width`, trong khi iframe và `.content` còn giới hạn chiều ngang.
2. Sử dụng đúng ảnh mẫu đã được người dùng gửi, **chỉ lấy phần đồ họa** để tránh trùng lặp nút/text của ảnh chụp giao diện.
3. Giữ tất cả chức năng công ty, phân quyền Admin, OAuth Google, Google Drive, MEP và Xây dựng.

## Tệp ảnh trích từ mẫu do người dùng cung cấp

| Tên file | Nội dung | Vị trí |
|---|---|---|
| `static/assets/user_reference_header_v672.webp` | Toà nhà/silhouette xanh ở đỉnh ảnh | Thanh tiêu đề toàn chiều rộng + nền lớp tiêu đề sheet |
| `static/assets/user_reference_sidebar_v672.webp` | Công trình sáng đèn, nền trời xanh | Ảnh chân menu trái |
| `static/assets/user_reference_foyer_v672.webp` | Phòng điều hành/văn phòng 3D | Nền ảnh mờ sau các sheet |

Ảnh giữ cục bộ trong GitHub, không sử dụng URL tài khoản người dùng hoặc hình đầy đủ với văn bản và nút giả. `command_shell.js` khai báo đường dẫn an toàn, bộ tạo Streamlit bundle chuyển ảnh đã được kiểm soát thành data URL; phiên đăng nhập Google vẫn là điều kiện để tải toàn bộ giao diện.

## Kỹ thuật mở tràn khung màn hình

- Trong `streamlit_app.py`, `st.set_page_config(layout="wide")` vẫn được giữ, nhưng CSS nay đưa **`stMain`**, **`stMainBlockContainer`**, **`.block-container`**, **`stVerticalBlock`** về 100% chiều ngang, `max-width:none`, `margin:0`, `padding:0`. Đây là nguyên nhân chính của vùng trống trái/phải.
- Đặt iframe trong `st.container(key="xd_fullwidth_workspace")` để chỉ chỉnh kích thước đúng iframe chính, không vô tình làm to iframe cầu nối Google Drive.
- Iframe hiển thị có `width:100%` và `height:calc(100dvh - 44px)` trên desktop, tương ứng toàn bộ diện tích sau thanh tài khoản/đăng xuất bên ngoài Streamlit.
- Trong giao diện, `#app`, `.main` và `.content` đều có chiều rộng fluid, `.content` không còn `max-width:1600px`. Khu dashboard và văn phòng 3D cũng tự căn theo khung rộng.
- Không phóng ảnh mẫu thành toàn bộ trang, vì cách đó tạo chữ/số/nút giả và mờ khi hiển thị trên màn hình 2K/4K.
- Hình nền dùng overlay dark navy để vẫn đọc được số liệu và các cảnh báo.

## Kiểm tra nghiệm thu

1. 1920×1080, 1672×941, 1366×768: ứng dụng lấp đầy chiều ngang trình duyệt, không có hai dải đen cân đối do khung ngoài.
2. 1920×1080: thanh tiêu đề, sidebar, KPI, bảng và đồ thị không bị co vào một khung 1600px ở giữa.
3. 390×844: menu trượt, dashboard co cột, không có cuộn ngang toàn trang.
4. Logo/header có ảnh tòa nhà, sidebar có ảnh công trình và lớp nền sau sheet có bóng văn phòng, **không có chữ hoặc button ảnh chụp đè lên nút thật**.
5. Đăng nhập Admin và nhân viên đọc: quyền Settings vẫn đúng; chức năng tải lên Drive và bật dialog không làm vỡ kích thước iframe.
6. Đăng xuất qua thanh Streamlit hoạt động; không tạo nút đăng xuất giả trong iframe.
7. Nhấn vào Văn phòng 3D/MEP/XD, Công việc, Kho tài liệu, Giám sát Agent, Báo cáo: các sheet có nền thống nhất và không tự thay đổi số liệu.
8. Kiểm tra nút thay đổi MEP/XD, biểu đồ MEP↔XD vẫn dùng event HMAC thực và tự làm mới 15 giây.
9. Kiểm tra chế độ zoom trình duyệt 100%, 125%; chạy Chrome/Edge trên máy tính.
10. Chạy test Python/Node và quan sát trực tiếp bản Streamlit Cloud trước khi ký nghiệm thu cuối.

**Giới hạn:** Đây là bản chỉnh giao diện và khung chứa. Chưa thử trực tiếp trên trình duyệt người dùng có đúng trình duyệt/độ phân giải; CSS có thể cần tinh chỉnh riêng nếu Streamlit đổi tên selector trong phiên bản mới.
