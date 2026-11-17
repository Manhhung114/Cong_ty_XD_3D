# Bàn giao GitHub — Tiếp tục Công ty XD & MEP AI 3D V7.5.1

**Ngày kiểm tra:** 17/11/2026 (Asia/Ho_Chi_Minh)  
**Repo:** Manhhung114/Cong_ty_XD_3D | **branch:** main  
**HEAD xác nhận:** 037a7fe594947c61947d4e43a9247519d32ed263  
**Phạm vi:** kiểm tra GitHub/CI/mã nguồn, KHÔNG phải nghiệm thu Streamlit Cloud/Drive production.

## 1. GitHub hiện hành
- [PR #23](https://github.com/Manhhung114/Cong_ty_XD_3D/pull/23): V7.5 plan/test matrix MERGED.
- [PR #24](https://github.com/Manhhung114/Cong_ty_XD_3D/pull/24): V7.5.0 danh mục 20 Agent MERGED.
- [PR #25](https://github.com/Manhhung114/Cong_ty_XD_3D/pull/25): V7.5.1 thêm phòng QCX, LEG MERGED.
- [PR #26](https://github.com/Manhhung114/Cong_ty_XD_3D/pull/26): nhãn phiên bản trên Streamlit tab MERGED.
- VERSION_MANIFEST.json ghi V7.5.1, 20 Agent, **18 phòng**, live_acceptance_recorded=false, postgresql_deployed=false, v74_runtime_deployed=false.
- data/agents_v75.json gồm 18 ID cũ + QCX/LEG; data/agents_v61.json vẫn giữ nguyên dữ liệu 18 Agent.
- drive_storage/v75_rollout.py quy định QCX chỉ có thể bật cho dự án canary qua cờ XD_V75_QCX và XD_V75_CANARY_PROJECTS. LEG chưa có ACL từng hợp đồng, **không được phép thực thi Agent**.

## 2. Bằng chứng CI, giới hạn
- [App/Drive-auth main HEAD 037a7fe](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44120721403): SUCCESS — Python unit (không có token OAuth thật), JavaScript, compile.
- [V7.5.1 candidate a1e1f3a](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44119637071): SUCCESS — runtime test, Chromium/WebGL và SVG với đăng nhập giả lập, **PostgreSQL + Redis + Celery thực chạy trên GitHub Actions với Google Drive giả lập**.
- [Runtime merged main 67fd76a](https://github.com/Manhhung114/Cong_ty_XD_3D/actions/runs/44120040648): runtime SUCCESS, v75-canary SKIPPED (workflow chỉ kích hoạt canary trên event khác push). Không có chứng cứ canary runtime đã chạy lại sau merge trên production.
- Không coi CI là xác thực quyền Google production, worker sản xuất, thanh toán API thực tế, 18 Agent song song hay năng lực CAD shopdrawing.

## 3. Đối chiếu M0–M7
| Mốc | Có bằng chứng nguồn/CI | Còn cần nghiệm thu |
|---|---|---|
| M0 | Plan, matrix, baseline | Sao lưu thật và kiểm logs deployed app |
| M1 | Catalog 20 Agent, bảo tồn 18 ID | So sánh dữ liệu/lịch sử Drive thật |
| M2 | QCX gated và LEG profile | QCX 2 account + reviewer; LEG ACL từng hợp đồng chưa có |
| M3 | Công cụ tính sơ bộ, ITP/NCR, bảng register và IFC revision | Thẩm tra tiêu chuẩn, dữ liệu kỹ thuật thật, giới hạn CAD |
| M4 | 20 Agent, 18 phòng và browser CI PASS | Thiết bị/viewport Streamlit thật |
| M5 | Postgres+Redis+Celery thử trên CI fixture | Host production, OAuth, revoke, backup/restore thật |
| M6 | Batch preflight tổng hợp 2/4/8/12/18 | Tải thật, quota/chi phí, CPU/RAM |
| M7 | PR đã merge, tag V7.5.1 trong manifest | Nghiệm thu production chưa ghi nhận |

## 4. Ưu tiên thực hiện kế tiếp
1. **P0: Streamlit Cloud** — Trong Work/Cloud Browser hoặc với chủ sở hữu: xác nhận app congtyxd.streamlit.app có repo Manhhung114/Cong_ty_XD_3D, branch main, entrypoint streamlit_app.py, mã commit đang chạy đúng, Python/runtime và Deployment logs. Không sao chép Secrets hoặc token vào GitHub.
2. **P0: Dữ liệu và quyền** — Có bản sao lưu có thể khôi phục của Google Drive files và signed journal; đối chiếu event ID/SHA/revision, xác nhận vault không yêu cầu re-enter key; test hai tài khoản với quyền Read/Update/Admin và cross-project.
3. **P0: QCX/LEG** — Thử QCX dự án canary, chuyên gia khác người QC duyệt, QAC lịch sử không bị đổi; LEG vẫn BLOCKED đến khi ACL từng hợp đồng được triển khai và thử độc lập; không tự cấp quyền pháp chế.
4. **P0: Runtime production** — xác minh private PostgreSQL/Redis/Celery, queue, heartbeat, cancel, crash recovery, OAuth revoke trước worker read, idempotency, monitoring/alerts, HTTPS.
5. **P1: Chuyên môn** — ELE có dữ liệu tính chọn cáp/sụt áp được kiểm độc lập, QA/CAD tạo revision mới, standards status chính xác; các bộ môn còn lại có input validation/evidence/human QA.
6. **P1: Tải và nghiệm thu** — đo nguồn lực/cost/quota tải 2→4→8→12→18, không đồng nhất 20 Agent profile với 20 worker; test Drive upload 500 MB và đọc file Agent 50 MiB riêng. Cập nhật release flag chỉ khi các gate có log PASS.

## 5. Nguyên tắc an toàn cho lần triển khai tiếp
- **Không đổi nền tảng:** giao diện vẫn trên Streamlit Community Cloud; không tự deploy Railway hoặc thay DNS.
- **Giữ nguyên** Google OIDC, Google Drive, signed event ledger, dữ liệu cũ, auth.cookie_secret, vault key và Secrets. Không chạy migration/xóa/bổ sung quyền production nếu chưa được chủ sở hữu phê duyệt.
- Chỉ thực hiện thay đổi code qua feature branch, PR và test; tách riêng triển khai/prod acceptance khỏi CI. Không gọi M0–M7 hoàn tất vì thiếu log thực tế.
- Quay lui V7.5 dùng feature flags ở trình đọc mới, **không quay bản V7.4 lên một ledger đã có event V7.5 mới**.

## 6. Prompt tiếp tục trong phiên Work
Tiếp tục Cong_ty_XD_3D V7.5.1 tại main, đọc tài liệu bàn giao này, docs/V750_STAGING_ACCEPTANCE.md, docs/V750_20_AGENT_ACCEPTANCE_MATRIX.md và VERSION_MANIFEST.json; đối chiếu HEAD mới trước khi sửa. Dùng Cloud Browser kiểm tra congtyxd.streamlit.app và log deployed SHA; tự đăng nhập, không gửi Secrets. Tiếp tục các P0 nghiệm thu quyền Google, dữ liệu Drive, QCX/LEG, runtime production và chuyên môn. Báo PASS/FAIL/BLOCKED trung thực.

**Tài liệu chỉ phản ánh trạng thái GitHub ở HEAD ghi trên, phải tái kiểm tra khi có commit mới.**
