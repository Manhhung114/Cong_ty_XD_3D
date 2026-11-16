# Google Drive: Kho hồ sơ XD & MEP AI 3D

Mở tài liệu chi tiết: [Kết nối Google Drive từ Streamlit](GOOGLE_DRIVE_CONNECT_STREAMLIT.md).

**Bản cập nhật:** phần tải tệp đặt ở **đầu trang Streamlit**, không còn nằm trong sidebar bị ẩn.
Chỉ tài khoản Google được cho phép mới được tạo thư mục hoặc ghi dữ liệu.

Thư mục gốc đã tạo: `CONG_TY_XD_MEP_AI_3D`
- `00_DUNG_CHUNG`: Pháp luật, TCVN/QCVN, biểu mẫu, quản trị
- `01_DU_AN`: mỗi dự án một thư mục riêng, gồm 13 nhóm hồ sơ
- `99_SAO_LUU`: dự án và danh mục

Dự án hiện có: `S234_SUNSHINE_SKY_CITY` (13 thư mục, chia MEP/Xây dựng ở Bản vẽ, BOQ, BIM, Báo cáo).

**Chưa tự động đồng bộ từ iframe 3D sang Drive.** Chức năng hiện tại là người quản trị
chọn dự án, nhóm hồ sơ, tệp rồi bấm **Lưu tệp lên Google Drive** trên Streamlit.
Google Drive kết nối với ChatGPT không truyền OAuth sang Streamlit.

Quy tắc: không lưu mật khẩu/API key trên GitHub, không cho ghi tệp khi chưa đăng nhập,
không cho chọn ID thư mục bên ngoài cây dự án, không ghi đè các revision trước đó.
Mỗi lần tải một tệp cùng tên được tạo phiên bản `_R01`, `_R02`…

Kiểm thử logic: `python -m unittest discover -s tests -p 'test_drive*.py' -v`.
