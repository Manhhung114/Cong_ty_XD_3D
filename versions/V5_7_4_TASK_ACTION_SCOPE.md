# V5.7.4 – Tập trung thao tác Công việc vào đúng màn hình

## Lý do
Video Android `1000013928.mp4` cho thấy nút `+ Công việc` ở đầu gần như mọi sheet: Văn phòng 3D, Nhân viên AI, Công việc, Cài đặt, BOQ/Dự toán, Pháp luật & tiêu chuẩn, các phiên bản. Trang Quản lý dự án còn lặp cả form tạo nhiệm vụ và danh sách công việc.

## Quy tắc giao diện
- **Công việc:** điểm duy nhất để **tạo mới, bắt đầu, cập nhật, gửi báo cáo** và xem toàn bộ nhiệm vụ của dự án đang chọn.
- **Chờ phê duyệt:** xem nội dung, phê duyệt/trả lại những nhiệm vụ chờ duyệt; không có nút tạo nhiệm vụ.
- **Quản lý dự án:** tạo/chọn dự án, theo dõi số công việc, số hồ sơ, số chờ duyệt; không có form nhiệm vụ hoặc danh sách nhiệm vụ chi tiết.
- **Văn phòng 3D:** chỉ xem nhiệm vụ gắn với phòng đã chọn, không có nút tạo nhiệm vụ lặp.
- **Nhân viên AI / Kho tài liệu / BOQ / BIM / Pháp luật / Cài đặt / Nhật ký / Phiên bản:** không có nút `+ Công việc` lặp ở đầu trang.
- **Số liệu tổng hợp:** vẫn hiển thị nơi cần quan sát; khi cần xử lý, người dùng vào sheet Công việc.

## Dữ liệu
Không sửa cơ chế lưu trữ, không xóa bất kỳ dự án/nhiệm vụ/hồ sơ/revision nào. Cơ chế phê duyệt và API Settings giữ nguyên.

## Nghiệm thu
1. Chỉ trang Công việc có form `localCreateTask`.
2. Trang Quản lý dự án chỉ có form `localCreateProject` và tổng hợp, không có `localCreateTask`.
3. Không tồn tại `newTaskBtn` toàn cục trong HTML/JS.
4. Công việc có thể tạo mới, gửi duyệt và xem lịch sử như trước.
5. Tiếng Việt và English không xuất hiện nút tạo nhiệm vụ trên các sheet không liên quan.
