# HƯỚNG DẪN CHẠY V5.6–V5.7 (WEB + ANDROID)

## Cài máy chủ dùng thử nội bộ

1. Cài Python 3.11+, vào thư mục dự án và chạy `python -m pip install -r backend/requirements.txt`.
2. Tạo tài khoản quản trị qua `python -m backend.bootstrap_admin`. Nhập mật khẩu riêng >=12 ký tự tại dấu nhắc (không được commit mật khẩu).
3. Chạy `RUN_SERVER_V57.bat` trên Windows hoặc `sh RUN_SERVER_V57.sh` trên Linux/macOS.
4. Mở `http://127.0.0.1:8766` → **Quản lý dự án** → đăng nhập. Đăng ký dự án, tài khoản, quyền và giao việc.
5. `/api/health` cho biết trạng thái; `/api/docs` là mô tả REST API.

**Lưu ý:** `RUN_WEB_3D.bat` cũ chỉ khởi tạo web demo tĩnh; để có `/api` thật phải chạy `RUN_SERVER_V57.bat`. Không chạy hai tiến trình cùng cổng 8766.

## Quản lý và phê duyệt

- Vào **Tài khoản & quyền**: admin tạo tài khoản, chọn dự án và gán thành viên theo vai trò/khối.
- Vào **Quản lý dự án**: tạo nhiều dự án, chọn dự án, giao nhiệm vụ và tải hồ sơ; mỗi mã hồ sơ có revision riêng trong từng dự án.
- Người kỹ sư/người quản lý gửi báo cáo nhiệm vụ (>=12 ký tự); QA, trưởng bộ môn và PM đăng nhập tài khoản riêng để duyệt từng cấp.
- Nút nhập nhiệm vụ demo cần xác nhận: không tự đưa trạng thái duyệt cũ lên máy chủ. Tệp nhị phân phải tải lên riêng.

## Triển khai Internet và điện thoại

- Dùng PostgreSQL qua `DATABASE_URL` và **kho tệp có lưu trữ bền vững** (volume hoặc S3 adapter khi triển khai), HTTPS reverse proxy, sao lưu database/file.
- Đặt `DOCUMENT_STORAGE_DIR` vào volume không mất dữ liệu khi redeploy.
- Có thể build `Dockerfile` trên Railway/Docker; repository KHÔNG tự deploy và GitHub Pages chỉ phục vụ giao diện tĩnh.
- Android giữ `applicationId=vn.congtyxd3d.app`, `versionCode=57`. Để cập nhật đè, tiếp tục dùng đúng chữ ký release bí mật của V5.5.
- Khi dùng APK WebView, vào **Quản lý dự án** để cấu hình URL gốc `https://...` của backend; server cho phép origin nội bộ `https://appassets.androidplatform.net` theo CORS đã định.
- Không đưa dự án thật lên môi trường demo nếu chưa bảo đảm xác thực MFA, kho tệp an toàn, kiểm tra malware và backup/restore.

## Đã có / Chưa có

- Đã có: CRUD dự án, tài khoản, phân quyền, giao việc, ba cấp duyệt, lưu hồ sơ revision, theo dõi tài liệu theo dự án, audit API, cấu hình agent **không gồm khóa**.
- Chưa có: AI Agent gọi model thật, BIM IFC viewer, DWG engine, S3 adapter, email thông báo, quy trình chữ ký số pháp lý.
