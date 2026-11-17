# V7.5 · Nghiệm thu ứng viên thí điểm

Mã nền `main@3c066d0951418f8b783746a6b3bafaaefcdd6d6c`, kế hoạch và ma trận ở nhánh V7.5. Nhánh phát hành chính vẫn dùng V7.4. Cấu hình và nhật ký triển khai thật trên Streamlit Cloud chưa được xác minh vì bước đăng nhập GitHub trả lỗi máy chủ.

| Mốc | Phạm vi đã chạy / điều kiện còn mở |
|---|---|
| M0 | Đã xác nhận mã nền, cấu hình repo 500 MB và bộ test hồi quy. Cần kiểm tra branch, entrypoint, Python và log trên Streamlit. Chưa đối chiếu sao lưu hoặc phục hồi dữ liệu Drive thật. |
| M1 | 20 ID, giữ nguyên 18 profile gốc, 16 phòng, kiểm tra phát lại nhật ký mẫu có HMAC. |
| M2 | QCX cho cây xây dựng thí điểm tạo mới, giữ QAC trong hồ sơ cũ và cây MEP. Giao QCX cần nhân sự độc lập trong dự án, quyền được kiểm tra lại khi chạy. LEG chỉ hiển thị hồ sơ năng lực, chặn chạy và đọc tệp qua Agent. Chưa có cổng ACL hợp đồng riêng và chưa nghiệm thu với hai tài khoản Google thật. |
| M3 | Có 20 hồ sơ năng lực, công thức nháp Điện/HVAC/Cấp thoát nước/PCCC/Kết cấu, CPM và kiểm mẫu ITP/NCR. Chưa nghiệm thu đầy đủ từng hồ sơ năng lực, tiêu chuẩn có hiệu lực và bộ số liệu đối chiếu ký duyệt bởi chuyên gia. |
| M4 | Kiểm thử JavaScript và bản dựng frontend Streamlit. Quy trình CI ghi nhận WebGL và SVG ở 390, 820, 1440 px. |
| M5 | Có kiểm thử PostgreSQL, Redis, Celery với dữ liệu Drive giả lập và kiểm tra trạng thái hàng đợi/hủy. Cần log máy chủ sản xuất, OIDC/Drive thật, thu hồi quyền và diễn tập phục hồi. |
| M6 | Có chiến dịch cấu hình 2, 4, 8, 12, 18 worker dùng preflight với dữ liệu tổng hợp miễn phí. Tải hồ sơ thật, hạn mức nhà cung cấp, chi phí, thời gian và tài nguyên máy chủ thật vẫn cần đo. |
| M7 | Ứng viên riêng, mặc định tắt tính năng. Chờ hoàn tất các điều kiện trên, phê duyệt nghiệp vụ và diễn tập quay lui trước khi merge và phát hành. |

## Kết quả thử tải tổng hợp

Mỗi dòng là một lượt preflight cho mỗi slot Celery, qua PostgreSQL và Redis nội bộ. Các job hoàn tất đúng một lần, có ID kết quả và chi phí dự trù bằng 0. Thử hủy khi đang chạy tại checkpoint và thử từ chối tài khoản bị thu hồi trên fixture đã đạt.

| Slot Celery | Số job hoàn tất | Thời gian lô (s) | Job chậm nhất (s) |
|---:|---:|---:|---:|
| 2 | 2 | 1,392 | 1,262 |
| 4 | 4 | 1,384 | 1,303 |
| 8 | 8 | 1,727 | 1,478 |
| 12 | 12 | 3,422 | 2,918 |
| 18 | 18 | 3,853 | 3,504 |

## Bật trên môi trường thí điểm sau khi đạt điều kiện

Cấu hình **biến môi trường máy chủ** `XD_V75_CATALOG=1` và `XD_V75_CANARY_PROJECTS` là các ID dự án thí điểm đã được cấp quyền, phân cách bằng dấu phẩy. Bật thêm `XD_V75_QCX=1` để tạo cây có QCX. Dùng biến giống nhau trên Streamlit, private API và Celery nếu thử hàng đợi. Cấu hình độc lập với Secrets hiện hữu. Chỉ dùng bản sao dự án đã được cho phép. Hệ thống tạm chặn tạo/duyệt phương án V7.5 từ 2.250 sự kiện trong kho giới hạn 2.500.

Tại **Cơ cấu nhân sự**, Admin phân công QA/QC Xây dựng cho người có quyền cập nhật dự án, độc lập với người lập và người thực hiện hồ sơ. Chỉ đề xuất mới trong canary được ghi chính sách V7.5. Kiểm tra QCX chỉ dùng hồ sơ xây dựng đã duyệt thuộc nhiệm vụ hoặc bước chuyên gia mà nhiệm vụ QC phụ thuộc. LAB/ITP/NCR được kiểm trên dòng mẫu, sau đó người có thẩm quyền đọc chứng từ gốc và duyệt. LEG vẫn bị khóa.

Quay lui bằng cách tắt các cờ trên **cùng bản ứng viên** để giữ khả năng đọc toàn bộ sự kiện đã ký. Sau khi đã có sự kiện QCX, không triển khai lại bản đọc V7.4 trực tiếp trên cùng ledger. Dừng hoạt động thí điểm và đối chiếu chữ ký, revision, bản sao độc lập và quyền truy cập trước chuyển đổi máy chủ.

## Chạy lại kiểm thử

- `python -m unittest discover -s tests -p 'test_*.py'`
- `python -m unittest discover -s agent_runtime/tests -p 'test_*.py'`
- `npm test`
- `python -m compileall -q drive_storage agent_runtime streamlit_app.py`
- CI **Verify V7.5 Canary** dựng Redis và PostgreSQL riêng, khởi động Celery thật và chạy Playwright trên bundle Streamlit đã xác thực giả lập. Bộ thử dùng tài khoản, tệp và khóa tổng hợp. Không gọi provider AI hoặc Google.
