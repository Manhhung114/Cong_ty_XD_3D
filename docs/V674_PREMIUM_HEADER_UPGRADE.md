# V6.7.4 – Premium Header Upgrade

Ngày thực hiện: 17/11/2026.

## Vấn đề từ ảnh chụp màn hình

Trên ứng dụng V6.7.3, ảnh kiến trúc ở thanh tiêu đề bị **mờ và dẹt**. Nguyên nhân nằm ở `user_reference_header_v672.webp`, file cắt chỉ **350×90 px** (~4,3 KB), được kéo bằng `background-size: 100% 100%` trên màn hình 1366–1920 px hoặc lớn hơn. Nhân rộng độ phân giải file cũ đơn thuần không thể phục hồi chi tiết gốc.

## Thay đổi đã triển khai

1. Thêm **`static/assets/premium_skyline_v674.svg`** với khung tọa độ vector **3200×420**, gồm đường chân trời, các tòa nhà kính, mái văn phòng, cửa sổ và ánh sáng cyan. Các đối tượng vector giữ sắc nét ở màn hình Retina/2×/4K, không cần ảnh 1×/2× khác nhau.
2. Thêm **`static/assets/premium_emblem_v674.svg`**, vector 512×512 dành riêng cho logo ở header, không dùng ảnh dải skyline bị ép thành logo hình vuông.
3. Trong `src/core/command_shell.js` và mirror `static/src/core/command_shell.js`, thay hình header/logo bằng hai asset vector mới; giữ hình công trình ở cuối sidebar V6.7.2 theo yêu cầu trước.
4. Trong `src/polish.css` và mirror, đặt hình nền header với **`background-size: cover`** để giữ đúng tỷ lệ kiến trúc; đặt vị trí ảnh quanh 45% chiều cao. Lớp chuyển sắc tối hai đầu giữ chữ, logo, Google Drive, chuông và avatar rõ ràng.
5. Tăng nét viền logo, ánh sáng cyan, độ dày chữ tiêu đề, độ tương phản nhãn online, độ nổi icon heartbeat và viền phân tách header. Cân chỉnh riêng trên desktop >1700px, laptop <=1500px, tablet <=1020px và mobile <=750px.
6. Nhãn phiên bản hiển thị **V6.7.4**. Các asset tự động **đóng gói nội tuyến** bên trong iframe riêng tư; không phụ thuộc đường dẫn static công khai hoặc CDN.

**Lựa chọn kỹ thuật:** thay vì xuất hai file WebP 1×/2× từ ảnh nhỏ bị mờ, phiên bản này sử dụng **SVG gốc vector** có thể tăng lên hàng nghìn pixel mà không giảm độ nét. Nhờ vậy hiệu quả tương đương hoặc tốt hơn ảnh raster Retina cho các đường nét kiến trúc và logo. Artwork này là minh họa vector mới theo tinh thần hình mẫu, không phải bản phóng lớn từng pixel của ảnh chụp cũ.

## Giới hạn và kiểm thử

- Header vector là ảnh minh họa, không phải ảnh thực tế của dự án hay chứng cứ kỹ thuật. Không có chuỗi ký tự/giao diện mô phỏng trong ảnh.
- Không thay đổi Google OAuth, chức năng Cài đặt Admin-only, API AI, dữ liệu Drive, backend event ledger, bảng MEP/XD hay luồng phê duyệt.
- Bộ kiểm thử tự động kiểm tra SVG hợp lệ, kích thước viewBox, bundler inline ảnh, tính tương thích của CSS src/static, các breakpoint và rào chắn quyền truy cập.
- GitHub Actions PASS chưa thay được kiểm tra bằng trình duyệt thật trên tài khoản đã đăng nhập.

## Checklist nghiệm thu trình duyệt

1. Trên màn **1910×898** ở 100% zoom, tòa nhà sắc, không bị kéo dẹt, logo riêng nét, tên công ty đọc rõ.
2. Trên màn **2560×1440/Retina**, zoom 125–200%, nét SVG không mất chi tiết; không có ảnh 350 px bị giãn lớn.
3. Header dàn kín chiều ngang, nền hai đầu tối vừa đủ để logo/chữ/tài khoản rõ.
4. Chuyển giữa Văn phòng 3D, Giám sát Agent, Kho tài liệu: header giữ nguyên tỷ lệ và không giật khi đổi tab.
5. Trên điện thoại **390×844**, ảnh tự crop hợp lý, không chen nút tài khoản, menu hoạt động.
6. Nhãn `V6.7.4`, cảnh báo thật và trạng thái Drive thật; không có dữ liệu demo.
7. Kiểm tra quyền nhân viên không thấy Cài đặt; Admin vẫn thấy, đăng xuất Streamlit hoạt động.
8. Không có cuộn thừa hay hai vệt đen của bản V6.7.3.
