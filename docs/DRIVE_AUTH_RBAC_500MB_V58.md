# V5.8 – Google Drive tích hợp vào từng sheet và phân quyền

## Đăng nhập và quyền truy cập
- Streamlit xác thực bằng Google OIDC thông qua phần [auth] Secrets hiện có.
- Trang Streamlit không tải giao diện 3D hoặc kết nối Drive khi chưa đăng nhập.
- Admin là email khớp chính xác với [drive].allowed_email đã xác minh.
- Có thể thêm nhân viên qua danh sách [access].members trong Streamlit Secrets.
- Nhân viên không thấy mục "Cài đặt"; đường truy cập Drive được kiểm tra lại trên server.
- Giới hạn hiện tại: mọi tài khoản nhân viên đã allowlist đều có quyền xem/tải lên
  các dự án trong thư mục gốc. Chưa có RBAC theo *từng dự án*.

Ví dụ chỉ cho nhân viên, không chứa bí mật:

    [access]
    members = ["nhanvien1@example.com", "nhanvien2@example.com"]

Không sửa hoặc chia sẻ [auth] / [drive] Secrets cũ. 
Không đưa refresh_token vào repo.

## Tác vụ trong các sheet
- Quản lý dự án: thông tin dự án, hợp đồng, pháp lý, tiến độ, hình ảnh, nhật ký.
- Kho tài liệu: bản vẽ MEP/Xây dựng, PCCC, BOQ, BIM, hợp đồng và báo cáo.
- BOQ / Dự toán: BOQ MEP và BOQ Xây dựng.
- BIM / Mô hình: BIM MEP và BIM Xây dựng.
- Công việc: công việc và báo cáo.
- Chờ phê duyệt: hồ sơ phê duyệt và báo cáo.

Ở mỗi sheet, nút "Tải tệp lên" và "Xem hồ sơ / Tải xuống" mở
hộp thoại Streamlit ngay trên app qua postMessage + Streamlit components v2.
Không có trang tải tệp riêng.

## 500 MB
- [server].maxUploadSize=500 và uploader max_upload_size=500.
- Sử dụng MediaIoBaseUpload resumable với chunk 8 MB.
- Không dùng .getvalue() để sao chép thêm tệp 500 MB khi upload.
- Mỗi lần tải tạo tệp revision R01/R02/... thay vì ghi đè bản trước.
- Trên Community Cloud, giới hạn bộ nhớ và thời gian tải mạng vẫn có thể khiến
  tệp 500 MB thất bại; cần thử tệp lớn và cân nhắc hosting riêng.
- Tải xuống trong app qua proxy cho tệp <=40 MB. Với tệp lớn, mở
  Google Drive để tải trực tiếp, cần tài khoản có quyền Drive.

## Bảo mật
- Không phát hành dữ liệu dưới /app/static: enableStaticServing=false.
- Bộ dựng HTML nhúng danh mục tiêu chuẩn và mẫu biểu công khai.
- Không lộ Google OAuth token trong iframe. Admin-only Settings là ẩn UI;
  chức năng lưu Drive được xác thực lại phía Python.
- Google Drive được truy cập với token của admin ở server, vì vậy mọi thành viên
  allowlist có quyền file chung; không dùng dữ liệu khách hàng nhạy cảm cho đến
  khi có phân quyền riêng từng dự án, nhật ký audit và kiểm thử bảo mật.

## Kiểm thử
`python -m unittest discover -s tests -p 'test_*.py' -v`
`npm test`
Kiểm thử bằng GitHub Actions `test-streamlit-drive.yml`.

## Kiểm tra sau khi deploy
1. Trên Streamlit Community Cloud Reboot app.
2. Dùng cửa sổ ẩn danh: chưa login không được xem app.
3. Login Admin: có Cài đặt, có nút Drive ở các sheet.
4. Login tài khoản nhân viên được allowlist: không thấy Cài đặt.
5. Tải tệp thử nhỏ lên S234, kiểm tra đúng nhóm hồ sơ; tải R02.
6. Tải xuống và thử tệp lớn dần, lưu ý hạn mức Cloud.
