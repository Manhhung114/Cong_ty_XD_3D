# Sửa lỗi Thư viện Pháp luật trên Streamlit – V5.7.9

Ngày cập nhật: 16/11/2026.

## Vấn đề
Trang Pháp luật & tiêu chuẩn có thể chỉ hiện 'Không tải được nội dung trang'.
Đây là thông báo bắt lỗi ở lớp giao diện, chưa đủ để kết luận nguyên nhân thật.
Bộ nhớ cache HTML/JS của Streamlit có thể giữ bundle cũ sau khi mã nguồn thay đổi.

## Đã sửa
- streamlit_app.py không còn cache HTML đã bundle bằng @st.cache_data.
- Trang Pháp luật có chế độ hiển thị an toàn khi bảng nâng cao phát sinh exception.
- Chế độ an toàn giữ số hiệu, tên, lĩnh vực, STT, liên kết nguồn và nút cập nhật TVPL/TCVN.
- Thêm mục 'Thông tin kiểm tra' có thể mở để xem lỗi nếu vẫn xảy ra.
- Không thay đổi hồ sơ, dữ liệu dự án hay kho QLDA_ver612_VPS.

## Nghiệm thu
- npm test: 79/79 PASS (hai bài thử cũ được cập nhật để chấp nhận dữ liệu đã làm sạch).
- unittest: 11/11 PASS.
- Chromium: Trang bình thường hiển thị 42 mục; khi tạo lỗi nhân tạo, chế độ an toàn vẫn có 42 dòng và nút TVPL.

## Hướng dẫn triển khai
1. Đưa thay đổi lên nhánh main của Manhhung114/Cong_ty_XD_3D.
2. Streamlit Community Cloud → congtyxd → Manage app → Reboot.
3. Chrome nhấn Ctrl+Shift+R (điện thoại tải lại trang).
4. Mở Pháp luật & tiêu chuẩn; kiểm tra số liệu, bảng, STT, các nút.
5. Nếu vẫn bị lỗi, mở 'Thông tin kiểm tra' và gửi dòng lỗi cho người phát triển.

Lưu ý: Không tuyên bố đã nghiệm thu trên Streamlit Cloud trước khi kiểm tra site công khai.
