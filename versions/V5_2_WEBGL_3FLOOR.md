# V5.2 — Văn phòng 3D WebGL ba tầng / bộ điều khiển camera

- Giữ nguyên V5.1, các điểm chọn phòng, 18 Agent mô phỏng, dữ liệu và mã revision.
- Nâng cảnh WebGL thành hai tầng chuyên môn MEP/Xây dựng cùng tầng ba phòng điều hành và họp chung. Tầng mới không tạo Agent giả.
- Góc nhìn phối cảnh, mặt trước, từ trên, tập trung MEP hoặc Xây dựng; zoom in/out, chế độ tiết kiệm pin trên điện thoại.
- Gắn trạng thái nhân vật với nhiệm vụ đang lưu; vẫn là hoạt cảnh mô phỏng, KHÔNG có backend AI thật.
- Kết nối GitHub Pages được chuẩn bị bằng workflow, chỉ coi web công khai là hoạt động sau khi kiểm tra deployment thực tế.

## Kiểm thử
- `npm test` và `node --check` trên tệp JS.
- Manual: chuyển từ phối cảnh tĩnh sang WebGL, thử các camera, zoom, mobile, chọn phòng và xem Agent/task.
- Cần nghiệm thu trên điện thoại thật, đặc biệt WebGL và IndexedDB khi dùng hồ sơ dung lượng lớn.
