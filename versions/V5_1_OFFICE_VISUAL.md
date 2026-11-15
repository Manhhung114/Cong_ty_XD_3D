# V5.1 – Văn phòng ảo 3D theo ảnh mẫu

## Mục tiêu
Làm lại phần trình bày văn phòng theo phong cách isometric ba tầng, có nhân viên tại bàn làm việc, phòng họp, cây xanh, màn hình dự án và bảng điều hành trung tâm.

## Đã thực hiện
- Thêm `assets/office_xd_mep_isometric_v5_1.webp`.
- Thêm `src/3d/illustrated.js`: 16 điểm chọn phòng có hỗ trợ thao tác bàn phím.
- Thêm bộ chọn chế độ **Phối cảnh chi tiết** và **3D tương tác**.
- Chế độ WebGL (`src/3d/scene.js`) vẫn được giữ nguyên, không xóa hành vi xoay/zoom/chọn Agent.
- Thiết kế có thể vuốt ngang trên điện thoại.
- Quản lý phiên bản chọn qua `officeRenderMode`; không reset các tác vụ/BOQ/hồ sơ cũ.

## Giới hạn / nghiệm thu
- Phối cảnh chất lượng cao là ảnh tĩnh 3D isometric có hotspot, **không phải mesh WebGL**.
- Chế độ WebGL hiện vẫn là mô hình low-poly từ V5.0.
- Không nhận diện tự động đối tượng trong ảnh; các điểm chọn phòng được gán thủ công.
- 18 Agent hiện mô phỏng, chưa xử lý chuyên môn bằng LLM.
- Cần kiểm thử tiếp trên thiết bị Android thật trước khi coi là nghiệm thu cuối.
