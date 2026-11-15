# V1.0 — VĂN PHÒNG 3D

**Tình trạng:** Prototype chức năng (cần nghiệm thu WebGL trên máy thật).

## Đã dựng

- Toàn bộ 8 phòng ban MEP, 10 nhân viên avatar bố trí theo phòng.
- Camera xoay bằng kéo chuột/touch, zoom bằng bánh xe, chọn phòng và chọn Agent để cập nhật thanh thông tin.
- Màn hình thể hiện status của Agent từ các nhiệm vụ (có/không có nhiệm vụ đang làm hoặc chờ duyệt).
- Nếu WebGL không dùng được, hiển thị một phối cảnh isometric SVG có thể click vào phòng.

## File riêng phụ trách

- `src/3d/scene.js`: engine 3D và SVG fallback.
- `src/core/config.js`: phòng, vị trí, tên, màu, Agent.
- `src/styles.css`: giao diện, responsive.

## Chưa có

- Avatar chuyển động phức tạp, walk animation, phòng họp thực, hệ thống 3D thương mại.
- Texture PBR, GLTF, ánh sáng vật lý hoặc VR.

## Tiêu chí kiểm tra

1. Mở web: màn hình có 8 phòng, 10 người.
2. Click Điện, HVAC và QS: inspector đổi đúng phòng.
3. Kéo và cuộn trong canvas: góc nhìn và tỷ lệ thay đổi (WebGL).
4. Trên trình duyệt tắt WebGL: SVG dự phòng có thể chọn phòng.
