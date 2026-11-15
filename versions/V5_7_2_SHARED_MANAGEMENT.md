# V5.7.2 – Ban điều hành chung MEP và Xây dựng

Ngày: 15/11/2026. Cập nhật từ yêu cầu kiểm tra video Android `1000013923.mp4`.

## Thay đổi

- Gỡ mục `Khối Xây dựng` ra khỏi thanh menu. Hai bộ môn MEP/Xây dựng được chọn ngay trong `Văn phòng 3D` hoặc `Nhân viên AI`, tương đương nhau.
- `Giám đốc công ty` (CEO) và `Trưởng ban quản lý dự án` (PM) dùng chung cho cả hai lĩnh vực qua `dept=director`, **không nhân đôi tài khoản/Agent**.
- `Toàn công ty`: 18 Agent, 16 phòng; `MEP`: 10 Agent / 8 phòng (7 MEP + 1 chung); `Xây dựng`: 10 Agent / 9 phòng (8 XD + 1 chung).
- Chế độ phối cảnh/3D của cả MEP và XD đều hiển thị phòng Ban giám đốc dùng chung khi lọc riêng.
- Giữ lựa chọn bộ môn khi chuyển trang. Chức năng điều hướng cũ tới `construction` được chuyển sang `overview` kèm lọc Xây dựng.
- Không xóa hay chuyển đổi dữ liệu dự án, người dùng, quyền, công việc, hồ sơ hoặc các revision.
- Đồng bộ tiêu đề/ghi chú mới sang VI/EN.

## Nghiệm thu

- Menu trái chỉ có một `Văn phòng 3D`, không có `Khối Xây dựng` riêng.
- Bộ lọc Nhân viên AI: MEP = 10, Xây dựng = 10, Toàn công ty = 18 (mỗi CEO/PM xuất hiện một lần theo bộ lọc).
- Chạm vào Ban giám đốc trên phối cảnh Xây dựng: hiện đúng 2 nhân sự điều hành.
- Chuyển EN/VI không làm biến mất hai vị trí dùng chung.
- Kiểm thử web, backend và các tương tác trình duyệt phải đạt. WebGL thực và cập nhật APK chưa thay cho nghiệm thu trên Android thật.
