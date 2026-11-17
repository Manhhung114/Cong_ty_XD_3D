# V7.5.2 — Quy trình giao việc, phối hợp đa bộ môn và họp giải quyết vướng mắc

**Trạng thái:** Feature branch; chờ CI, kiểm thử Drive thật, hai tài khoản Google và xác nhận Streamlit.  
**Định hướng:** Giữ Streamlit Community Cloud, Google Drive signed event ledger, các chức năng V7.5.1, 20 Agent và 18 phòng.  
**Quan trọng:** Chức năng họp mới mặc định TẮT; chỉ bật tại dự án thí điểm sau khi đã triển khai trình đọc mới và thử nghiệm sao lưu.

## 1. Ba con đường tiếp nhận công việc (không nhân bản cơ sở dữ liệu)

| Trường hợp | Lối vào | Hệ thống tạo | Điều kiện kiểm soát |
|---|---|---|---|
| Tổng hợp nhiều bộ môn | Công việc → Tạo → Giao Giám đốc AI | Công việc CEO + phương án sơ bộ HMAC để Admin duyệt | Chỉ chọn 1–4 bộ môn có căn cứ; mơ hồ phải chọn thủ công; không gọi LLM giả |
| Chuyên ngành rõ | Công việc → Tạo → Giao trực tiếp | Công việc cho ELE/HVA/PLU/FIR/STR... | Người có quyền Cập nhật, đúng dự án/bộ môn |
| Có vướng mắc liên bộ môn | Công việc → Họp phối hợp, hoặc Phối hợp & Họp → Tạo | Cuộc họp gắn 1–5 công việc + 2–8 bộ môn | Hồ sơ/vấn đề có thật, không tự thay quyền project |

**Không tự duyệt**: Agent là người đề xuất; một quyết định giao nhiều nhóm công việc phải có Admin xác nhận.

## 2. Chuỗi thực thi chung

1. **Tiếp nhận**: chọn dự án được cấp, ghi yêu cầu, mã hồ sơ/revision, độ ưu tiên, thời hạn, trách nhiệm.
2. **Xác định bộ môn**: CEO đề xuất dựa trên từ khóa, hoặc PM/Trưởng bộ môn điều phối trực tiếp. Tập hợp liên ngành không mặc định giới hạn vào một bộ môn nếu có xung đột.
3. **Giao việc có truy vết**: sinh các nhiệm vụ theo cây CEO→PM→Lead→Expert→QA (khi Admin duyệt) hoặc giao trực tiếp. Task ID và project ID không đổi; thêm nhiệm vụ không tái ghi sự kiện cũ.
4. **Kiểm tra dữ liệu đầu vào**: Agent kiểm tra phạm vi, tài liệu đã đăng ký, revision, quyền được cấp và kết quả công cụ thật. Thiếu dữ liệu → NEED_INPUT/BLOCKED, không bịa kết quả.
5. **Phối hợp ngang**: nếu vướng giữa các hệ, dùng phiếu yêu cầu phối hợp sẵn có; nếu cần quyết định của nhiều bộ môn, tổ chức họp.
6. **Họp phối hợp V7.5.2**: mở từ một hoặc nhiều công việc, chỉ định người/bộ môn, ghi agenda và thời gian; sau họp ghi minutes, kết luận, 0–6 đầu việc có email người chịu trách nhiệm, bộ môn và hạn.
7. **Duyệt kết luận**: Admin xem toàn bộ minutes, đầu việc và phân công, lựa chọn Duyệt hoặc Trả lại; chỉ lúc DUYỆT hệ thống mới tạo nhiệm vụ có mã CV-* bằng một sự kiện HMAC atomically replayable. Chỉ lưu bản DRAFT nếu chưa duyệt.
8. **Thực hiện/kiểm tra**: từng đầu việc được chuyên gia thực hiện, lưu báo cáo DRAFT, QA độc lập thẩm tra; Admin hoặc cấp quản lý đủ quyền xét duyệt theo quy tắc hiện hành.
9. **Khóa vấn đề**: chỉ khi tất cả đầu việc sau họp đạt trạng thái DONE mới cho Admin đóng cuộc họp. Các cuộc họp chưa hoàn thành vẫn được hiển thị ở bảng điều hành.
10. **Lưu và truy vết**: event ID, creator, approver, ngày giờ, task IDs; giữ bản gốc/revision và ký HMAC bằng khóa hiện tại.

## 3. Trạng thái vận hành

**Công việc:** todo → working → review → done; returned → working; cancelled bị chặn tạo phối hợp mới.  
**Phương án CEO:** pending → approved/dispatched hoặc rejected.  
**Phiếu phối hợp:** open → resolved.  
**Họp:** scheduled → pending_approval → in_progress → closed; hoặc pending_approval → revision_requested → pending_approval.  
**Agent:** queued / running / unconfirmed / draft / failed chỉ khi có sự kiện thật. Không suy diễn Agent hoàn thành từ trạng thái công việc.

## 4. Trách nhiệm (RACI vận hành)

| Giai đoạn | Phụ trách | Duyệt | Phối hợp |
|---|---|---|---|
| Tiếp nhận và phân loại | PM/CEO | Admin cho cây phân phối | ELE/HVA/PLU/FIR/BIM/ARC/STR |
| Phân công chuyên môn | PM/Lead | Quản lý cấp trực tiếp | Kỹ sư chuyên ngành và kế hoạch |
| Giải quyết xung đột kỹ thuật | Chủ trì cuộc họp / PM | Admin duyệt kết luận liên phòng | MEP, XD, BIM/XBI, SITE, MAT, QCX/QAC |
| Chạy công cụ kỹ thuật | Kỹ sư/Agent bộ môn | Người thẩm tra độc lập | QA/QC, DOC, HSE khi có an toàn |
| Kiểm tra QA, NCR/CAR | QAC hoặc QCX theo loại việc | Người đủ thẩm quyền trong workflow | Chuyên gia và PM |
| Phát hành hồ sơ/bàn giao | DOC/PM | Admin/người ký có thẩm quyền | QS, QA, pháp chế (chỉ khi được cấp quyền) |

LEG **chưa được tự đọc hợp đồng**; mọi thông tin nhạy cảm giữ nguyên ACL. QCX vẫn chỉ chạy trong canary đã duyệt. Họp không tự cấp quyền đăng nhập cho người được giao việc.

## 5. Tối giản giao diện trên Streamlit

- **Công việc:** một form hai chế độ "Giao Giám đốc" / "Giao trực tiếp"; bộ môn/Agent ẩn nếu đã chọn CEO. Sau khi lưu CEO, phản hồi ngay phương án chờ duyệt hoặc thiếu dữ kiện cần chọn.
- **Từng thẻ công việc:** nút Họp phối hợp (khi bật), nút phân công/chạy Agent, trạng thái cản trở, nhiệm vụ phát sinh từ cuộc họp.
- **Phối hợp & Họp:** một bảng tổng hợp việc cần xử lý, phiếu chuyển phòng và cuộc họp; nút phù hợp theo trạng thái (ghi minutes, duyệt kết luận, đóng), không hiển thị thao tác người Chỉ đọc không có quyền.
- **Họp:** 1–5 công việc gốc; 2–8 bộ môn; tối đa 6 đầu việc sau họp để giới hạn event và giao diện di động. Không ghi âm, không khởi tạo Google Meet và không tự mời email (chưa có tích hợp lịch).
- **Mobile:** các bước được nhóm ngắn, nút theo trạng thái và vùng chạm đủ lớn; xác thực và ghi sự kiện chỉ diễn ra ở Streamlit server.

## 6. Kiến trúc dữ liệu bảo toàn

- Dùng **cùng** SharedWorkspace HMAC Drive ledger, không tạo file nhị phân mới hoặc kho công việc song song.
- Thêm loại sự kiện (được signed): meeting.created, meeting.minutes, meeting.approved, meeting.revision_requested, meeting.closed.
- meeting.approved tạo tối đa 6 nhiệm vụ có ID deterministic tính từ event ID duyệt và chỉ hiển thị sau khi duyệt (replay một event). Sự kiện cũ không sửa và không đổi chữ ký.
- Một khi production có sự kiện meeting.* V7.5.2, phiên bản V7.5.1 cũ KHÔNG được đọc trực tiếp ledger mới vì chưa nhận action mới. Rollback an toàn: dùng bản trình đọc V7.5.2 và tắt cờ XD_V752_MEETINGS, không redeploy trình đọc cũ.
- Chỉ bật trên production sau backup/restore và test với 2 tài khoản, kiểm soát max ledger 2500 event (điểm chặn ở 2250), kiểm tra replay.
- Feature flag mặc định **XD_V752_MEETINGS=0**, bật =1 trên môi trường test sau khi xác minh cách khôi phục, không yêu cầu thay đổi Secrets cũ.

## 7. Kiểm thử & điểm chặn nghiệm thu

- Python tests: suggest_departments có dấu/không dấu, idempotent CEO, meeting draft, Admin-only approve, cross-project deny, không nhân đôi task, QA review trước khi close, HMAC old blob unchanged, version flag OFF.
- JS tests: giao diện phân quyền, nút họp theo trạng thái, encode nội dung cuộc họp tránh XSS, bridge truyền projectId/meetingId đúng.
- Nền tảng: source == static bundle, compileall và npm test, GitHub Actions.
- **Chưa thay thế**: hai tài khoản Google thật, Streamlit Cloud login/browser, thử tải file 50 MiB/500 MB, Redis/PostgreSQL/Celery production và 20 Agent thực thi trả phí.

## 8. Điều kiện triển khai

1. Merge mã và có bằng chứng kiểm thử unit/browser đúng SHA.
2. Backup Drive signed ledger/files và ghi baseline, chạy restore rehearsal.
3. Deploy trên Streamlit với flag OFF, kiểm tra hiện trạng V7.5.1 trước/sau.
4. Bật flag cho dự án kiểm thử phù hợp (cờ hiện ở mức máy chủ, project scope vẫn được kiểm tra), chạy đủ luồng họp và phân quyền.
5. Kiểm kết quả, lỗi, quyền và rollback; chỉ sau đó duyệt phát hành chính thức.

**Không được tuyên bố production hoàn tất hoặc AI Agent tự họp/ra quyết định khi mới chỉ có nhật ký cuộc họp và kết luận của người dùng.** Tương lai có thể nối từng bước tổng hợp đề xuất kỹ thuật vào LLM worker thật, sau khi có consent/cost/identity checks.
