# V6.9.0 — Hierarchical AI Task Orchestrator

Ngày: 17/11/2026. Dành cho dự án **Cong_ty_XD_3D** (Streamlit + Google OIDC + HMAC-signed Google Drive events).

## Quy trình mới

1. Admin vào **Cài đặt → Phân quyền** để cấp quyền đăng nhập **Cập nhật** và phạm vi dự án cho những người tham gia. Vai trò tổ chức bên dưới **không** tự cấp quyền truy cập.
2. Trong sheet **Công việc**, Admin bấm **⚙ Cơ cấu tổ chức** để gắn email thực cho Giám đốc, PM, Trưởng bộ môn, Kỹ sư, QA/QC theo dự án và bộ môn. Đây là sự kiện `org.role_set` ký HMAC; có thể thay đổi/thu hồi vị trí, không chỉnh email trên chính sách OAuth.
3. **Tạo công việc cấp Giám đốc** với `Bộ môn = Ban giám đốc`, `Agent = CEO`, và người phụ trách là email người điều hành đã có quyền.
4. Trên thẻ công việc, bấm **🏢 Giám đốc AI lập phương án**. Hệ thống **gợi ý** bộ môn dựa trên từ khóa trong tên/mã hồ sơ; Giám đốc kiểm tra/chỉnh 1–4 bộ môn và gửi phương án có HMAC `hierarchy.proposed`. Đây là **quy tắc điều phối xác định**, không tự gọi Gemini/OpenAI và không tuyên bố CEO đã tự suy nghĩ bằng LLM.
5. Admin bấm **✓ Duyệt phương án CEO**. Nếu **trả lại**, ghi lý do bắt buộc, CEO có thể lập lại phương án. Nếu **chấp thuận**, **một sự kiện HMAC `hierarchy.approved`** tạo đồng thời 1 nhiệm vụ PM và 3 nhiệm vụ / bộ môn được chọn: Trưởng bộ môn → Chuyên gia chuyên ngành và QA/QC kiểm tra độc lập. Mỗi nhiệm vụ có **ID, mã CV-, parentTaskId, rootTaskId, hierarchyStage, dependsOn, assignee, assignedAgentId**, thời điểm, người duyệt và planId. Tạo tối đa 13 nhiệm vụ con/lần. Idempotency qua ID giao dịch.
6. **Phân phối tự động theo cấp** dựa trên danh bạ vai trò đã ký: PM, lead, engineer và QA; nếu chưa cấu hình email đúng vị trí, người phụ trách để trống, chỉ Admin xử lý được. Không biến email được nhập vào quyền truy cập dự án.
7. **Thực hiện:** mỗi Agent chỉ chạy khi người dùng có quyền bấm **Chạy Agent**, không có giả lập worker nền. Kết quả là báo cáo nháp; QA chỉ mở được sau khi công việc chuyên gia đã được duyệt; cấp trên chỉ được trình kết quả khi tất cả nhiệm vụ con đã được duyệt.
8. **Kiểm soát 2 chiều:** Lead duyệt chuyên gia; PM duyệt Lead; Giám đốc được giao duyệt PM; **QA/QC và nhiệm vụ gốc CEO phải do Admin phê duyệt**. Không cho cấp quản lý tự duyệt công việc của chính mình. Trả lại bắt buộc nêu lý do, báo cáo sửa và trình lại; lịch sử bất biến.
9. Thẻ công việc sắp xếp theo cấu trúc cha–con, hiển thị cấp, bộ môn, người được giao, số công việc con đã duyệt, lý do chặn bởi nhiệm vụ tiền nhiệm và trạng thái đã trình / trả lại / hoàn thành.

## Bảo vệ kỹ thuật

- **Không tự cấp quyền.** Role tổ chức chỉ là metadata phân tuyến. Mọi thao tác thật qua tài khoản Google OIDC có `update` hoặc `admin` **và đúng dự án**, xác minh ở Streamlit, không tin dữ liệu iframe.
- **Không tự cấp ngân sách, ký số hoặc nghiệm thu.** Kết quả Agent dựa trên dữ liệu có provenance vẫn là nháp; việc chấp thuận nhiệm vụ không chứng nhận TCVN/QCVN, xác minh DWG/RVT hay kiểm tra giao cắt BIM.
- **Không phát sinh chi phí AI tự động:** phân phối deterministic sau duyệt Admin, chạy Agent thủ công bằng nút và consent hiện hành; không background worker.
- **Không tạo nhiệm vụ trùng:** chỉ 1 phương án đang chờ hoặc đã phân phối cho 1 công việc CEO. HMAC ledger lưu riêng, không sửa hồ sơ Drive gốc.
- **Không cho phê duyệt công việc gốc khi cấp dưới chưa duyệt**, không cho QA chạy trước chuyên gia. Khi quản lý muốn đổi người phụ trách nhiệm vụ con, chỉ cấp trên trực tiếp hoặc Admin.
- **Không xóa đơn lẻ công việc cha có con:** cấm thao tác hủy lẻ để tránh mất liên kết. Admin có nút **Dừng toàn bộ cây phân phối**, bắt buộc nhập lý do và xác nhận. Một sự kiện HMAC `hierarchy.stopped` hủy những công việc chưa duyệt, thu hồi người/Agent; những nhiệm vụ đã duyệt, báo cáo và hồ sơ vẫn giữ nguyên, không hủy ngầm hay xóa dữ liệu.
- **Giới hạn môi trường:** Google Drive event ledger hiện có trần 2.500 sự kiện. Mỗi cây 1–4 bộ môn tạo 4–13 nhiệm vụ, và phê duyệt / Agent chạy tạo thêm sự kiện. Khi tăng quy mô doanh nghiệp sẽ cần PostgreSQL + job queue / worker riêng, không nên tự tăng trần ledger hay tự chạy 18 Agents đồng thời trên Streamlit.

## Checklist nghiệm thu

- [ ] 2 tài khoản Google thật (Admin, PM, lead, engineer, QA) với quyền dự án đúng, tài khoản ngoài dự án bị từ chối
- [ ] CEO tạo đề xuất đúng bộ môn; Admin **trả lại** và CEO gửi lại, không sinh nhiệm vụ giả
- [ ] Admin **duyệt** tạo đúng 1 PM và 3 nhiệm vụ/bộ môn, không trùng khi reload/retry
- [ ] User cấp thấp không thể phân bổ khác dự án/nhận việc người khác/duyệt chính mình
- [ ] Chuyên gia đọc DXF/PDF từ Drive **đã ghi sổ** và lưu báo cáo nháp; QA bị chặn cho tới khi chuyên gia hoàn thành
- [ ] Chỉ người quản lý trực tiếp được duyệt nhiệm vụ cấp dưới; **QA và CEO cần Admin**
- [ ] Thử trả lại, chỉnh sửa, trình lại, các cấp tổng hợp cho tới CEO, xác minh tất cả HMAC events
- [ ] Kiểm tra Web desktop/mobile, dialog dismiss, role roster, cache, cập nhật giao diện không mất file
- [ ] Theo dõi bộ nhớ và số event trên Streamlit; không coi là production enterprise tới khi nghiệm thu thực tế.

**Giới hạn hiện tại:** chưa có lời gọi LLM để CEO tự sáng tạo kế hoạch, chưa tự chạy nền sau khi duyệt; quy trình “tự phân phối” nghĩa hệ thống tự tạo / gán nhiệm vụ theo sơ đồ được Admin chấp thuận. Nâng cấp LLM planning và autonomous workers chỉ triển khai khi có job queue, giới hạn token, phê duyệt và replay/audit.
