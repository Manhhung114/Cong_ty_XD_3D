# CHANGELOG — Công ty Xây dựng & MEP AI 3D

## 2026-11-15 — V5.2 WebGL ba tầng và điều khiển camera

- Cảnh WebGL 3 tầng (MEP + Xây dựng + điều hành), bàn họp, màn hình, nội thất và nhân vật hoạt động theo trạng thái nhiệm vụ.
- Bộ điều khiển camera, zoom và lựa chọn chất lượng hiển thị. Tối ưu tần suất render trên điện thoại.
- Chuẩn bị workflow xuất bản GitHub Pages; không đồng nghĩa đã online.
- Giữ nguyên quản lý công việc, hồ sơ, BOQ và revision.

## 2026-11-15 — V5.1 Phối cảnh 3D cao cấp

- Bổ sung ảnh isometric 3 tầng có phòng ban MEP và Xây dựng, khu giám đốc, phòng họp và bảng điều hành trung tâm.
- Bổ sung 16 điểm chọn phòng trên phối cảnh; giữ liên kết với inspector và dữ liệu công việc.
- Chế độ “Phối cảnh chi tiết” mặc định; giữ nút “3D tương tác” (WebGL) và chế độ dự phòng SVG.
- Tối ưu vuốt ngang khi xem trên điện thoại; giữ nguyên BOQ, bản vẽ, revision và nhiệm vụ đang lưu.
- Ảnh phối cảnh là hình dựng minh họa, **không phải mô hình WebGL 3D**; AI vẫn là mô phỏng.

## 2026-11-15 — V5.0: Bổ sung nhánh Xây dựng

- Thêm 8 phòng chuyên môn Xây dựng, 8 Agent ảo và 6 nhiệm vụ demo; giữ khối MEP, tổng 16 phòng/18 Agent.
- Mở rộng văn phòng WebGL/SVG thành 2 tầng có chế độ xem toàn công ty / từng khối.
- Phân khối hồ sơ và revision độc lập cho MEP và Xây dựng; thêm 5 mẫu CSV và cây thư mục XD_PROJECT_001.
- Hai bảng BOQ demo riêng. Đã thêm migration localStorage cho nhiệm vụ cũ; không xóa hồ sơ đã lưu.
- AI thực, BIM IFC viewer và tự tính toán vẫn chưa triển khai.


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
