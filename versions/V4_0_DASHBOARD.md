# V4.0 — DASHBOARD / QUẢN TRỊ

**Tình trạng:** Dashboard dữ liệu cục bộ, chưa có máy chủ.

## Đã có

- Số Agent, nhiệm vụ đang xử lý, chờ duyệt, số hồ sơ.
- Nhật ký tạo/chuyển việc/upload/xóa file.
- Xuất file JSON chứa dữ liệu nhiệm vụ + metadata hồ sơ; không chứa binary.
- Trang thông tin phiên bản và quyền truy cập cấp demo.

## File riêng phụ trách

- `src/app.js`: dashboard, metrics, sự kiện điều hướng.
- `src/core/export.js`: JSON export.
- `src/core/storage.js`: log & KPI.

## Chưa có

- Đồng bộ theo thời gian thực nhiều máy, tài khoản người dùng, role-based authorization.
- Audit bất biến, tự động sao lưu và khôi phục, dashboard chi phí thực tế.
