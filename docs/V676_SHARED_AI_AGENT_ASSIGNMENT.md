# V6.7.6 – Giao việc đúng Agent & API dùng chung toàn công ty

**Ngày triển khai:** 17/11/2026. Dự án: Công ty XD & MEP AI 3D (Streamlit + Google Drive).

## 1. Phân tích vấn đề thực tế

Ảnh chụp công việc **CV-1AB9B47B** thể hiện `electrical · Chưa giao` trong khi nhãn công việc là **Đang thực hiện**. Hai dữ kiện này KHÔNG xác nhận Agent đã chạy. Trước bản sửa:

- `task.created` chỉ có `assignee` chuỗi người phụ trách; thường để trống. `task.started` chỉ đổi tiến độ task thành `working`.
- Phải mở **Nhân viên AI**, chọn Agent và công việc, bấm **Chạy Agent** rồi xác nhận; chỉ khi backend ghi sự kiện `agent.completed` thì mới có báo cáo nháp.
- `Cài đặt API` V5.7.3 lưu khóa trong RAM/khóa mã hóa localStorage của **một thiết bị**; nhưng engine `run_agent` chỉ nhận `st.secrets[ai]` **trên máy chủ**, nên key nhập ở app web không kích hoạt chạy AI trên backend, tài khoản khác cũng không dùng được.

## 2. Giải pháp phân công và theo dõi minh bạch

- Nhiệm vụ có **người phụ trách** (`assignee`) và **Agent được chỉ định** (`assignedAgentId`) độc lập.
- Biểu mẫu **Giao công việc** bổ sung Agent theo bộ môn (tùy chọn), không giả định Agent đã chạy.
- Thêm nút **Gán / Sửa phân công** cho nhiệm vụ đang chờ hoặc đang xử lý. Chỉ Admin/nhân viên Cập nhật trong dự án được cấp quyền mới thao tác được.
- Mọi phân công sửa đổi lưu dưới sự kiện **`task.assigned` HMAC có chữ ký** vào kho Drive dự án. Không làm mất công việc cũ; công việc cũ mặc định “Chưa gán Agent”.
- Trên mỗi thẻ công việc có **Chuyên gia được giao / Trạng thái Agent**: “Agent chưa chạy” hoặc “Đã tạo N báo cáo nháp; chờ kỹ sư kiểm chứng”.
- Khi đã gán Agent phù hợp, hiện nút **🤖 Chạy Agent** ngay trên thẻ công việc, mở dialog trên Streamlit có kiểm tra ACL dự án và bộ môn; người dùng chọn `Checklist`, `Chuyên gia đọc file thật`, `AI metadata` hoặc `AI + file`. Chế độ gọi nhà cung cấp có chi phí phải tick đồng ý gửi metadata/file trích xuất mẫu.
- Sau khi Agent trả lời thành công, backend ghi `agent.completed` kèm báo cáo nháp/nguồn vào sổ ký; có thể xem kết quả theo công việc, Agent hoặc dashboard.

**Không có worker chạy nền.** Gán Agent không tự gọi AI hay đánh dấu đã hoàn thành. Mỗi lần chạy do người dùng bấm trực tiếp. Mục tiêu worker chạy tự động theo lịch/hàng đợi cần PostgreSQL, job queue và heartbeat ở bản sau.

## 3. API dùng chung — cấu hình một lần

**Chỉ Admin** thấy mục **Cài đặt**. Sau đăng nhập:

1. Mở **Cài đặt → API & 18 Agent – cấu hình dùng chung toàn công ty**.
2. Bấm **Cài đặt / Thay API dùng chung**. Streamlit mở dialog phía máy chủ.
3. Chọn **Google Gemini** hoặc **OpenAI**, nhập **model mặc định**, **API key**. Có thể gán một model riêng theo Agent, tất cả Agent khác dùng model mặc định.
4. Xác nhận điều khoản chi phí, bấm **Lưu mã hóa và áp dụng toàn công ty**.
5. Mở thiết bị/tài khoản nhân viên khác. Sheet Agent sẽ hiển thị **đã cấu hình AI trên máy chủ**, không yêu cầu nhân viên nhập key lại. Người Cập nhật có quyền chạy trong dự án được cấp; Chỉ đọc chỉ xem.
6. Khi đổi key/provider, Admin mở dialog và thay; key cũ không bao giờ hiển thị lại. Khi thu hồi, hệ thống ghi trạng thái **vô hiệu hóa có mã hóa**, tránh fallback vào `[ai]` Secrets trước đây.

**Backend bảo mật:** file `_XD_MEP_AI_SHARED_CREDENTIALS_V676.json` trong root Google Drive cấu hình sẵn, chứa AES-256-GCM ciphertext + nonce ngẫu nhiên. Khóa mã hóa suy ra bằng SHA-256 có tách miền từ **`[auth].cookie_secret` bí mật/ổn định dài tối thiểu 32 ký tự** kết hợp `root_folder_id`. Mã nguồn, repo, log, iframe và JSON snapshot không chứa API key hoặc khóa giải mã. Nếu đổi cookie_secret mà không giữ khóa cũ, dữ liệu vault không thể giải mã; chương trình **chặn** thay vì ghi đè.

Khác với API localStorage cũ, bản mới chỉ dùng máy chủ. Nhân viên không được thấy hoặc tải ciphertext/khóa qua API app. Hệ thống duy trì tương thích với cấu hình **`[ai]` trong Streamlit Secrets** cho đến khi Admin lưu bản Drive đầu tiên.

### Kiểm soát chi phí và bảo mật vận hành

- Lệnh LLM vẫn yêu cầu xác nhận truyền metadata hoặc phần trích xuất MẪU của hồ sơ, không tự gửi tệp gốc.
- Mọi lượt chạy tuân theo giới hạn/ngày và bộ môn, dự án được kiểm tra trên máy chủ.
- Không tự động tải lên GitHub bất kỳ API key/refresh token. Tránh dùng key có hạn mức chi tiêu quá cao.
- Tham số model phải khớp model nhà cung cấp thực sự hỗ trợ, ví dụ Gemini 2.5 Flash/OpenAI Chat Completions tương thích; không tự kiểm chứng tên model chưa được cấu hình.

## 4. Trường hợp công việc trong ảnh

Với `CV-1AB9B47B` (Điện):

1. Vào **Công việc** của dự án **S234 – SUNSHINE SKY CITY**.
2. Trên thẻ nhiệm vụ, bấm **Gán / Sửa phân công**.
3. Điền người phụ trách nếu có, chọn **Agent Điện (ELE)** rồi lưu.
4. Thẻ hiển thị **Đã gán ELE · Agent chưa chạy**.
5. Bấm **🤖 Chạy Agent ELE**. Nếu cần kết quả mô hình AI thực, chọn `AI metadata` hoặc `AI + file`, tick xác nhận chia sẻ và thực thi.
6. Sau khi có `agent.completed`, mở báo cáo nháp; kỹ sư phải rà soát số liệu, DWG/IFC và quyết định phê duyệt. Nếu lỗi nhà cung cấp, **không ghi kết quả giả** và task vẫn giữ nguyên.

## 5. Nghiệm thu bắt buộc

1. Admin lưu Gemini API/key/model một lần từ Settings. Đăng xuất và dùng nhân viên được cấp quyền để mở Agent: trạng thái vẫn “đã cấu hình”; không thấy khóa.
2. Tạo task mới, gán ELE khi dept=electrical; server bác gán STR vào task Điện. Test sửa phân công nhiệm vụ cũ.
3. Trước khi chạy, `agentRuns = 0` mặc dù task đã có người/Agent và nhãn tiến độ `working`.
4. Bấm Chạy Agent, chọn checklist: có sự kiện HMAC `agent.completed`, không tự phê duyệt.
5. Chọn gọi AI thật, tick consent; xác minh provider phản hồi, key chỉ được gửi từ Streamlit server.
6. Thử hai tài khoản trên hai thiết bị; nhân viên không sửa được API tập trung, Chỉ đọc không tạo task/lượt Agent.
7. Thử sửa hoặc đổi 1 byte ciphertext Drive: backend từ chối giải mã và không tự ghi đè.
8. Admin thu hồi API: backend vẫn không quay về Secrets cũ.
9. Chrome/Edge, màn hình mobile, chuyển giữa Công việc, Nhân viên AI và Cài đặt, upload Drive và phê duyệt không hồi quy.
10. Giữ nguyên toàn bộ dữ liệu và báo cáo đã lưu. **CI PASS không thay cho thử nghiệm thật** với tài khoản và API key trong môi trường sản xuất.

## 6. Giới hạn

Phiên bản này không cung cấp worker chạy nền, không tự đọc toàn bộ DWG/RVT, không phê duyệt hồ sơ và không thay thế người làm thiết kế; trạng thái “Agent chạy” chỉ được xác nhận sau khi có sự kiện hoàn tất. Admin cần nhập lại API key từ thiết bị cũ **một lần** để đưa vào vault máy chủ; không thể tự đồng bộ mật khẩu đã được mã hóa trên localStorage của trình duyệt khác.
