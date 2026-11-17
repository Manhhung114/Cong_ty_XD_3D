# V6.7.3 — Phủ kín màn hình và loại bỏ khoảng trống khi cuộn

Căn cứ video nghiệm thu `Recording 2026-11-17 102648.mp4` ở kích thước 1910 × 898:

- Thanh tiêu đề dùng ảnh tòa nhà đã cung cấp nhưng phần nền hiện chỉ là một khối hình hẹp ở giữa vì CSS `background-size: auto 115%`; phần còn lại xanh đen không đồng nhất.
- Khi cuộn gần cuối **Văn phòng 3D**, các card công việc và phòng ban kết thúc cao hơn chân màn hình, phía dưới còn vùng nền tối lớn.
- Streamlit và ứng dụng HTML chạy trong iframe tạo hai vùng có thể cuộn; trước bản sửa, chiều cao iframe cố định 1100px trong API và có override CSS trên trình duyệt, dẫn đến khả năng cuộn trang ngoài tới vùng trống.

## Thay đổi mã

1. **Thanh tiêu đề:** phủ ảnh skyline trên toàn chiều rộng bằng `background-size: 100% 100%` cùng lớp gradient mờ hai đầu, đồng thời dàn nền trong thanh thông tin sheet. Không đè giao diện text/nút.
2. **Khung Streamlit:** giới hạn vùng ngoài ở `100dvh`, giảm khả năng cuộn thừa; iframe tự chiếm toàn bộ viewport trừ hàng tài khoản/đăng xuất. Vẫn giữ đăng nhập bắt buộc trước khi dựng iframe, giữ dialog Streamlit.
3. **Các sheet:** `main`, `content`, `page-body` co giãn theo chiều cao và chiều rộng khả dụng, không giới hạn max-width 1.600px.
4. **Văn phòng 3D:** tăng chiều cao phối cảnh từ mức cố định lên `clamp(490px,62dvh,830px)` trên máy tính; kéo khung công việc/phòng ban ít nhất `34dvh`, hai cột vẫn độc lập.
5. **Mobile:** sidebar drawer và khung mobile giữ nguyên; tòa nhà header phủ ngang viewport, nội dung chuyển sang một cột, không cắt nút.

## Điều không thay đổi

Không sửa Google OIDC, cấp quyền, HMAC, Google Drive, dữ liệu dự án, 18 Agent, bảng giám sát MEP/XD, hoặc bộ công cụ kỹ thuật. Các chỉnh sửa phần nhìn thực hiện tại `streamlit_app.py`, `src/polish.css` và bản sao `static/src/polish.css`.

## Nghiệm thu

- Chrome/Edge 100% ở màn hình 1910×898, 1648×928 và 1366×768: ảnh skyline trải đều toàn header, tất cả card tận dụng vùng rộng.
- Dùng con lăn xuống cuối Văn phòng 3D: không xuất hiện một **vùng cuộn Streamlit thứ hai** với nền trống bên dưới iframe. Khung nội dung không co cụm về giữa.
- Chuyển sang Giám sát Agent, Kho tài liệu, BOQ, BIM: nội dung rộng hết vùng khả dụng, có thể cuộn bên trong ứng dụng, thao tác file vẫn thực hiện được.
- Đăng nhập nhân viên, kiểm tra Cài đặt vẫn ẩn; Admin còn thấy Cài đặt. Popup Google Drive và đăng xuất Streamlit vẫn hoạt động.
- Thử màn hình điện thoại 390×844 và xoay ngang, không mất sidebar hoặc tràn ngang.
- **Chưa xác minh trực tiếp trên website đăng nhập sau khi triển khai**; phải đối chiếu video thực tế. CI chỉ xác minh mã và kiểm thử hành vi, không thay cho browser QA.

Bản sửa không đưa số liệu demo vào dashboard.
