# Khắc phục V7.4 không hoạt động khi giao diện đặt trên Streamlit Community Cloud

**Phiên bản giao diện:** V7.5.4. **Nhiệm vụ:** kích hoạt hàng đợi Agent V7.4 đúng nghĩa.  
**Trạng thái hiện tại:** mã runtime V7.4 có trong GitHub, nhưng phải triển khai máy chủ dịch vụ riêng. Không khẳng định worker đã hoạt động khi chưa có log máy chủ và job heartbeat thực.

## 1. Vì sao màn hình hiện “V7.4 chưa được kết nối”?

Streamlit Community Cloud chạy giao diện Streamlit và kết nối Google Drive. **Nó không tự khởi chạy PostgreSQL, Redis và Celery worker từ `docker-compose.v74.yml`** mỗi khi GitHub cập nhật.

Nút “Chạy ngay trong Streamlit” là luồng V7.0: phân tích/trích xuất trực tiếp.  
Nút “Đưa Agent vào hàng đợi V7.4” cần **Runtime API ở một máy chủ khác**, PostgreSQL, Redis, Celery và thông tin xác thực HMAC giữa Streamlit–API.

## 2. Kiến trúc không thay thế Streamlit

```text
Người dùng / điện thoại
   |
Streamlit Community Cloud (Google OIDC + giao diện V7.5.4)
   | POST /api/runtime/jobs/query, /jobs ... (HTTPS + HMAC server-side)
   v
Runtime API (FastAPI, máy chủ riêng)
   |                        |
PostgreSQL: lưu job         Redis: hàng đợi  ---> Celery worker
                                                   |
                                         Quyền Drive kiểm lại tại runtime
                                                   |
                                   Ghi báo cáo DRAFT vào signed Drive ledger
```

Không đẩy Redis/PostgreSQL ra Internet công khai. Không nhúng HMAC hay API key vào JS/iframe. Giao diện không làm mất dữ liệu Drive cũ.

## 3. Trình tự triển khai production

1. Chuẩn bị máy chủ/ứng dụng có thể chạy dịch vụ nền ổn định (Docker Compose hoặc dịch vụ tương đương). Không dùng localhost trên máy cá nhân để kết nối từ Streamlit Cloud; localhost trên Cloud không trỏ về máy của bạn.
2. Sao lưu thật Google Drive (event ledger + binary files), giữ nguyên `auth.cookie_secret`, Google root, refresh token, identity policy, đã thử restore trong sandbox.
3. Trên máy chủ worker, triển khai `postgres`, `redis`, `agent-api`, `agent-worker` từ GitHub theo `docker-compose.v74.yml` hoặc tách riêng các service trong mạng riêng. Nguồn cấu hình tham khảo `.env.v74.example`, nhưng **không đưa giá trị thật vào repository, issue, PR hoặc chat**.
4. Bảo đảm Runtime API có endpoint HTTPS do máy chủ Streamlit tiếp cận được. Test `GET /api/runtime/health` có thể dùng để nhận diện dịch vụ, nhưng `queueConfigured=true` **chưa chứng minh Celery thực chạy**.
5. Trong **Streamlit Community Cloud > Manage app > Settings > Secrets**, chủ sở hữu thêm section `[runtime]` với URL HTTPS và **cùng secret HMAC** của API. Chỉ thêm hai trường mới; không ghi đè hay xóa `[auth]`, `[drive]`, `[ai]` hiện có:
   ```toml
   [runtime]
   api_url = "https://TEN-MIEN-HTTPS-API-DA-TRIEN-KHAI"
   internal_secret = "GIA-TRI-HMAC-PRIVATE-CUA-MAY-CHU"
   ```
   Ví dụ trên chỉ là placeholder. Giữ toàn bộ Secrets ngoài Git.
6. Restart hoặc đợi Streamlit áp dụng cấu hình. Chọn dự án/công việc hợp lệ, mở “Chạy chuyên viên AI”. V7.5.4 kiểm tra `POST /api/runtime/jobs/query` có ký HMAC trước khi bật nút V7.4.
7. Chạy thử bằng **Checklist hồ sơ** (không cần provider/không phát sinh phí), bấm Đưa vào hàng đợi; đối chiếu job `queued → running` với heartbeat thật → `completed` hoặc báo lỗi. Trước khi thử LLM/file thật phải kiểm ACL, file hash, giới hạn file, quy trình QA người thật.
8. Test hủy job, mất Redis, mất worker, thu hồi người dùng, crash/restart, idempotency, băng thông Drive, và thử phục hồi database. Khi có bằng chứng mới nghiệm thu production.

## 4. Chẩn đoán trạng thái V7.5.4

| Trạng thái | Ý nghĩa và hành động |
|---|---|
| Chưa cấu hình | Thiếu URL API hoặc HMAC hợp lệ; chưa triển khai hoặc chưa thêm `[runtime]` trong Secrets |
| API chưa kết nối | Server tắt, HTTPS/DNS/firewall/network lỗi, API không phản hồi hoặc trả dữ liệu không hợp lệ |
| Từ chối xác thực/quyền | HMAC không khớp, timestamp sai hoặc dự án/Google identity không đủ quyền |
| API đã xác thực | HMAC + query danh sách job có phản hồi; **không đồng nghĩa worker sống** |
| Job có heartbeat thật | Bằng chứng Celery xử lý; phải có log và signed Drive draft để xác nhận kết quả |

**Dữ liệu AI:** “Chuyên gia phân tích file thật” dùng parser nội bộ và không yêu cầu đồng ý chuyển dữ liệu tới Gemini. Chỉ các chế độ có chữ **AI** mới yêu cầu đồng ý chia sẻ metadata/trích xuất mẫu.

## 5. Điều chưa có căn cứ nghiệm thu

- Hiện chưa có quyền truy cập bảng quản trị máy chủ Runtime API hay Secrets của Streamlit trong cuộc hội thoại.
- Mã nguồn/CI đã có PostgreSQL+Redis+Celery thử nghiệm với **Drive giả lập**, không chứng minh các dịch vụ đó đã chạy trên tên miền thật.
- Không bật quyền QCX/LEG, không đặt `XD_V752_MEETINGS` thành 1, không đăng ký agent với quyền không xác minh, không mở cổng Redis/PostgreSQL Internet.

**Kết luận:** Không thể kích hoạt hàng đợi V7.4 chỉ bằng merge GitHub; cần máy chủ nền riêng cùng cấu hình Streamlit server-side. V7.5.4 sửa phần chẩn đoán và tránh hiện nút hàng đợi khi API không xác thực.
