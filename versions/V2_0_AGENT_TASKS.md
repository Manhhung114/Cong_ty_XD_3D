# V2.0 — AGENT VÀ NHIỆM VỤ

**Tình trạng:** Demo mô hình điều phối, **không** gọi LLM.

## Đã có

- 10 vai trò Agent theo bộ phận: CEO, PM, Điện, HVAC, CTN, PCCC, BIM, QS, QA/QC, Document Control.
- Giao nhiệm vụ theo phòng ban, trạng thái Kanban, cập nhật thủ công, nhật ký và lưu trên localStorage.
- Nút Chạy mô phỏng: diễn tiến các nhiệm vụ chờ đến Đang thực hiện và Chờ duyệt; **không** tự duyệt hoàn thành.

## File riêng phụ trách

- `src/core/config.js`: cấu hình Agent.
- `src/core/storage.js`: nhiệm vụ, chuyển trạng thái, KPI.
- `src/app.js`: giao diện làm việc, đăng ký form, nhật ký.

## Khi nâng cấp AI thật

- Backend xác thực, Agent SDK hoặc orchestrator tương đương.
- Các công cụ tính kỹ thuật MEP được kiểm chứng, kèm unit và integration tests.
- Quy trình phân quyền, kiểm tra nguồn, Human-in-the-loop, phê duyệt kỹ sư.
