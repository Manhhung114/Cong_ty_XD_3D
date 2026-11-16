# Quản lý tài khoản và phân quyền ngay trong Cài đặt — tham khảo QLDA_ver612_VPS

## Giao diện
Đăng nhập Google vào https://congtyxd.streamlit.app. Chỉ Admin thấy tab **Cài đặt** và thẻ **Quản lý người dùng & phân quyền**. Nhấn **Mở quản lý phân quyền** để hiển thị hộp thoại:
- Danh sách tài khoản, email, vai trò, trạng thái và phạm vi dự án
- Thêm tài khoản, chỉnh sửa họ tên/quyền/phạm vi, tạm khóa
- Thu hồi tài khoản với xác nhận và nhật ký
- Admin gốc lấy từ `[drive].allowed_email` trong Streamlit Secrets và không thể bị xóa trong app

## Các vai trò tương ứng QLDA
| Quyền | Xem, tải xuống Google Drive | Tải tệp lên | Quản lý tài khoản | Tab Cài đặt |
|---|---|---|---|---|
| Chỉ đọc (`read`) | Có, theo dự án | Không | Không | Ẩn |
| Cập nhật (`update`) | Có, theo dự án | Có, theo dự án | Không | Ẩn |
| Admin (`admin`) | Tất cả | Có | Có | Hiện |

Chỉ dùng Google OIDC đã có để xác thực email, **không** thêm biểu mẫu mật khẩu riêng. Phân quyền thực thi ở máy chủ trên từng lần đọc/tải hồ sơ Drive, không chỉ ẩn nút phía trình duyệt. Khi tài khoản bị thu hồi hoặc tạm khóa, lần Streamlit chạy lại sẽ kiểm tra và chặn truy cập.

## Lưu trữ tập trung
Ứng dụng dùng Google Drive OAuth đã thiết lập, lưu tệp cấu hình `_XD_MEP_ACCESS_ROLES_V1.json` trong thư mục gốc Drive (`[drive].root_folder_id`). Không đưa refresh token hay secret xuống frontend và không lưu cấu hình quyền trên GitHub/IndexedDB.

Nếu chưa có tệp cấu hình, danh sách `[access].members` cũ được nạp ở chế độ tương thích với quyền **Cập nhật**. Sau khi Admin lưu thay đổi lần đầu, tệp Drive trở thành nguồn phân quyền duy nhất để bảo đảm tài khoản đã thu hồi không tự quay lại từ Secrets.

**Không xóa** `[drive].allowed_email` và `[auth]`. Google Drive không cần kết nối lại.

## Phạm vi áp dụng và giới hạn
Phân quyền theo dự án được thực thi trên các thao tác Google Drive trong sheet Kho tài liệu, BOQ, BIM, Công việc, Phê duyệt và Quản lý dự án. Phần quản lý dự án/công việc lưu cục bộ trong IndexedDB hiện chưa được chuyển sang backend nhiều người dùng: không nên xem đây là phân quyền hoàn chỉnh cho các dữ liệu cục bộ đó. Admin cần làm tiếp đồng bộ dự án và nhiệm vụ lên máy chủ để thực thi ACL đồng nhất.

Tệp đính kèm Google Drive giữ nguyên giới hạn upload 500 MB đã cấu hình; việc thử tải thực tế gần 500 MB vẫn phụ thuộc tài nguyên Streamlit Cloud.

## Nghiệm thu
1. Admin gốc thấy Cài đặt; tài khoản chưa đăng nhập không vào app.
2. Trong Cài đặt tạo người dùng mới chỉ bằng email Google, chọn Chỉ đọc.
3. Người dùng đăng nhập bằng Google, không thấy Cài đặt, có thể xem/tải nhưng không thể tải lên.
4. Chuyển sang Cập nhật, kiểm thử tải lên đúng dự án đã cấp.
5. Giới hạn một dự án; tài khoản không thể mở tệp của dự án khác qua hộp thoại.
6. Tạm khóa/thu hồi; người dùng bị từ chối ở lần chạy tiếp theo.
7. Admin gốc không thể bị tự xóa, role/chính sách vẫn tồn tại sau khởi động lại ứng dụng.
8. Dữ liệu và các file Drive R01/R02 hiện có không bị xóa hoặc di chuyển.
