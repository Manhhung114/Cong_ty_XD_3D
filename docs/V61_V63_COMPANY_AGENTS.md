# V6.1–V6.3 — Công ty Xây dựng & MEP AI 3D: Điều phối Agent và vận hành tập trung

**Chức năng thực sự:** quản lý 18 Agent chuyên môn (đúng 16 phòng/khối đang có), chọn nhiệm vụ theo dự án, kiểm tra bằng chứng đầu vào theo bộ môn, tùy chọn gọi OpenAI/Gemini thật trên máy chủ, lưu báo cáo nháp có nhật ký, tạo và theo dõi phiếu phối hợp liên phòng, kiểm soát KPI công ty theo dữ liệu Google Drive đã ký, sao lưu metadata và kiểm tra tính toàn vẹn.

**Không tuyên bố:** Agent tự động bóc tách nội dung DWG/RVT/IFC/PDF/Excel, tính ngắn mạch/khối lượng/hệ thống PCCC, phát hiện va chạm hình học, tính tải lạnh hoặc thay kỹ sư kiểm tra. **Không có chức năng ký số hay duyệt thay Admin.** Agent chỉ được cấp *metadata* của task, project, mã hồ sơ và revision đã được người dùng đồng ý chia sẻ. Chưa có PostgreSQL chạy sản xuất, hàng đợi Agent chạy nền hay cảnh báo push.

## V6.1 – 18 Agent có chức trách và kiểm chứng rõ ràng

| Agent | Phòng ban | Chuyên môn / kết quả bàn giao | Hồ sơ mong đợi |
|---|---|---|---|
| CEO | Điều hành | Phân nhóm rủi ro, ưu tiên dự án & yêu cầu ra quyết định | Báo cáo điều hành / tiến độ |
| PM | Điều hành | Nhiệm vụ, hạn và phụ thuộc các phòng | Tiến độ / báo cáo điều hành |
| ELE | Điện | Checklist điện, danh mục thiết bị & dữ liệu cần tính | Bản vẽ MEP / BOQ MEP |
| HVA | HVAC | Checklist HVAC, tải lạnh & vấn đề cần xác minh | Bản vẽ / BIM MEP |
| PLU | Cấp thoát nước | Checklist nhu cầu nước, áp lực, bơm, thoát nước | Bản vẽ / BIM MEP |
| FIR | PCCC | Hồ sơ thử nghiệm, nghiệm thu, tiêu chuẩn cần kiểm chứng | PCCC / bản vẽ |
| BIM | BIM MEP | Phối hợp giữa mô hình và yêu cầu kiểm tra clash | BIM / bản vẽ MEP |
| QSU | QS MEP | Checklist mã công tác, đơn vị và thay đổi BOQ | BOQ MEP |
| QAC | QA/QC MEP | Checklist QA, biên bản thử nghiệm, tồn tại | Báo cáo / phê duyệt |
| DOC | Kiểm soát hồ sơ | Revision, mã hồ sơ, lịch sử phát hành | Thông tin dự án / phê duyệt |
| ARC | Kiến trúc | Mặt bằng, giao diện và vấn đề hoàn thiện | Bản vẽ XD |
| STR | Kết cấu | Hồ sơ cấu kiện, giao diện, giả thiết cần kỹ sư tính | Bản vẽ XD |
| XBI | BIM XD | Phối hợp IFC/RVT kiến trúc-kết cấu | BIM XD / bản vẽ XD |
| XQS | QS XD | Kiểm tra mã BOQ, đơn vị và phát sinh | BOQ XD |
| PLN | Kế hoạch | Chậm tiến độ, mốc, công việc phụ thuộc | Tiến độ |
| SIT | Hiện trường | Nhật ký, biện pháp thi công, vấn đề hiện trường | Ảnh / báo cáo XD |
| HSE | QA/HSE XD | Checklist nguy cơ an toàn, khắc phục và hồ sơ nghiệm thu | Ảnh / báo cáo XD |
| MAT | Vật tư | Danh mục vật tư, nguồn cung và trình mẫu | Báo cáo / hợp đồng |

**Chất lượng đầu ra bắt buộc:** (1) dẫn rõ mã/revision nếu có, (2) tách dữ kiện với giả thiết, (3) chỉ rõ bằng chứng thiếu, (4) xác định bộ môn chịu trách nhiệm kiểm tra tiếp, (5) không tự chuyển trạng thái hồ sơ hay duyệt quyết định.

### Cách chạy

1. Đăng nhập bằng Google với vai trò **Admin** hoặc **Cập nhật** và được cấp quyền dự án.
2. Tạo một công việc trong **Công việc**: tên, bộ môn, người phụ trách, mức độ ưu tiên, hạn và mã hồ sơ.
3. Mở **Nhân viên AI**, chọn dự án và Agent đúng bộ môn. Agent PM/CEO/DOC/QAC có thể hỗ trợ kiểm tra phối hợp liên bộ môn.
4. Chọn công việc → **Chạy Agent**. Mặc định **Kiểm tra checklist (không AI)** hoạt động mà không cần API. Báo cáo lưu dưới dạng quy tắc và **không được gọi là AI**.
5. Khi Admin cấu hình nhà cung cấp thật, người chạy có thể chọn **Chạy AI thực** và phải xác nhận đồng ý gửi metadata. Kết quả lưu vào sự kiện `agent.completed` đã ký, có email người thao tác và vẫn là **nháp**.
6. Chỉ Admin và kỹ sư được phân quyền được quyết định phê duyệt qua quy trình hồ sơ/công việc hiện hành. Agent **không** gọi phê duyệt hay ghi đè tệp.

### Cấu hình AI thật (tùy chọn)

Tại **Streamlit Cloud → App settings → Secrets**, giữ nguyên tất cả `[auth]`, `[drive]`, `[access]` hiện có và thêm đúng một nhóm (chọn **một** trong hai):

```toml
[ai]
provider = "openai"
model = "gpt-4.1-mini"
api_key = "KHOA_OPENAI_CUA_BAN"
```

hoặc:

```toml
[ai]
provider = "gemini"
model = "gemini-2.5-flash"
api_key = "KHOA_GEMINI_CUA_BAN"
```

Đây là ví dụ cấu hình; tài khoản AI của công ty phải có quyền sử dụng model tương ứng. Không thêm API key vào GitHub, browser LocalStorage hoặc chat công khai. Phần **Cài đặt API** cũ của giao diện 3D không tự động đồng bộ lên server; nguồn key cho tác vụ mới là Streamlit Secrets. Nếu chưa có `[ai]`, toàn bộ tính năng quản lý Agent và kiểm tra checklist vẫn hoạt động; **không gọi API trả phí**.

Lệnh gọi model đến endpoint chính thức với timeout 25 giây, giới hạn dữ liệu/nội dung và quota thô 30 lần/ngày cho một email dựa trên lịch sử gần đây. Cần thiết lập quota và ngân sách ở tài khoản nhà cung cấp để bảo đảm chi phí tuyệt đối. Metadata task, project và tên/mã hồ sơ có thể được gửi ra nhà cung cấp **chỉ sau khi người dùng đồng ý**; mặc định không đưa file gốc lên AI. Prompt injection và hallucination được hạn chế bằng chỉ dẫn hệ thống và kiểm tra trước/sau; **chưa thể đảm bảo loại bỏ hoàn toàn**. Lệnh chạy lặp có mã sự kiện cũ được tra cứu trước để không gọi lại AI có phí.

## V6.2 — Tổ chức công ty và luồng phối hợp

**Điều hành công ty** sử dụng dữ liệu thật từ các dự án người đăng nhập được cấp quyền:

- Danh mục dự án, tổng nhiệm vụ, đang làm, chưa phân công, ưu tiên cao/khẩn, quá hạn, chờ duyệt, hồ sơ chờ xử lý, phiếu phối hợp đang mở.
- Thống kê theo 16 phòng ban và 18 Agent; báo cáo ưu tiên cần PM/Admin xử lý.
- **RACI** được hiển thị dưới dạng hướng dẫn tổ chức trách nhiệm: PM điều phối; kỹ sư con người chịu trách nhiệm kỹ thuật; QA/DOC kiểm tra; Admin phê duyệt nội bộ; Agent hỗ trợ đề xuất, không phải nhân viên có thẩm quyền ký.
- **Phiếu phối hợp liên phòng**: chọn công việc, chọn phòng nhận, nêu vấn đề/bằng chứng, tạo phiếu ký bằng tài khoản Google. Phòng nhận hoặc nhân viên có quyền cập nhật dự án viết phản hồi; lưu người trả lời và trạng thái đã giải quyết.
- Không tự chuyển người phụ trách/công việc và không tự gửi email/push. Phiếu phối hợp được xem sau khi người dùng tải lại dữ liệu.
- Admin xem dữ liệu tất cả dự án; tài khoản Cập nhật/Chỉ đọc chỉ xem dự án được cấp quyền. Vì phân quyền hiện chủ yếu theo *dự án* chứ chưa theo từng phòng ban, hệ thống chưa đảm bảo chỉ nhân viên đúng bộ môn mới được đóng phiếu. Chức năng này cần mở rộng danh sách nhân sự/ACL bộ môn trước khi vận hành quy mô lớn.

## V6.3 — Kiểm tra dữ liệu và sao lưu

Trong **Điều hành công ty**, chỉ Admin thấy **Kiểm soát hệ thống & sao lưu**.

- Đọc lại toàn bộ sự kiện Google Drive và kiểm chữ ký HMAC-SHA256 bằng `[auth].cookie_secret`. Nếu lỗi chữ ký/tệp mất, từ chối xuất bản sao.
- Tổng hợp rủi ro từ công việc quá hạn, chưa phân công, phối hợp chưa xử lý, hồ sơ chờ duyệt và ưu tiên cao.
- Xuất `XD_MEP_BACKUP_V63_YYYYMMDD...json` gồm metadata dự án, công việc, lịch sử phối hợp, kết quả Agent nháp và event ledger. Có SHA-256 để kiểm tra tính toàn vẹn file xuất.
- **Không có API key, refresh token hay file nhị phân trong bản sao.** File gốc vẫn trên Drive; cần sao lưu riêng bằng cơ chế Drive của công ty.
- Không có nút **Khôi phục ghi đè** tự động, để tránh hỏng dữ liệu nhiều người dùng; phục hồi cần thủ tục có đối chiếu và khóa tác vụ.
- Giữ nguyên dữ liệu dự án, tài liệu và revision của V6.0.1. Tất cả các sự kiện mới đều dùng cơ chế ký hiện có. **Không đổi `[auth].cookie_secret`** nếu chưa có kế hoạch đổi khóa, vì chính sách người dùng và event ledger đã ký sẽ không đọc được.

## Kỹ thuật và giới hạn

| Thành phần | Đã thực hiện | Chưa thực hiện |
|---|---|---|
| 18 Agent | Tất cả có catalog, kỹ năng, kiểm tra đầu vào và tùy chọn AI thực | Chưa có 18 công cụ tính toán vật lý/geometry độc lập |
| Orchestrator | Điều phối theo công việc/dự án, RACI, phiếu handoff | Không có hàng đợi nền hoặc đa tác vụ tự động |
| AI API | Tùy chọn OpenAI/Gemini qua máy chủ; mã nguồn có mock tests | Chưa kiểm thử trên tài khoản provider thực của công ty |
| BIM | Quản lý IFC/RVT qua metadata/Drive và checklist phối hợp | Chưa có trình xem hình học IFC hoặc clash engine |
| QMS/QA | Audit ký HMAC, kiểm tra trạng thái, bước duyệt con người | Chưa có ký số pháp lý và kiểm định theo tiêu chuẩn có hiệu lực |
| Dữ liệu | Streamlit + Google Drive signed ledger, sao lưu metadata | Chưa có PostgreSQL production, transaction và sao lưu DB theo lịch |
| Vận hành | CI test Python/JS, kiểm tra roles và tính toàn vẹn | Chưa nghiệm thu nhiều người dùng, tải 500MB, thử hồi phục thảm họa |

## Kiểm tra nghiệm thu thực tế

1. Tài khoản Admin thấy Điều hành công ty, đủ 18 Agent, đúng nhóm phòng ban; tài khoản Chỉ đọc không có nút chạy Agent/tạo phối hợp/xuất sao lưu.
2. Tài khoản Cập nhật tạo task Điện → ELE chạy checklist, có thông báo thiếu bản vẽ, kết quả lưu nhưng không thay đổi trạng thái task.
3. Không thể dùng HVA chạy task Điện bằng nút hay lệnh giả; không thể xem task thuộc dự án chưa được cấp.
4. Cấu hình key AI trên server, thử một yêu cầu nhỏ, kiểm tra người dùng đã đồng ý chia sẻ metadata và không lộ key lên frontend/GitHub.
5. Phiếu phối hợp Điện → BIM, người trả lời ghi nội dung, Admin xem trạng thái đã giải quyết trên máy khác.
6. Đặt một nhiệm vụ hạn trong quá khứ, kiểm tra dashboard quá hạn và cảnh báo PM.
7. Admin xuất bản sao và kiểm toàn bộ event signatures. Giữ file gốc Drive riêng; không thử restore trực tiếp vào dữ liệu thật.
8. Xác nhận Kho tài liệu V6.0.1 vẫn kiểm kê R01/R02 và đăng nhập Drive không thay đổi.
9. Kiểm tra các báo cáo AI có nguồn đã ghi sổ và disclaimer chưa đọc file gốc; không phát hành kết luận kỹ thuật tự động.
10. Với hơn 2.500 sự kiện Drive, số liệu sẽ cần PostgreSQL có phân trang/transaction: đây vẫn là điều kiện nâng cấp sản xuất.

**Trạng thái bàn giao:** mã nguồn V6.1–V6.3 + unit/JS integration tests. Chỉ xem là **đã nghiệm thu chạy thực tế** sau khi kiểm thử Google OAuth, tài khoản phụ, provider AI thật và tải/khôi phục dữ liệu trong môi trường của công ty.
