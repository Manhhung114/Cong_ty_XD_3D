# V7.1–V7.4 — Bộ nâng cấp hợp nhất Công ty XD & MEP AI 3D

Ngày chuẩn bị: 17/11/2026. **Giữ nguyên dữ liệu Google Drive, quyền Google OIDC, 18 Agent, V6.9 phân cấp, V7.0 văn phòng 3D**.

## Phạm vi đã thêm trong mã nguồn

| Mốc | Thành phần | Khả năng hiện có sau khi cấu hình runtime |
|---|---|---|
| V7.1 | `agent_runtime/api.py`, `models.py`, `worker.py`, Redis/Celery/PostgreSQL | Job có ID duy nhất, hàng đợi thật, worker thực thi Agent, heartbeat 10 giây, giới hạn tài nguyên, hủy có kiểm soát, báo lỗi thật, idempotency, chi phí **ước tính** |
| V7.2 | `agent_runtime/graph.py`, `batch.py`, V6.9 hierarchy UI | LangGraph xác định cổng QA/duyệt người thật; Admin có lựa chọn **đẩy đồng loạt checklist** PM/Lead/Engineer sau khi duyệt cây, KHÔNG gọi AI tính phí tự động, không chạy QA trước tiền nhiệm |
| V7.3 | `standards.py`, `cad_tools.py` | Nguồn tiêu chuẩn/catalogue được phép sử dụng có số hiệu, version, trích dẫn, SHA-256, giới hạn đoạn trích; công cụ phân tích PDF bảng; tạo **bản sao DXF có ghi chú** sau khi kỹ sư xác nhận, không ghi đè nguồn |
| V7.4 | `providers.py`, `docker-compose.v74.yml`, giao diện CEO | Tùy chọn Anthropic hoặc Ollama trên worker **qua môi trường riêng**, OpenAI/Gemini vẫn dùng vault mã hóa Drive; giám sát 3D có queued/running/heartbeat/unconfirmed/completed/failed, lọc quyền dự án, Docker Compose 5 dịch vụ, CI chuyên biệt |

**Ranh giới:** Đây là mã nguồn nâng cấp + gói triển khai. Phải tự cấp cơ sở dữ liệu/Redis và OAuth secrets cho deployment mới. Không hứa 18 AI chạy đồng thời chỉ vì 18 Agent có tên. Chưa có kiểm thử tải với 18 lời gọi LLM/CAD 50 MB thực tế. Không tự kiểm duyệt bản vẽ hoặc cấp chứng nhận TCVN/QCVN.

## Bảo mật và vận hành

1. **Giao diện Streamlit vẫn dùng Google OIDC:** chỉ người có quyền Cập nhật/Admin và đúng dự án mới được nhấn đưa job vào hàng đợi. Bản quyền của người dùng không được quyết định bởi tham số iframe hay trường dữ liệu tùy ý.
2. **Server-to-server:** Streamlit ký HMAC bằng `AGENT_RUNTIME_SECRET` cho `POST /api/runtime/...` (timestamp ±60 giây, method+path+body); không đưa shared secret vào browser.
3. **Worker tái kiểm tra quyền Drive tại lúc chạy:** root, refresh token, policy HMAC, actor và project scope. Nếu bị thu hồi quyền khi đang chờ, worker không đọc file.
4. **Worker chỉ tạo nháp có ký:** `SharedWorkspace.record_agent_start` → `run_agent` hoặc `run_expert` (file đã ghi sổ; checksum/ACL) → `agent.completed`/ `agent.failed`. Kết quả không làm task `done`; kỹ sư/QA/Admin vẫn duyệt qua quy trình cũ.
5. **Heartbeat:** Worker thực thi ghi DB mỗi 10 giây, UI công nhận `running` chỉ khi heartbeat không quá 90 giây; nếu mất, `unconfirmed`. Chờ hàng đợi thể hiện `queued` riêng, không giả đã thực thi.
6. **Hủy:** queued chuyển `cancelled` ngay; running đánh dấu `cancel_requested` và dừng tại checkpoint trước tác vụ tiếp theo. **Không thể bảo đảm ngắt ngay một lời gọi API/CAD đang xử lý**. Không được báo hủy xong khi chưa có trạng thái tương ứng.
7. **Chống chạy trùng:** jobId 32-hex duy nhất; API trả cùng job khi nhấn lại; worker claim bằng UPDATE WHERE status=queued, không chạy lại yêu cầu có phí nếu đã có signed start của cùng attempt. Broker thất bại => `dispatch_failed`, không hiển thị đang chạy.
8. **Chi phí:** dự trù tối đa $0.06 (metadata) / $0.09 (file+LLM) cho mỗi job để chặn hạn mức theo tháng; đây là **ước tính bảo thủ cấu hình**, `actualCostUsd=null` cho đến khi có số usage đáng tin cậy. Không hiển thị chi phí ước tính như hóa đơn.
9. **Nhật ký:** PostgreSQL dành cho vòng đời job, HMAC Google Drive giữ tài liệu/hồ sơ và quyết định ký cũ. Không chuyển/xóa các sự kiện cũ. Ledger Drive V7.0 hiện có trần 2500 sự kiện, cần migration + reconciliation trước khi mở rộng production lớn.
10. **Tài liệu tiêu chuẩn:** Admin nhập nguồn theo dự án, chứng nhận quyền sử dụng, version, citation, ngày hiệu lực, SHA. Chỉ đưa metadata trích dẫn có giới hạn vào context Agent; không gộp nhầm tìm kiếm tương đồng thành quyết định đạt quy chuẩn.
11. **CAD/BIM:** Direct DWG/RVT/NWD vẫn chưa hỗ trợ; DXF/PDF/CSV/XLSX/IFC đọc có giới hạn; IFC geometry clash, dựng BIM hoàn chỉnh, shopdrawing CAD tự sửa đúng tiêu chuẩn là các hệ thống chuyên ngành chưa được chứng minh. File sửa do `cad_tools` tạo **phải được kỹ sư duyệt rồi mới upload dưới revision mới**, chưa tự phát hành.

## Cách chạy trên máy chủ có Docker

1. Lấy bản mới từ nhánh `main` sau khi CI PASS; chuẩn bị một tên miền HTTPS/ reverse proxy cho Streamlit và cấu hình Google OIDC redirect URI đúng tên miền. Nếu tiếp tục chạy trên Streamlit Community Cloud thì *chỉ phần V7.0 trực tiếp* có thể hoạt động; runtime mới cần PostgreSQL+Redis+worker bên ngoài và cấu hình `[runtime]` trong Secrets hoặc biến môi trường server.
2. Copy `.env.v74.example` thành **file bí mật nằm ngoài Git** (có thể tham khảo ở `.env.v74` trên máy chủ) và cung cấp **giá trị thực qua secret manager**. Các biến bắt buộc: `XD_POSTGRES_PASSWORD`, `AGENT_RUNTIME_SECRET` (32+ ký tự), `XD_AUTH_COOKIE_SECRET` (phải trùng cookie secret Streamlit hiện có), `XD_OWNER_EMAIL`, 4 khóa `XD_DRIVE_*`, `XD_STREAMLIT_SECRETS_FILE`. Đảm bảo Worker và Streamlit trỏ cùng Google Drive root. Không chia sẻ/tạo file bí mật trong GitHub.
3. Bật mạng nội bộ Docker, HTTPS từ bên ngoài, Redis/PostgreSQL không mở cổng public. Thiết lập `XD_WEB_BIND=127.0.0.1` hoặc một reverse proxy HTTPS nếu cần truy cập từ điện thoại.
4. Chạy `docker compose --env-file .env.v74 -f docker-compose.v74.yml up -d --build`. Đợi trạng thái dịch vụ `postgres`, `redis`, `agent-api`, `agent-worker`, `streamlit`.
5. Trong Streamlit, giữ cấu hình Google OAuth hiện tại. Docker Compose kết nối ngầm bằng `XD_RUNTIME_API_URL=http://agent-api:8082` và `AGENT_RUNTIME_SECRET` trên server; chỉ chấp nhận HTTP nội bộ với `AGENT_RUNTIME_ALLOW_DOCKER_HTTP=1`. Nếu server phân tách ngoài Docker, sử dụng URL HTTPS.
6. Vào **Công việc → Chạy Agent** chọn `🚀 Đưa Agent vào hàng đợi V7.4`, theo dõi tiến độ và thu hồi trong dialog. Trong **Giám sát Agent**, quan sát worker heartbeat/queue và cây CEO. Có thể vẫn `Chạy ngay trong Streamlit` nếu chưa bật worker.
7. Giao cho CEO theo V6.9, Admin duyệt phương án; Admin có thể chọn **đưa checklist tự động xuống PM/Lead/Engineer** (không trả phí). QA chỉ bắt đầu sau khi kết quả chuyên gia đã được cấp có thẩm quyền duyệt. LLM và đọc file thật phải được người có quyền chọn, chấp thuận chia sẻ dữ liệu.
8. Admin có thể nhập tài liệu tham chiếu có bản quyền hợp lệ trực tiếp trong dialog Agent (V7.3), không tạo trang tải file riêng.
9. Nếu chọn Anthropic/Ollama, quản trị viên cấu hình trên worker bằng `AGENT_RUNTIME_OPTIONAL_PROVIDER`, model và key tương ứng. OpenAI/Gemini vẫn lấy từ API dùng chung mã hóa trên Drive. Không sửa file `[ai]` cũ để chuyển provider mà chưa được kiểm thử.

## Giới hạn song song và kế hoạch nghiệm thu 18 Agent

- **Mặc định:** `AGENT_WORKER_CONCURRENCY=4`, `AGENT_QUEUE_MAX=100`. 18 Agent logic có thể được giao việc trong hàng đợi nhưng không có nghĩa là 18 tiến trình nặng chạy cùng lúc.
- **Tăng dần:** thử 2 → 4 → 8 → 12 → 18 worker dưới mức CPU/RAM/API quota thật, theo dõi lỗi 429, timeout, băng thông Drive, số job được duyệt và kích thước DXF/IFC 50 MiB. Mỗi model provider còn có riêng giới hạn RPS/TPM; không được tùy tiện tăng 18 nếu quota không đủ.
- **Acceptance:** trọn vòng CEO→PM→Lead→Expert→QA→Admin, 2 tài khoản thật, lỗi Google token/revocation, worker crash/restart, Redis down, DB down, đồng thời các tác vụ lớn, bảo đảm giữ file gốc, phục hồi ký Google Drive, không có kết quả giả; backup PostgreSQL và restore thử.
- **Các khả năng tiếp theo:** đo **actual token usage/cost** thay thế ước tính, chứng minh CAD geometry/clash, xây shopdrawing đầy đủ, tìm kiếm vector pgvector (bản hiện tại dùng **tìm kiếm lexical có nguồn**, không nói đã có embedding), tự phục hồi job đã chạy dở với kiểm soát không tính phí lặp.

## Lệnh kiểm thử

```sh
python -m pip install -r requirements.txt -r agent_runtime/requirements.txt httpx pytest
python -m unittest discover -s agent_runtime/tests -p 'test_*.py' -v
python -m unittest discover -s tests -p 'test_*.py'
npm test
python -m compileall -q agent_runtime drive_storage streamlit_app.py
```

GitHub Actions: `Verify V7.1-V7.4 Agent Runtime` + `Verify app and Drive auth`. Cả hai phải PASS trước khi merge. **Đạt CI không đồng nghĩa đã nghiệm thu live production.**
