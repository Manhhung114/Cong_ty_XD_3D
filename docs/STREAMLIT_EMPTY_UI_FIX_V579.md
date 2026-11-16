# Streamlit hotfix: giao diện trống (V5.7.9)

Trang có khung HTML/CSS nhưng menu và văn phòng 3D không hiển thị do trình duyệt chưa chạy module JS.

Khắc phục: `streamlit_app.py` gọi `scripts.build_streamlit_inline.build()` để tạo `static/standalone.html` khi khởi động Streamlit. Tệp này nhúng các JS module (gồm ảnh phối cảnh) bằng data URL và CSS trực tiếp; JSON pháp luật vẫn tải từ `static/data/` qua fetch. Không còn phụ thuộc MIME `.js` từ máy chủ.

Ứng dụng không tự động tải hồ sơ khách hàng lên server hoặc đưa API key vào mã nguồn. Dữ liệu dự án vẫn lưu trong trình duyệt; nên chọn **Mở văn phòng 3D toàn màn hình** trên Android để tránh các hạn chế lưu trữ trong iframe.

Triển khai:
1. Đồng bộ tệp sửa lên GitHub `main`.
2. Streamlit Community Cloud → Manage app → Reboot.
3. Sau khi Streamlit chạy lại, nhấn **Mở văn phòng 3D toàn màn hình**.
4. Nhấn Ctrl+Shift+R hoặc thử tab ẩn danh nếu trang còn cache bản cũ.

Kiểm thử: npm test (79/79), pytest tests/test_streamlit_inline.py tests/test_streamlit_package.py (6/6); thử giao diện trên Chromium ở chế độ mô phỏng dữ liệu và localStorage.
