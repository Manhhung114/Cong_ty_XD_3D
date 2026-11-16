# Sửa màn hình trống Streamlit – V5.7.9 (16/11/2026)

## Hiện tượng

Streamlit trên congtyxd.streamlit.app khởi chạy Python nhưng chỉ có khung HTML nền;
không hiển thị menu và văn phòng 3D. Video ngày 16/11/2026 cho thấy không phải
lỗi khởi động Python mà là lỗi hiển thị JavaScript trong iframe.

## Cách sửa

- Không dùng `components.iframe("app/static/standalone.html")`.
- Không dùng các ES-module import `data:text/javascript` của bản hotfix trước.
- `scripts/build_streamlit_runtime_v2.py` chuyển các ESM nội bộ thành một script
  inline cổ điển, nhúng CSS và ảnh phối cảnh vào HTML. Không nhúng bí mật.
- `streamlit_app.py` truyền HTML tin cậy trực tiếp cho `st.iframe` hoặc
  `components.html` để JavaScript thực thi bên trong iframe của Streamlit.
- Đường dẫn dữ liệu JSON trỏ về `/app/static/` qua phần tử `<base>`.
- Liên kết mở rộng `/?embed=true` quay về chính Streamlit (không mở trang
  tĩnh chưa chắc cho phép JavaScript).

## Kiểm tra

- `python -m unittest tests.test_streamlit_inline_v2 -v`
- `python -m unittest tests.test_streamlit_package -v`
- Trên Streamlit Community Cloud: Manage app → Reboot; sau đó Ctrl+Shift+R.
- Kiểm tra 11 mục menu, 4 thẻ thống kê, Văn phòng 3D, Công việc và
  Pháp luật & tiêu chuẩn → TVPL.

Các bài kiểm thử Chromium cục bộ dùng iframe `srcdoc` đã hiển thị 11 menu,
4 thẻ thống kê, bảng pháp luật và không báo lỗi JavaScript. Chưa thể khẳng định
website Streamlit đã sửa hoàn toàn khi chưa kiểm tra bản triển khai trên Cloud.

Lưu ý: dữ liệu dự án vẫn ở localStorage/IndexedDB theo từng trình duyệt.
Không dùng tệp hồ sơ khách hàng thực trên bản web công khai chưa có xác thực.