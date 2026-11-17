# SPEC V6.7 — Graphic realtime giám sát Agent và phối hợp MEP ↔ Xây dựng

**Ngày:** 17/11/2026 · **Ứng dụng:** Công ty XD & MEP AI 3D · **Trạng thái:** đặc tả giao diện đã duyệt, hiện thực hóa trên Streamlit + Google Drive có HMAC.

## 1. Mục tiêu và phong cách mẫu

Tham chiếu hình giao diện được duyệt trong cuộc trò chuyện: **dashboard dark navy, ánh sáng xanh cyan, các card bo góc, viền sáng mỏng, sidebar trái, header, sáu KPI, biểu đồ hoạt động, donut, bar, Sankey, network, timeline, top Agent, bottleneck, live feed và cảnh báo**.

Đây là bản ứng dụng thật dựa trên nhật ký đã ký, **không bê nguyên các số minh họa hoặc ngày tháng của ảnh mẫu**. Nền chung của ứng dụng dùng #04101E/#071E38, viền xanh #137DBE, MEP xanh cyan #27C8EB, Xây dựng tím #A07CF6, cảnh báo đỏ #FF6877, xử lý tốt trên desktop, tablet, mobile. Giữ giao diện Văn phòng 3D và các chức năng quản lý hiện có.

**Mục menu mới:** Giám sát Agent (V6.7), hiển thị cho mọi tài khoản Google đã được cấp phép. Không thêm màn hình đăng nhập hay trang upload riêng. Cài đặt vẫn chỉ Admin thấy.

## 2. Hai hệ MEP và XD là hai hệ riêng, phối hợp hai chiều

### Phân chia chuyên môn

| Hệ MEP | Hệ Xây dựng (XD) | Khối chung |
|---|---|---|
| Điện (ELE), HVAC (HVA), Cấp thoát nước (PLU), PCCC (FIR), BIM MEP (BIM), QS MEP (QSU), QA/QC MEP (QAC) | Kiến trúc (ARC), Kết cấu (STR), BIM XD (XBI), QS XD (XQS), Kế hoạch (PLN), Thi công hiện trường (SIT), HSE (HSE), Vật tư (MAT) | Giám đốc/PM (CEO/PM); DOC làm chức năng kiểm soát tài liệu chéo hệ trong phân tích Agent |

### Bốn loại luồng đúng từ dữ liệu

- **MEP → MEP**: ví dụ Điện → BIM MEP.
- **XD → XD**: ví dụ Kết cấu → BIM XD.
- **MEP → XD**: ví dụ HVAC → Kết cấu hoặc Điện → BIM XD.
- **XD → MEP**: ví dụ Kết cấu → Điện hoặc Hiện trường → PCCC.

Phân loại dựa trên `source_dept` / `target_dept` được ghi trong sự kiện `handoff.requested`. Sự kiện `handoff.resolved` phải tra lại nguồn/đích từ phiếu gốc. Không tự nối mũi tên nếu chưa có phiếu phối hợp thực; không vẽ PM như nút trung tâm nếu không có phiếu thực tế liên quan.

**Phạm vi xem:** Toàn bộ dự án được cấp quyền / một dự án / Hệ MEP / Hệ XD / Chỉ luồng phối hợp MEP ↔ XD / bộ môn cụ thể. Admin xem toàn bộ dự án; người cập nhật hoặc chỉ đọc chỉ xem dự án được máy chủ cấp quyền. **Phạm vi lọc không cấp thêm quyền đọc.**

## 3. Dashboard

| Khu vực | Dữ liệu và ý nghĩa | Quy tắc hiển thị |
|---|---|---|
| KPI 1 | Số **lượt Agent đã hoàn thành** trong kỳ | `agent.completed`, KHÔNG gọi là Agent đang chạy nếu không có heartbeat |
| KPI 2 | Công việc đang mở | Trạng thái task todo/working/review hiện tại |
| KPI 3 | Phiếu phối hợp đang mở | Từ trạng thái handoff hiện tại |
| KPI 4 | Thời gian phản hồi trung bình | Hiệu `resolvedAt-createdAt` của phiếu đóng trong kỳ; 0 mẫu hiển thị — |
| KPI 5 | Công việc quá hạn | `dueDate` trước ngày hiện tại và chưa done |
| KPI 6 | Tỷ lệ hoàn thành | done/total trong phạm vi xem, không có task thì hiển thị — |
| Line chart | Hoạt động theo giờ/5 phút/ngày | Nhóm Agent, công việc, phối hợp, phê duyệt từ sự kiện thật |
| Donut | Todo, Doing, Review, Done | Tổng đúng bằng số task; quá hạn là cảnh báo riêng, không cộng hai lần |
| Department bars | Agent runs theo phòng | Phân loại MEP/XD theo bộ môn |
| Sankey | Luồng source → target | Độ dày theo số phiếu thật trong kỳ |
| Network | Các phòng ban thực sự có phiếu | Không thêm cạnh tưởng tượng |
| Timeline handoff | 5 phiếu gần nhất | Thời gian gửi/đóng; phiếu còn mở dùng thời gian tính đến lúc đồng bộ |
| Top Agent | Agent có nhiều lần chạy hoàn tất | Không suy diễn công suất hay năng suất của AI từ số lần chạy |
| Top bottleneck | Phòng nhận nhiều phiếu đang mở | Phân theo targetDept |
| Activity feed | 8 sự kiện gần nhất | Email đã xác thực, thời gian VN, loại sự kiện và mã liên quan |
| Alert | Tắc nghẽn/phê duyệt/quá hạn | Handoff quá 4 giờ; review quá 24 giờ; task quá hạn; 5+ phiếu mở/phòng |

**Khoảng thời gian:** 1 giờ gần nhất, Hôm nay (múi giờ Asia/Ho_Chi_Minh), 7 ngày. Có nút làm mới ngay và tự làm mới mỗi 15 giây khi tab hiển thị. **KPI trạng thái hiện tại** và biểu đồ sự kiện trong kỳ được ghi rõ để không hiểu lầm.

## 4. Dữ liệu thời gian thực được hỗ trợ

V6.7 hiện dùng **polling gần thời gian thực**, không phải WebSocket:

1. Trang Giám sát Agent yêu cầu Streamlit lấy snapshot.
2. Máy chủ dùng Google OAuth + quyền dự án rồi xác thực chữ ký HMAC của toàn bộ sự kiện.
3. Sự kiện được lọc theo tập dự án được cấp trước khi tạo bất kỳ dữ liệu đầu ra nào.
4. Chỉ gửi bản tóm tắt an toàn gồm: ID, thời gian, actor, action, mã Agent/task, nguồn/đích handoff. Không truyền report nội bộ, file gốc hay API key.
5. Client SVG dựng đồ thị; mỗi 15 giây (khi trang đang mở và checkbox Tự cập nhật bật) gửi `monitor/refresh` qua bridge đã xác thực.
6. Sau khi rerun, Streamlit nạp lại packet; bộ lọc dự án/hệ/kỳ/bộ môn được ghi trong session và kiểm tra giới hạn quyền trước khi trả về.
7. Nếu không có dữ liệu, hiển thị **chưa có sự kiện**, tuyệt đối không sinh dữ liệu giả.

Phản hồi API Google Drive có thể chậm nên **chu kỳ mục tiêu 15 giây không bảo đảm độ trễ dưới 15 giây**. Không có worker/heartbeat để biết Agent đang xử lý tại đúng giây hiện tại. V6.7 chỉ biết lượt đã ghi nhận; khi cần giám sát trạng thái RUNNING thật cần job queue và heartbeat của worker.

Giới hạn trong bản thử nghiệm: tối đa 900 sự kiện gần nhất trong 7 ngày, 1.000 task và 300 phiếu handoff trong phạm vi. Khi cắt mẫu, hiển thị cảnh báo, không trình bày số lượng sự kiện trong kỳ như thống kê toàn vẹn. Bản doanh nghiệp nhiều sự kiện cần chuyển sang PostgreSQL + Redis/WebSocket hoặc dịch vụ event stream.

## 5. Phân quyền và an toàn

- Chỉ người đăng nhập Google, email được xác thực/allowlist và thuộc dự án mới nhận packet.
- Tài khoản Chỉ đọc được xem dashboard nhưng không có thao tác sửa dữ liệu.
- Bảng là read-only; không có nút cho Agent tự duyệt, tự đóng phiếu hay ký số.
- Tất cả thông tin file gốc, mật khẩu API, OAuth refresh token, prompt/report nhạy cảm bị loại trước khi gửi iframe.
- Trường text hiển thị đều được escape HTML; tên tác vụ hay tiêu đề phiếu không được thực thi script.
- Khi xác minh HMAC hoặc Drive lỗi, chặn dữ liệu mới thay vì dùng KPI tự bịa.
- Đối với nhiều người đồng thời, Drive ledger phải được thay bằng DB có transaction/cache để tránh đọc hàng trăm file JSON mỗi 15 giây.

## 6. Cấu trúc mã nguồn

- `drive_storage/monitoring.py`: MEP/XD taxonomy và thống kê sự kiện đã ký theo ACL.
- `drive_storage/shared_workspace.py`: tùy chọn `include_monitor` khi snapshot, dùng lại ledger đã xác thực (không tải nhật ký lần thứ hai).
- `drive_storage/workspace_ui.py`: nhận `monitor/refresh`, lưu filter trong Streamlit session, đảm bảo không chuyển quyền.
- `drive_storage/in_app.py`: giao thức bridge monitor qua iframe.
- `src/core/monitor_dashboard.js` và `static/src/core/monitor_dashboard.js`: SVG line, donut, bars, Sankey, network, timeline, ranking, activity feed, filters và polling.
- `src/polish.css` và `static/src/polish.css`: giao diện xanh đen theo hình mẫu, sidebar, KPI card, responsive.
- `scripts/build_streamlit_runtime_v2.py`: giữ đúng tab monitor qua mỗi lần Streamlit rerun.

## 7. Checklist nghiệm thu (điều kiện bắt buộc trước khi vận hành chính thức)

1. Đăng nhập Admin trên Streamlit, mở Giám sát Agent, xác nhận nền và đồ thị giống bố cục hình mẫu nhưng **không có số giả**.
2. Tạo task Điện và task Kết cấu cùng dự án; lọc MEP chỉ hiển thị task Điện, XD chỉ task Kết cấu.
3. Tạo phiếu MEP Điện → XD Kết cấu, và XD Kết cấu → MEP BIM; Sankey và network phải hiển thị **cả hai chiều**.
4. Admin/nhân viên khác đóng một phiếu; chọn 1 giờ/Hôm nay, thấy cập nhật thời gian phản hồi, số phiếu mở và Live Feed sau refresh.
5. Mở tài khoản Chỉ đọc chỉ cấp một dự án, xác nhận không nhìn thấy sự kiện/phiếu/tên dự án khác.
6. Đổi filter và kiểm tra auto refresh 15 giây vẫn giữ nguyên filter. Ẩn tab trình duyệt thì dừng gửi sự kiện refresh.
7. Vào Công việc/Agent sau đó quay lại Giám sát, không bị nhiều timer chạy song song.
8. Tạo task quá hạn, phiếu mở >4 giờ, task chờ duyệt >24 giờ; cảnh báo khớp dữ liệu và không sửa trạng thái.
9. Không có task hay event phải hiện 0 hoặc —, không lấy số trên hình demo.
10. Test trên màn 1920px, 1366px, tablet và mobile; bảng/đồ thị không tràn màn và các nút sử dụng được.
11. Đổi một byte trong event ledger đã ký: máy chủ từ chối hiển thị và ghi nhận lỗi; không dùng bản cache cũ.
12. Xác nhận Google OAuth, phân quyền Admin-only Cài đặt, Kho tài liệu và các chức năng V6.4–V6.6 vẫn hoạt động.
13. Đo số API calls và thời gian snapshot khi có 100/500/900 sự kiện và 2–10 người dùng; nếu polling Drive quá tải, bật chu kỳ 30–60 giây hoặc nâng backend.

## 8. Hạng mục sau V6.7

- PostgreSQL/Redis, worker heartbeats RUNNING/QUEUED/FAILED/RETRY, WebSocket/SSE thật.
- SLA theo từng phòng ban và công việc, thông báo push/email; phân quyền theo phòng ban.
- Xuất báo cáo giám sát PDF/Excel chính thức; lịch sử dài hơn 7 ngày có phân trang.
- Phân tích chuỗi thời gian chuyên sâu, truy nguồn lỗi QA/IFC và thời gian xử lý theo mức ưu tiên.
