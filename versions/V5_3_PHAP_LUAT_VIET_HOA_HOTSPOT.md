# V5.3 – Chuẩn hóa tiếng Việt, điểm chọn phòng và thư viện văn bản pháp luật

- Đối chiếu video 1000013906.mp4 (15/11/2026), sửa tọa độ 14 điểm phòng trong ảnh phối cảnh.
- Hai phòng QA/QC MEP và Quản lý hiện trường XD chưa có vị trí minh họa riêng; tách thành nút chọn rõ ràng, **không gắn nhầm vào phòng họp**.
- Ẩn nhãn nổi của các điểm chọn trên di động để tránh che hình ảnh; chỉ phòng đang chọn hiện ở bảng thông tin.
- Chuẩn hóa chữ hiển thị/18 tên nhân viên sang tiếng Việt (giữ chữ viết tắt chuẩn MEPF, BOQ, BIM, AI, WebGL).
- Thư viện pháp lý gồm 29 mục trong `data/legal/`, chia 2 lĩnh vực MEPF/PCCC và Xây dựng/QLDA, mỗi mục lưu URL nguồn nhà nước hay VSQI.
- Những tiêu chuẩn đã được thay thế (ví dụ TCVN 5738:2021) đánh dấu rõ, không đưa vào danh sách hiện hành.
- Sheet Excel có cột nguồn và ngày rà soát; phục vụ tra cứu, **không khẳng định hiệu lực tuyệt đối** khi áp dụng cho dự án đặc thù.
- Không chạm dữ liệu người dùng trong IndexedDB/localStorage; không làm thay đổi danh sách nhiệm vụ và revision.
