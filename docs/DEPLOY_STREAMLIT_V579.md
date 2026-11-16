# Triển khai XD & MEP AI 3D V5.7.9 trên Streamlit Community Cloud

## Tạo website
1. Đăng nhập https://share.streamlit.io bằng tài khoản GitHub có quyền repository.
2. Create app → I have an app → repository `Manhhung114/Cong_ty_XD_3D`.
3. Branch `main`; main file path `streamlit_app.py`.
4. Chọn Deploy và mở URL do Streamlit cấp.
5. Trên điện thoại, dùng nút **Mở văn phòng 3D toàn màn hình**.

## Kỹ thuật
- `streamlit_app.py` dùng iframe để nhúng trang HTML/JS trong `static/index.html`.
- `.streamlit/config.toml` bật `enableStaticServing = true`.
- `static/src`, `static/assets` và `static/data` là bản công khai của web gốc; không chứa backend/secret.
- Khi thay đổi web gốc, đồng bộ cả bản `static/` để Streamlit cập nhật đúng giao diện.
- Cập nhật GitHub `main` sẽ kích hoạt Streamlit Cloud cập nhật, có thể Reboot nếu cần.

## Giới hạn bảo mật và lưu trữ
- Đây là web thử nghiệm lưu dự án/nhiệm vụ ở localStorage/IndexedDB của từng trình duyệt.
- Bản nhúng và bản mở toàn màn hình có thể khác vùng lưu trữ; không giả định dữ liệu tự chuyển qua lại.
- Không tải hồ sơ khách hàng nhạy cảm và không lưu API key vào repository công khai.
- Chưa có backend quản lý tài khoản, đồng bộ nhiều thiết bị hoặc xử lý AI thật.

## Chạy cục bộ
1. `python -m pip install -r requirements.txt`
2. `streamlit run streamlit_app.py`
3. Mở `http://localhost:8501`.
