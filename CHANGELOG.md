# CHANGELOG — MEP AI Company 3D

## 2026-11-15 — Initial prototype V1.0–V4.0 foundation

- V1.0: tạo văn phòng WebGL gồm 8 phòng ban/10 avatar, chức năng chọn phòng/nhân viên, camera xoay/zoom, SVG isometric dự phòng.
- V2.0: mô hình các Agent, danh sách nhiệm vụ, Kanban, cập nhật tiến độ và nhật ký; có nút mô phỏng, **không chạy AI thật**.
- V3.0: tài liệu tách category, revision tăng theo mã, tệp gốc trong IndexedDB; BOQ CSV mẫu và tính tổng đơn giản. BIM chưa có viewer.
- V4.0: dashboard số lượng công việc, số file, số Agent, xuất metadata JSON, trang roadmap.
- Tests: 6/6 core PASS. Các chức năng WebGL thực và IndexedDB trên thiết bị chưa nghiệm thu.

## Quy tắc phát hành tương lai

- Đưa code mới vào đúng module `src/core/` hoặc `src/3d/` thay vì sửa tất cả trong một file.
- Bổ sung ghi chú thay đổi trong `versions/V*_*.md` tương ứng và CHANGELOG.md.
- Tạo Git tag mới (ví dụ `v1.1.0`) sau khi test; không sửa tag đã phát hành.
- Hồ sơ khách hàng không commit lên GitHub public.
