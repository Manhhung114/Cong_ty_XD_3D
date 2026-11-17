# V6.7.5 – Header Visibility Fix (17/11/2026)

## Lỗi đã xác định

Ảnh chụp sau V6.7.4 cho thấy chỉ còn phần mái và vài đường kiến trúc; **file không mất**. Asset cũ `premium_skyline_v674.svg` có tỉ lệ 3200×420, nhưng header chỉ cao khoảng 64 px. Với `background-size:cover`, trên màn 1910 px bức ảnh chiếm chiều cao khoảng **251 px**; khung 64 px cắt mất phần lớn mặt tiền ở phía dưới.

Chỉ giảm độ tối và chuyển `background-position` không thể luôn đảm bảo nhìn thấy cả mái và tầng trệt ở các độ phân giải. Dùng `background-size:100% 100%` lại làm dẹt tòa nhà. **Bản V6.7.5 dùng cách sửa tận gốc: tạo asset panoramic theo tỷ lệ khung header.**

## Thay đổi đã triển khai

- **`static/assets/premium_header_visible_v675.svg`**: panorama SVG mới 3200×120, thiết kế riêng cho header, thể hiện trọn mái, mặt tiền kính, đèn tầng trệt, cửa chính và cảnh quan trong cùng một dải; dùng SVG vector để không mờ trên màn hình Retina.
- **`src/core/command_shell.js` và `static/src/core/command_shell.js`**: khai báo biến `--xd-visible-header` trỏ đến asset mới, được nhúng vào iframe sau khi xác thực Google; vẫn giữ logo và minh họa sidebar hiện tại.
- **`src/polish.css` và `static/src/polish.css`**: dùng asset mới cho thanh tiêu đề và topbar; lớp phủ giảm xuống ~8% ở chính giữa nhưng vẫn tối hai đầu để chữ và các nút dễ đọc. Dùng `background-size:cover` để giữ tỉ lệ, đặt tâm ảnh ở 50%. Các breakpoint desktop/laptop/mobile áp dụng cùng tài nguyên.
- **`static/index.html`**: cập nhật nhãn V6.7.5.
- **Kiểm thử**: kiểm tra vị trí mái/tầng trệt trong vùng 64 px ở màn 1910×898; mặt tiền nằm trọn ở laptop 1366 px; bundler tự nhúng SVG; giữ nguyên phân quyền, OAuth và dữ liệu ứng dụng.

## Vì sao cách này không mất tòa nhà nữa?

Với tỉ lệ 3200×120, trên màn 1910px, `cover` chỉ tạo chiều cao ~71,6px: khung 64px cắt trên/dưới tổng cộng khoảng 7,6px. Mái ở cao độ 22 và mặt tiền kết thúc ở cao độ 108 của SVG, **đều nằm trong vùng hiển thị**. Ở màn 1366px, chiều cao ảnh hiển thị 64px, ảnh bị cắt nhẹ hai bên chứ không cắt thân tòa nhà.

## Quy trình nghiệm thu

1. Mở `https://congtyxd.streamlit.app/`, làm mới cứng bằng `Ctrl+Shift+R` sau khi deploy.
2. Ở **1910×898**, ảnh header trải ngang, mái và tầng kính đều thấy rõ; không còn cảnh chỉ thấy mái.
3. Ở **1366×768**, ảnh công trình đầy đủ, không chen vào text/Google Drive/avatar; các nút vẫn hoạt động.
4. Ở **390×844**, trung tâm ảnh vẫn thấy tòa nhà, chữ và avatar rõ, không tràn chiều ngang.
5. Chuyển Văn phòng 3D → Giám sát Agent → Kho tài liệu để bảo đảm header đúng trên mọi sheet.
6. Đăng nhập Member: Cài đặt ẩn; Admin: Cài đặt hiện. Thử cảnh báo, logout, quản lý Google Drive.
7. Không có dữ liệu nghiệp vụ hoặc chữ trên ảnh bị giả lập: ảnh chỉ là trang trí kiến trúc.

**Lưu ý:** Giải pháp đã thay asset/crop và kiểm thử tự động, nhưng vẫn cần nghiệm thu trình duyệt thực tế trên tài khoản đã đăng nhập. Đừng coi CI PASS là kết quả xác nhận giao diện trực quan tuyệt đối.
