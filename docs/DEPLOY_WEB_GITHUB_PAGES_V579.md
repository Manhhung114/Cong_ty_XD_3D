# Hướng dẫn triển khai website Công ty XD & MEP AI 3D V5.7.9

> Website thử nghiệm: giao diện 3D + dự án và hồ sơ lưu trong trình duyệt. Không phải Streamlit. Chưa có backend/AI thực và chưa đồng bộ dữ liệu giữa web và APK.

## Một lần: bật GitHub Pages

1. Truy cập https://github.com/Manhhung114/Cong_ty_XD_3D/settings/pages bằng tài khoản có quyền quản trị repository.
2. Ở **Build and deployment → Source**, chọn **GitHub Actions**. Nếu đang chọn `Deploy from a branch`, chuyển sang `GitHub Actions`.
3. Mở https://github.com/Manhhung114/Cong_ty_XD_3D/actions/workflows/pages.yml.
4. Chọn **Run workflow → Branch: main → Run workflow**.
5. Mở workflow mới nhất, xác nhận **Verify web application**, **Upload static website** và **Deploy GitHub Pages** đều xanh.
6. Mở **Settings → Pages → Visit site**. Địa chỉ dự kiến của project Pages là https://manhhung114.github.io/Cong_ty_XD_3D/ (chỉ sử dụng sau khi workflow thành công).

## Dùng điện thoại Android để kiểm tra

- Mở địa chỉ website bằng Chrome.
- Chọn Văn phòng 3D → MEP / Xây dựng; kiểm tra chọn đúng phòng và 18 AI Agent chung.
- Chọn Dự án → tạo một dự án thử; Công việc → tạo công việc; Chờ phê duyệt → gửi báo cáo và duyệt nội bộ.
- Chọn Pháp luật & tiêu chuẩn → thống kê, STT, nguồn VBPL/VSQI, Cập nhật TVPL; thử Việt–Anh.
- Chọn Cài đặt để xem cấu hình; không nhập API key thật trong lần thử công khai.
- Có thể bấm Chrome (⋮) → Thêm vào màn hình chính để tạo lối tắt (đây không phải APK/PWA offline hoàn chỉnh).

## Nếu lỗi

- `Resource not accessible by integration` tại `configure-pages`: Pages chưa được chủ repository bật. Vào Settings → Pages chọn GitHub Actions rồi chạy lại.
- `404` ở URL: xem trạng thái workflow; sau khi xanh, mở lại bằng tab ẩn danh hoặc tải lại trang.
- Trắng màn hình: vào Actions xem lỗi kiểm thử/đóng gói; đối chiếu `index.html`, `src/app.js`, `data/legal` và `assets`.
- Nút cập nhật TVPL không có mục mới: dữ liệu cập nhật phụ thuộc workflow nguồn; không được coi là đã quét thành công nếu workflow chưa chạy.

## Giới hạn và bảo mật

- Không dùng dữ liệu dự án thực, tài liệu khách hàng hoặc API key thật ở bản thử nghiệm công khai.
- `localStorage` và `IndexedDB` thuộc từng trình duyệt / thiết bị / origin. Website không nhìn thấy dữ liệu đã lưu trong APK Android.
- Sao lưu JSON trong ứng dụng chỉ chứa metadata, không chứa nhị phân hồ sơ; cần tải riêng từng tệp gốc.
- Các Agent mới có giao diện và cấu hình model, chưa thực hiện tính toán AI kỹ thuật thực.
- Chỉ chạy mã web từ nhánh `main`; workflow xuất bản `index.html`, `src`, `assets`, `data/legal`, `data/templates`. Không xuất bản backend, `.env`, cấu hình server hay kiểm thử.