# V7.0.0 — 3D Virtual Headquarters & Signed Agent Control Center

**Cập nhật:** 17/11/2026. Dự án: `Manhhung114/Cong_ty_XD_3D`.

## Phạm vi triển khai

V7.0 mở rộng WebGL 3D hiện có (16 phòng ban, 18 Agent) và bảng giám sát của Streamlit + Google OIDC + Google Drive/HMAC. Đây là **văn phòng ảo 3D dành cho Agent**, chưa phải BIM viewer dựng công trình từ DWG/RVT. Trên desktop người dùng xoay, zoom, chọn tầng, chọn phòng/nhân vật; máy không có WebGL dùng SVG fallback. Có thể chọn lại ảnh phối cảnh cũ.

Khi nhấp vào từng Agent, thanh bên cho biết công việc được giao trong dự án hiện tại, lượt thực thi gần nhất, báo cáo nháp đã lưu, trạng thái có bằng chứng và thời điểm. Khi lọc sang dự án khác, không tiết lộ công việc ngoài phạm vi Google đã cho phép.

Sheet **Giám sát Agent** có CEO Command Center: hiển thị sơ đồ cha-con `CEO → PM → trưởng bộ môn → chuyên gia → QA/QC`, tiến độ và các điều kiện phụ thuộc từ cây phân cấp V6.9.0; 18 thẻ Agent có trạng thái nguồn gốc rõ ràng. Dashboard là **read-only**; phân việc, chạy Agent và duyệt vẫn qua dialog native có phân quyền ở sheet Công việc.

## Sự kiện thật và các trạng thái

| Nguồn nhật ký Drive có HMAC | Trạng thái hiển thị | Ý nghĩa |
|---|---|---|
| Không có `agent.started/failed/completed` | Chưa có lượt được xác minh | Không được suy ra “đang chạy” từ việc đã giao |
| `agent.started`, tối đa 120 giây, chưa có kết thúc | **Đã bắt đầu · chưa có heartbeat** | Có bằng chứng thao tác đã vào hệ thống, **không chứng minh worker còn hoạt động** |
| `agent.started` quá 120 giây, chưa có kết thúc | **Chưa xác nhận tiến trình** | Có thể bị ngắt, timeout hoặc vẫn bận; kiểm tra nhật ký / tác vụ |
| `agent.completed` | Đã lưu báo cáo nháp | Có sự kiện kết thúc, chưa phê duyệt kỹ thuật |
| `agent.failed` | Thực thi thất bại | Có mã lỗi an toàn; không lưu báo cáo giả |

Các sự kiện gắn `attempt_id`, `projectId`, `taskId`, `agentId`, `mode`, `actor`, thời điểm; `agent.completed` vẫn do hàm chạy Agent chính thức ghi sau khi xử lý. **Không** gửi token, API key, nội dung riêng tư của file CAD hoặc raw exception đến dashboard. Bấm trùng một mã lượt chạy không được gọi lại nhà cung cấp để tránh chi phí nhân đôi. Lỗi chỉ được công khai theo nhóm: permission, validation, quota, provider, network, drive, resource, internal.

## Đồng bộ

- Bảng Giám sát: polling 15 giây bằng bridge Streamlit, không WebSocket.
- Trang Văn phòng 3D: polling 15 giây **chỉ khi mở trang và tab trình duyệt đang hiển thị**, gửi lệnh `overview/refresh` read-only, có nonce và xác minh role trên server.
- Màu nhân vật và pin phòng dựa vào sự kiện thật; màu/hoạt ảnh hiển thị “đã bắt đầu, chưa heartbeat” phải có chú thích rõ, không tự quảng cáo Agent luôn online.
- Phiên bản đầu tiên chưa có worker nền hay heartbeat thực. Để cập nhật tiến độ theo từng bước trên nhiều thiết bị dù không có người mở app, cần hàng đợi + worker chạy độc lập + state store có TTL (ví dụ PostgreSQL/Redis), kiểm soát quota và truy vết; **chưa triển khai** trong bản này.

## Giới hạn và an toàn

- Giữ nguyên Google OAuth/Admin/Update/Read và quyền từng dự án; vai trò tổ chức V6.9.0 không cấp thêm quyền tài liệu.
- Giữ nguyên giới hạn đọc file Agent 50 MiB, tải lên Google Drive tối đa 500 MB.
- Không thay đổi bản vẽ gốc, hồ sơ, lịch sử phê duyệt và API vault mã hóa dùng chung.
- Không tự ký, duyệt thiết kế hay tuyên bố đã xác minh TCVN/QCVN; báo cáo luôn là bản nháp chờ kỹ sư.
- Signed event ledger Drive hiện giới hạn khoảng 2.500 sự kiện tổng cộng; phát sinh thêm start/failure events có thể làm nhanh đầy ledger. Khi mở rộng vận hành thực tế nên chuyển nhật ký tiến độ sang PostgreSQL/queue thay vì tăng trần trên Drive.

## Kiểm thử và nghiệm thu

- [ ] CI Python: start → complete; start → fail; stale sau 120 giây; không giả “running” khi chỉ có task working.
- [ ] CI Node: phản hồi 18 Agent, luồng CEO, bộ lọc dự án, XSS escaping, đồng bộ src/static và read-only polling.
- [ ] Kiểm thử 2 tài khoản Google thật trên Streamlit: Admin/Update/Read và phạm vi dự án.
- [ ] Chạy thực tế một Agent chuyên ngành với file DXF đã ghi sổ: kiểm tra event start, completion, SHA-256, báo cáo nháp.
- [ ] Thử API 401/429 và ngắt mạng, xác nhận không hiển thị giả kết quả thành công.
- [ ] Mở 2 trình duyệt song song: trạng thái polling phản ánh cùng nhật ký, start quá 120 giây bị chuyển chưa xác nhận.
- [ ] Kiểm tra xoay/zoom/chọn tầng và chọn Agent trên desktop Chrome/Android; máy không WebGL hiển thị SVG.
- [ ] Kiểm tra bộ nhớ CPU và độ trễ khi nhiều phiên xử lý; cần worker độc lập nếu không đạt.

**Trạng thái:** mã nguồn tích hợp V7.0, CI + nghiệm thu bản chạy trực tiếp quyết định mức độ sẵn sàng vận hành; không thay cho kết quả nghiệm thu tại công ty.
