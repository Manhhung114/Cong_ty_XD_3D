# BÀN GIAO DỰ ÁN — CÔNG TY XD & MEP AI 3D — V7.4.0
**Ngày:** 17/11/2026 · **Mục đích:** Chuyển sang cuộc trò chuyện ChatGPT mới, tiếp tục chính xác tiến độ, không khởi tạo lại dự án hoặc xóa dữ liệu.

## 1. THÔNG TIN KHÓA CỨNG (đã kiểm tra trực tiếp GitHub)

- Repository nguồn: https://github.com/Manhhung114/Cong_ty_XD_3D
- Nhánh chính: `main`
- **Baseline mã nguồn V7.4.0:** `f18062493035530a706da443598c5e29496cba10`
- PR gộp V7.1–V7.4: https://github.com/Manhhung114/Cong_ty_XD_3D/pull/22 (**merged**). Trước đó PR #20 đã gộp phân cấp V6.9, PR #21 đã gộp V7.0 văn phòng 3D.
- `VERSION_MANIFEST.json`: `artifact_version=0.7.4.0-integrated-agent-runtime-suite`, `current_version=V7.4.0 (Agent Runtime + Orchestration + Engineering Suite)`.
- Streamlit công khai: https://congtyxd.streamlit.app/ — **chưa nghiệm thu lại trực tiếp bằng tài khoản Google thật sau V7.4**; không suy diễn app đã deploy mọi microservice.
- Sau khi bổ sung chính tài liệu bàn giao này, HEAD trên `main` sẽ có commit mới hơn baseline `f180624` **chỉ vì thay đổi tài liệu**. Cuộc trò chuyện mới phải kiểm tra HEAD thực tế trước mọi sửa đổi.
- Đặc tả triển khai: https://github.com/Manhhung114/Cong_ty_XD_3D/blob/main/docs/V740_INTEGRATED_AGENT_RUNTIME.md
- Docker: `docker-compose.v74.yml`; cấu hình bí mật mẫu: `.env.v74.example`.

**CI chạy trên đúng mã nguồn f180624 sau khi merge:**
- [Verify app and Drive auth: PASS](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44084933264)
- [Verify V7.1–V7.4 Agent Runtime: PASS](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44084933075)
- [Build Android APK: PASS (debug; signed release step skipped)](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44084933146)
- **Lưu ý:** PR/CI là kiểm thử tự động trong môi trường giả lập (SQLite và dispatcher giả cho API); chưa xác minh triển khai hạ tầng, OAuth thật, 18 Agent chạy song song hoặc file CAD thực tế trên máy chủ.

## 2. YÊU CẦU KHÔNG ĐƯỢC PHÁ

1. Giữ nguyên 18 AI Agent theo vai trò; văn phòng WebGL 3D với 16 phòng, hình nền/header và responsive; giao diện có chọn tầng, nhân vật, inspector và CEO Command Center.
2. Giữ hệ thống Google OIDC: **đăng nhập trước vào app**, Admin mới thấy cài đặt và quản lý phân quyền; vai trò Read/Update/Admin, giới hạn dự án thực hiện trên server.
3. API AI dùng chung (OpenAI/Gemini) **Admin cấu hình một lần, mã hóa AES-256-GCM trên Drive**, các nhân viên được phép dùng mà không xem khóa. Không đưa API key, cookie secret, OAuth refresh token vào repo, trình duyệt, log hay tài liệu bàn giao.
4. Google Drive là nguồn lưu bản vẽ/hồ sơ, nhật ký nghiệp vụ HMAC, phiên bản và quyền. Không xóa hay ghi đè file cũ, nhật ký được duyệt, tài liệu pháp lý, nhiệm vụ đã ký.
5. Giao việc phân cấp CEO → PM → Trưởng bộ môn → Kỹ sư/Agent → QA/QC; Admin duyệt phân phối; có rút/hủy giao việc và dừng toàn bộ cây theo lý do, giữ kết quả đã duyệt; không tự phê duyệt kỹ thuật.
6. File upload Google Drive mục tiêu **500 MB** qua sheets hiện có (không tạo trang upload riêng); giới hạn file Agent phân tích **50 MiB**; đọc DXF/PDF/XLSX/CSV/IFC có giới hạn và căn cứ; DWG/RVT/NWD không được công bố là đã parse hình học trực tiếp.
7. Nhật ký có sự kiện Agent bắt đầu, hoàn thành, thất bại; phân biệt việc được giao/đang xử lý với bằng chứng worker thật. Không hiển thị tiến độ hoặc báo cáo giả.
8. Báo cáo CAD/MEP/BOQ/BIM/PCCC phải là bản nháp, được kỹ sư kiểm chứng và cấp quản lý duyệt trước khi phát hành; không tuyên bố đạt TCVN/QCVN nếu không kiểm chứng điều khoản.

## 3. NHỮNG GÌ ĐÃ CÓ TRONG MÃ NGUỒN

| Phiên bản | Mức triển khai | Tệp trọng tâm |
|---|---|---|
| V6.9 | Phân cấp có chữ ký, phụ thuộc, duyệt cấp trực tiếp, thu hồi/dừng cây | `drive_storage/hierarchy.py`, `hierarchy_ui.py`, `shared_workspace.py` |
| V7.0 | Văn phòng 3D, dashboard CEO, 18 Agent và phân biệt sự kiện thật | `src/3d/`, `src/core/hq_dashboard.js`, `drive_storage/live_agents.py`, `monitoring.py` |
| V7.1 | Runtime API riêng HMAC, PostgreSQL queue, Celery worker, Redis, heartbeat 10s, stale 90s, idempotency, hủy theo checkpoint, dự trù quota/chi phí | `agent_runtime/api.py`, `models.py`, `queue.py`, `worker.py`, `client.py`, `security.py` |
| V7.2 | LangGraph human-review gate; Admin chọn sau duyệt phân phối CEO để đưa checklist miễn phí xuống PM/Lead/Expert; QA vẫn chờ duyệt | `agent_runtime/graph.py`, `batch.py`, `drive_storage/hierarchy_ui.py` |
| V7.3 | Tài liệu tham khảo được phép nhập với version, citation, SHA256, lexical retrieval; DXF annotation xuất **file mới** có xác nhận kỹ sư; PDF table extraction có giới hạn | `agent_runtime/standards.py`, `cad_tools.py` |
| V7.4 | Provider Anthropic/Ollama tùy chọn worker-only, OpenAI/Gemini dùng vault Drive hiện có; Docker 5 dịch vụ; dashboard/3D có job queued/running/unconfirmed/failed/completed | `agent_runtime/providers.py`, `Dockerfile.agent-runtime`, `docker-compose.v74.yml`, `src/core/agent_live.js` |

**Giao diện sử dụng:** Trong Công việc → Chạy Agent có `Chạy ngay trong Streamlit` (tương thích cũ) hoặc `Đưa Agent vào hàng đợi V7.4` (chỉ khi backend đã cấu hình). Trong Giám sát Agent có bảng CEO và worker queue/heartbeat; trong dialog Agent có xem job và nút thu hồi theo quyền. Admin có thể nhập tài liệu tham chiếu được phép sử dụng ngay trong dialog.

## 4. CHƯA HOÀN THÀNH / KHÔNG ĐƯỢC GẮN NHÃN ĐÃ VẬN HÀNH

**P0 — phải làm đầu tiên khi tiếp tục:** Deploy và xác minh 5 dịch vụ (Streamlit, private agent-api, agent-worker, Redis, PostgreSQL) trên server/VPS hoặc cloud thích hợp, gắn Google OAuth và Drive secrets đã có; kiểm thử nguyên vòng thao tác đa tài khoản. Hiện không có bằng chứng runtime production đã deploy. Streamlit Community Cloud riêng lẻ không có Redis+worker chạy độc lập. Bật runtime qua private `[runtime]` trong Streamlit secrets hoặc env server.

**P0 — kiểm thử an toàn:** Dùng 2 tài khoản Google thật với quyền khác nhau, kiểm tra mất quyền khi job đang chờ, API 401/429, ngắt Redis, DB, worker, kiểm tra không lặp gọi phí và không tạo báo cáo giả; kiểm tra upload 500MB/đọc Agent 50 MiB khi hạ tầng đủ nguồn lực. Đảm bảo HMAC event ledger Drive (giới hạn 2500 sự kiện) không bị đầy, cần cơ chế lưu trữ/đồng bộ lâu dài trước khi chạy quy mô lớn.

**P1 — hiệu năng:** mặc định `AGENT_WORKER_CONCURRENCY=4`, `AGENT_QUEUE_MAX=100`; nâng lần lượt 2→4→8→12→18 sau stress test thực tế CPU/RAM/RPS/TPM/API quota và file DXF/IFC lớn. **Không có kết quả nghiệm thu 18 Agent đồng thời**.

**P1 — chuyên môn:** RAG đang là tra cứu từ khóa có nguồn, chưa có embedding/vector pgvector; LangGraph hiện là cổng QA/human review định hướng, không phải hệ thống AI CEO tự suy nghĩ/phân phối toàn bộ; CAD mới xuất DXF bản sao có ghi chú, chưa tự dựng BIM geometry, clash, DWG/RVT shopdrawing hoàn chỉnh; `actualCostUsd` chưa có usage thật từ provider và đang là null.

**P1 — kiểm soát rủi ro:** job running chỉ hủy tại checkpoint, **không ngắt ngay request LLM/CAD giữa chừng**; cần phương án backup & restore PostgreSQL, bảo vệ network/TLS, lock/race/cost concurrency và điều tra crash/recovery trước khi dùng thương mại.

## 5. QUY TRÌNH TRIỂN KHAI VÀ NGHIỆM THU

1. Kiểm tra repository `main`, HEAD mới nhất, `VERSION_MANIFEST.json`, CI. Không giả định bản GitHub và site Streamlit đã giống nhau.
2. Giữ bí mật ngoài Git, không yêu cầu người dùng gửi API key/token trực tiếp trong chat. Dùng `.env.v74.example` làm mẫu; xác nhận các secrets cho OIDC, root Drive, HMAC runtime, PostgreSQL. Giữ nguyên `auth.cookie_secret` đã mã hóa vault API (thay sẽ cần phục hồi vault).
3. Triển khai `docker compose --env-file .env.v74 -f docker-compose.v74.yml up -d --build` trên server thực, cấu hình HTTPS/Google login redirect; chỉ mở cổng Streamlit qua reverse proxy, không public Redis/PostgreSQL/API.
4. Xác nhận trạng thái /health, khả năng tạo job qua dialog, chuyển queued→running với heartbeat→completed draft, khả năng cancel, fail, revocation, QA quay lại, 2 thiết bị quan sát đồng nhất.
5. Chạy hồi quy: `python -m unittest discover -s tests -p 'test_*.py'`, `python -m unittest discover -s agent_runtime/tests -p 'test_*.py'`, `npm test`. Xem workflow GitHub cho code branch mới.
6. Dùng file chuyên môn đã ghi sổ Google Drive (ví dụ mẫu tủ điện DXF) để thử kết quả hash, chứng cứ CAD, số liệu phát hiện, QA quyết định và báo cáo nháp; không sửa file gốc. Chạy thử tải theo bậc, không tự động bật 18 worker.
7. Chỉ công bố “đã chạy 18 Agent đồng thời/đạt chuẩn” khi có log, hiệu năng, chi phí, nghiệm thu, dữ liệu kỹ thuật được kiểm chứng và chứng cứ; điều kiện chưa đạt phải giữ trạng thái BLOCKED/PENDING.

## 6. CÁC LIÊN KẾT & TỆP CẦN ĐỌC TRONG CUỘC TRÒ CHUYỆN MỚI

- [Repo main](https://github.com/Manhhung114/Cong_ty_XD_3D)
- [VERSION_MANIFEST.json](https://github.com/Manhhung114/Cong_ty_XD_3D/blob/main/VERSION_MANIFEST.json)
- [Hướng dẫn triển khai tích hợp V7.4](https://github.com/Manhhung114/Cong_ty_XD_3D/blob/main/docs/V740_INTEGRATED_AGENT_RUNTIME.md)
- [Hướng dẫn giám sát 3D V7.0](https://github.com/Manhhung114/Cong_ty_XD_3D/blob/main/docs/V700_3D_HQ_AGENT_MONITORING.md)
- [Sơ đồ phân cấp V6.9](https://github.com/Manhhung114/Cong_ty_XD_3D/blob/main/docs/V690_HIERARCHICAL_AI_TASK_ORCHESTRATOR.md)
- [Docker Compose V7.4](https://github.com/Manhhung114/Cong_ty_XD_3D/blob/main/docker-compose.v74.yml)
- [Runtime code](https://github.com/Manhhung114/Cong_ty_XD_3D/tree/main/agent_runtime)
- [PR #22](https://github.com/Manhhung114/Cong_ty_XD_3D/pull/22)
- [CI Streamlit](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44084933264)
- [CI Runtime](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44084933075)
- [CI Android debug](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44084933146)

## 7. LỆNH MỞ ĐẦU CHO CUỘC TRÒ CHUYỆN MỚI (SAO CHÉP NGUYÊN ĐOẠN)

> Tiếp tục dự án **Công ty XD & MEP AI 3D** từ gói bàn giao **V7.4.0**. Mở GitHub `Manhhung114/Cong_ty_XD_3D`, nhánh `main`, đọc `docs/handoffs/2026-11-17_V740_BAN_GIAO_CUOC_TRO_CHUYEN_MOI.md`, `VERSION_MANIFEST.json`, `docs/V740_INTEGRATED_AGENT_RUNTIME.md`, kiểm tra HEAD và GitHub Actions mới nhất. Baseline mã nguồn đã đạt CI là `f18062493035530a706da443598c5e29496cba10` (HEAD có thể mới hơn do commit tài liệu). Giữ nguyên Google OAuth, dữ liệu Drive, 18 Agent, 3D WebGL, phân cấp CEO→PM→Lead→Expert→QA, vault API dùng chung và các tính năng hoàn thành V7.0. Mã nguồn V7.1–V7.4 đã merge qua PR #22, nhưng **PostgreSQL, Redis, Celery chưa được nghiệm thu triển khai thực tế**. Ưu tiên đánh giá cấu hình hạ tầng worker/HTTPS, triển khai & test hàng đợi thật, heartbeat, hủy/retry, hai tài khoản Google, DXF mẫu và load test tăng dần từ 4 lên 18 worker. Không tuyên bố 18 Agent đang chạy hay tuân thủ tiêu chuẩn nếu thiếu bằng chứng. Sau mỗi thay đổi phải kiểm thử và cập nhật GitHub, không xóa hay ghi đè dữ liệu cũ. Hãy kiểm tra và báo cáo trạng thái trước khi thực hiện yêu cầu tiếp theo.

---
**Bảo mật:** Không đính kèm token, key, private credentials, file khách hàng hoặc bản export dữ liệu Drive. Chỉ đính kèm gói bàn giao kỹ thuật, đường dẫn mã nguồn đã xác minh, checklist và trạng thái chưa nghiệm thu.
