# CHANGELOG — Công ty XD & MEP AI 3D

## 2026-11-15 — V5.7.4: Bỏ mục Công việc trùng lặp

- Bỏ nút `＋ Công việc` cố định ở tất cả các sheet.
- Để biểu mẫu tạo/xử lý công việc duy nhất trong trang **Công việc**.
- Trang **Quản lý dự án** chỉ giữ tạo/chọn dự án, bộ lọc và các số liệu tổng hợp.
- Văn phòng 3D chỉ hiển thị nhiệm vụ theo phòng, không còn nút tạo/giao trùng.
- Không thay đổi cơ sở dữ liệu cục bộ, hồ sơ, revision, phê duyệt hoặc cấu hình Agent.

## 2026-11-15 – V5.7.2: Ban điều hành chung & đơn giản hóa menu

- Bỏ tab Khối Xây dựng riêng, dùng bộ lọc MEP / Xây dựng trong Văn phòng 3D và Nhân viên AI.
- Hiển thị Giám đốc và Trưởng ban QLDA trong cả hai danh sách; MEP 10, Xây dựng 10, toàn công ty 18 Agent không trùng.
- Giữ bộ lọc khi chuyển trang, vẫn hỗ trợ điều hướng cũ, không xóa hồ sơ hoặc thay mã Agent.
- Cập nhật kiểm thử lọc bộ phận và Android versionCode 59.

# CẬP NHẬT V5.7.1 — 15/11/2026

- Gỡ chế độ demo và menu phê duyệt trùng, giữ một quy trình xác thực theo máy chủ.
- Loại bỏ nhiệm vụ mẫu tự sinh; bảo toàn dữ liệu thực do người dùng nhập và tệp trong IndexedDB.
- Xóa dữ liệu mẫu khỏi bộ web đóng gói APK/Pages, không tự điền BOQ; chỉ hiển thị KPI khi đã đăng nhập máy chủ.
- Tăng Android versionCode lên 58; không đưa khóa bí mật vào source.

## 2026-11-15 — V5.6–V5.7: Backend đa dự án, RBAC và phê duyệt thật

- Xây dựng backend FastAPI/SQLAlchemy; bảng users, memberships, projects, tasks, approvals, documents, audit, agent configs; SQLite local/PostgreSQL production.
- Kết nối giao diện web và APK qua API, đăng nhập bằng tài khoản và phiên; quản lý danh mục nhiều dự án, hồ sơ/nhiệm vụ độc lập.
- Kiểm tra quyền 403 ở backend, duyệt QA → trưởng bộ môn → PM, chặn người tạo tự duyệt, lịch sử bất biến qua API.
- Bổ sung đủ 16 điểm chọn phòng; thay phối cảnh V5.7, minh họa riêng ba bàn việc chưa có trong ảnh.
- Giữ demo cũ độc lập; chuyển nhiệm vụ cục bộ sang server chỉ khi quản lý xác nhận. Phần AI thực vẫn bị khóa.
- Kiểm thử backend, frontend, kiểm tra source không lộ qua máy chủ.

## 2026-11-15 — V5.4 Danh mục TCVN mở rộng & giao diện song ngữ

- Nghiên cứu `Manhhung114/QLDA_ver612_VPS` theo mã gốc (legal_standards_backfill.py, legal_qlda.py); kế thừa nguyên tắc tra đúng số hiệu và chống bỏ sót, không sao chép dữ liệu chưa kiểm chứng.
- Bổ sung 16 bản ghi VSQI (MEPF/PCCC và Xây dựng), gồm cập nhật 9362:2026 thay 9362:2012; giữ nguồn VSQI, ngày rà soát và cảnh báo hiệu lực.
- Thư viện TCVN có thể cập nhật thủ công từ GitHub hoặc nhập JSON có kiểm tra miền nguồn; mục thủ công chờ xác minh và không ghi đè mục đã đối chiếu.
- Nút Tiếng Việt / English hoạt động trên các trang, form, bộ lọc và danh mục. Không thay đổi dữ liệu người dùng.
- Bảng Excel đa sheet bổ sung nguồn chính thống, bản dịch tiêu đề và hướng dẫn cập nhật. Android build nâng versionCode 54.

# CHANGELOG — Công ty Xây dựng & MEP AI 3D

## 2026-11-15 — V5.7.3: Cục bộ không đăng nhập, có Cài đặt API

- Bỏ mục Tài khoản & quyền trên giao diện; thêm mục Cài đặt. Không yêu cầu server/login cho Dự án, Công việc, Kho tài liệu, Chờ phê duyệt và Nhật ký.
- Quản lý nhiều dự án trên thiết bị, nhiệm vụ và báo cáo theo từng dự án; lưu hồ sơ trong IndexedDB có revision riêng theo dự án.
- Duyệt nội bộ theo tên người kiểm tra, không giả mạo xác thực; giữ thông báo giới hạn phê duyệt.
- Cấu hình OpenAI/Gemini, model theo 18 Agent và phép thử danh sách model. Khóa API không hard-code; hỗ trợ lưu mã hóa bằng passphrase.
- Giữ backend/RBAC để bật lại sau; phiên bản hiện tại chưa đồng bộ server hay chạy AI thực sự.
- VersionCode 60, cùng applicationId và workflow ký phát hành nếu có GitHub Secrets.
- Bảo vệ server static khỏi truy cập trực tiếp thư mục backend và tệp riêng tư.


## 2026-11-15 — V5.5 Approvals / English / Stable Android signing

- Thêm trang duyệt hồ sơ có bằng chứng, báo cáo thực hiện, lịch sử duyệt và trả lại với lý do; không cho duyệt khi thiếu báo cáo/hồ sơ.
- Việt–Anh hai chiều trên các trang và dữ liệu demo, có bản Anh cho mô tả văn bản pháp luật; giữ nguyên mã/tài liệu gốc.
- Android versionCode 55; quy trình ký release bằng bộ GitHub Secrets cố định, khóa phát hành bàn giao riêng tư; debug APK cũ không tự tương thích.
- Thử nghiệm tự động: 34/34 PASS; kiểm tra luồng duyệt và chuyển ngôn ngữ bằng Chromium nội tuyến. Vẫn cần xác minh Android thực tế và chức năng cài đè bản ký.

## 2026-11-15 — V5.3 Tiếng Việt, hiệu chỉnh điểm phòng và pháp lý

- Sửa ghim theo vị trí thực của ảnh, tách phòng chưa có hình minh họa khỏi ghim.
- Việt hóa tên nhân viên AI, nhãn giao diện, tạo trang Pháp luật & tiêu chuẩn riêng.
- Danh mục 29 văn bản từ cổng chính thức, có phân loại lĩnh vực, nguồn, lưu ý hiệu lực và Excel tải về.
- Không xóa dữ liệu demo và lịch sử hồ sơ đã lưu.

## 2026-11-15 — Android V5.2.1 Debug APK

- Thêm dự án Android WebView đóng gói assets V5.2, chọn tệp Android và workflow build APK.
- Chưa ký phát hành, chưa xác minh thiết bị Android thật. Không thay đổi nghiệp vụ và dữ liệu phiên bản cũ.


## 2026-11-15 — V5.2 WebGL ba tầng và điều khiển camera

- Cảnh WebGL 3 tầng (MEP + Xây dựng + điều hành), bàn họp, màn hình, nội thất và nhân vật hoạt động theo trạng thái nhiệm vụ.
- Bộ điều khiển camera, zoom và lựa chọn chất lượng hiển thị. Tối ưu tần suất render trên điện thoại.
- Chuẩn bị workflow xuất bản GitHub Pages; không đồng nghĩa đã online.
- Giữ nguyên quản lý công việc, hồ sơ, BOQ và revision.

## 2026-11-15 — V5.1 Phối cảnh 3D cao cấp

- Bổ sung ảnh isometric 3 tầng có phòng ban MEP và Xây dựng, khu giám đốc, phòng họp và bảng điều hành trung tâm.
- Bổ sung 16 điểm chọn phòng trên phối cảnh; giữ liên kết với inspector và dữ liệu công việc.
- Chế độ “Phối cảnh chi tiết” mặc định; giữ nút “3D tương tác” (WebGL) và chế độ dự phòng SVG.
- Tối ưu vuốt ngang khi xem trên điện thoại; giữ nguyên BOQ, bản vẽ, revision và nhiệm vụ đang lưu.
- Ảnh phối cảnh là hình dựng minh họa, **không phải mô hình WebGL 3D**; AI vẫn là mô phỏng.

## 2026-11-15 — V5.0: Bổ sung nhánh Xây dựng

- Thêm 8 phòng chuyên môn Xây dựng, 8 Agent ảo và 6 nhiệm vụ demo; giữ khối MEP, tổng 16 phòng/18 Agent.
- Mở rộng văn phòng WebGL/SVG thành 2 tầng có chế độ xem toàn công ty / từng khối.
- Phân khối hồ sơ và revision độc lập cho MEP và Xây dựng; thêm 5 mẫu CSV và cây thư mục XD_PROJECT_001.
- Hai bảng BOQ demo riêng. Đã thêm migration localStorage cho nhiệm vụ cũ; không xóa hồ sơ đã lưu.
- AI thực, BIM IFC viewer và tự tính toán vẫn chưa triển khai.


## 2026-11-15 — Initial prototype V1.0–V4.0 foundation

- V1.0: tạo văn phòng WebGL gồm 8 phòng ban/10 avatar, chức năng chọn phòng/nhân viên, camera xoay/zoom, SVG isometric dự phòng.
- V2.0: mô hình các Agent, danh sách nhiệm vụ, Kanban, cập nhật tiến độ và nhật ký; có nút mô phỏng, **không chạy AI thật**.
- V3.0: tài liệu tách category, revision tăng theo mã, tệp gốc trong IndexedDB; BOQ CSV mẫu và tính tổng đơn giản. BIM chưa có viewer.
- V4.0: dashboard số lượng công việc, số file, số Agent, xuất metadata JSON, trang roadmap.
- Tests: 6/6 core PASS. Các chức năng WebGL thực và IndexedDB trên thiết bị chưa nghiệm thu.

## Quy tắc phát hành tương lai

- Đưa code mới vào đúng module `src/core/` hoặc `src/3d/` thay vì sửa tất cả trong một file.
- Bổ sung ghi chú thay đổi trong `versions/V*_*.md` tương ứng và CHANGELOG.md.
- Tạo Git tag mới (ví dụ `v1.1.0`) sau khi test; không sửa tag đã phát hành.
- Hồ sơ khách hàng không commit lên GitHub public.
