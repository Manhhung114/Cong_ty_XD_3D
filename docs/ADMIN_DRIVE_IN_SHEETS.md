# Phân quyền Admin và Google Drive trong các sheet (Streamlit)

## Đăng nhập và Admin

Ứng dụng chính: https://congtyxd.streamlit.app/. Người chưa đăng nhập chỉ thấy cổng Google Sign-in.
Máy chủ xác minh email từ Google OIDC. Email được khai báo ở [drive].allowed_email trong Streamlit Secrets là Admin, được nhìn thấy sheet Cài đặt.
Giữ nguyên toàn bộ cấu hình [auth] và [drive] đã hoạt động; không đưa token hoặc secret vào GitHub.

Để cấp quyền cho nhân viên truy cập ứng dụng, trong Streamlit Cloud → Manage app → Settings → Secrets bổ sung:

```toml
[access]
members = ["nhanvien1@example.com", "nhanvien2@example.com"]
```

Tài khoản khác hoặc email chưa được Google xác minh bị từ chối. Nhân viên không thấy sheet Cài đặt. Đây là phân quyền ứng dụng Admin/nhân viên; CHƯA có ACL phân quyền riêng cho từng dự án. Chỉ cấp quyền cho nhân viên tin cậy.

## Tải lên và tải xuống trong sheet

Các sheet Kho tài liệu, BOQ/Dự toán, BIM/Mô hình, Công việc, Phê duyệt và Quản lý dự án có nút Tải tệp lên và Xem hồ sơ / Tải xuống.
Nút gọi hộp thoại Streamlit nổi trên sheet đang sử dụng, không cần mở trang upload riêng.
Người dùng chọn đúng dự án và loại hồ sơ; lần tải lại tạo R01/R02... không ghi đè bản cũ.

## Tệp 500 MB

Streamlit cấu hình maxUploadSize=500. Phần lưu lên Drive dùng MediaIoBaseUpload theo khối 8 MiB và không sao chép toàn bộ nội dung bằng getvalue().
Tuy nhiên file_uploader vẫn nhận tệp vào bộ nhớ của Streamlit; Community Cloud có thể bị giới hạn RAM/timeout nên mức 500 MB cần nghiệm thu trên hosting thật.
Tải xuống qua nút Streamlit hiện áp dụng cho file tối đa 40 MiB. Với file lớn hơn, mở trực tiếp trên Drive (cần quyền truy cập Google). Chưa thể khẳng định mọi nhân viên không có quyền Drive sẽ tải được file lớn.

## Checklist

- Chưa đăng nhập: không hiển thị văn phòng 3D và danh sách hồ sơ.
- Admin đăng nhập: nhìn thấy sheet Cài đặt, email, cấu hình Drive và các nút lưu file.
- Nhân viên trong [access].members: vào app nhưng không thấy Cài đặt.
- Email ngoài danh sách: không vào app.
- Mở BOQ/BIM/Công việc/Phê duyệt và tải file trực tiếp, hộp thoại giữ đúng sheet.
- Upload cùng file hai lần: có R01 và R02.
- Mở, tải xuống file nhỏ; tải file lớn qua Drive.
- Kiểm thử file 25/100/250/500 MB, theo dõi RAM, mạng và quyền Drive.
- Không phân phối APK offline cũ như bản có bảo vệ xác thực Streamlit.

## Trang GitHub Pages

Workflow Pages chỉ phát hành trang chuyển hướng về Streamlit, không phát hành bản app tĩnh không đăng nhập.
