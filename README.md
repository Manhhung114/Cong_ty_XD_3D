# CÔNG TY XÂY DỰNG & MEP AI 3D — Prototype V1.0–V5.0

**Bản bàn giao:** 2026-11-15  
**Loại:** Ứng dụng web 3D chạy cục bộ, không cần Node package, npm hoặc API key.  
**Trạng thái:** Demo chức năng. **Chưa** kết nối AI Agent thực sự, Google Drive, BIM engine hoặc cơ sở dữ liệu máy chủ.

## Chạy phần mềm

### Windows

1. Giải nén ZIP vào một thư mục **không** chứa mã nguồn sản xuất cũ.
2. Nhấp đúp `RUN_WEB_3D.bat` (máy cần có Node.js hoặc Python 3).
3. Trình duyệt mở `http://localhost:8766`. Nếu không tự mở, nhập địa chỉ đó.
4. Giữ cửa sổ dòng lệnh đang chạy khi sử dụng ứng dụng. Muốn dừng, nhấn `Ctrl+C`.

### macOS / Linux

Mở Terminal trong thư mục dự án, chạy:

```bash
sh RUN_WEB_3D.sh
```

Mở `http://localhost:8766`.

### Nếu máy chỉ có Python

```bash
python -m http.server 8766
```

**Không mở trực tiếp bằng cách nhấp đôi `index.html`**. Trình duyệt có thể chặn ES modules và `fetch` khi chạy dạng `file://`.

## Chức năng sẵn có

| Mốc | Tính năng hiện có | Chưa có |
|---|---|---|
| V1.0 | WebGL 3D, 16 phòng trên 2 tầng và 18 nhân viên avatar; click phòng/Agent, xoay, zoom; SVG isometric dự phòng | Mô hình nội thất 3D chất lượng thương mại, hoạt cảnh thực tế cao |
| V2.0 | Tạo nhiệm vụ, giao Agent theo phòng ban, chuyển trạng thái, mô phỏng luồng và nhật ký | LLM API, thuật toán kỹ thuật, quy trình agent tự thực thi |
| V3.0 | Nhóm hồ sơ, tải tệp và giữ revision bằng IndexedDB, mẫu bản vẽ/BOQ/BIM/PCCC; CSV BOQ có tính tổng | Đọc DWG/RVT/IFC, Excel XLSX trực tiếp, tách khối lượng từ mô hình |
| V4.0 | KPI, màn hình tiến độ, sự kiện và xuất JSON metadata | CSDL đa người dùng, SSO, quyền duyệt, sao lưu máy chủ, dashboard số liệu thực |
| V5.0 | Nhánh Xây dựng có 8 phòng/8 Agent, phân loại MEP–XD, BOQ/khối, revision hồ sơ riêng và văn phòng 3D hai tầng | AI kỹ thuật thực và mô hình 3D chi tiết như ảnh thiết kế |

## Cấu trúc thư mục tách biệt

```text
mep_ai_company_3d/
├── index.html                          # Điểm khởi chạy web
├── server.mjs                          # Web server Node.js thuần
├── RUN_WEB_3D.bat/.sh                  # Mở ứng dụng
├── src/
│   ├── app.js                          # Điều hướng, giao diện, form, sự kiện
│   ├── styles.css                      # Theme và responsive
│   ├── 3d/scene.js                     # WebGL & fallback isometric
│   └── core/
│       ├── config.js                   # Phòng ban, Agent, danh mục, roadmap
│       ├── storage.js                  # Nhiệm vụ + nhật ký, localStorage
│       ├── documents.js                # Upload, download, revision, IndexedDB
│       ├── boq.js                      # Phân tích BOQ CSV, tổng giá
│       ├── bim.js                      # Khai báo khả năng BIM (chưa tích hợp)
│       └── export.js                   # Xuất metadata JSON
├── data/
│   ├── samples/                        # Dữ liệu DEMO, có thể xóa khi đưa vào sản xuất
│   └── templates/                      # Từng mẫu nghiệp vụ độc lập
├── project_templates/MEP_PROJECT_001/  # 6 thư mục hồ sơ MEP
├── project_templates/XD_PROJECT_001/   # 8 thư mục hồ sơ Xây dựng
├── versions/                           # Ghi chú V1.0–V5.0 riêng
├── docs/                               # Hướng dẫn, kiểm thử và quy ước cập nhật
└── tests/                              # Bộ kiểm thử core bằng Node built-in
```

## Quy tắc cập nhật hồ sơ

1. Chọn khối **MEP** hoặc **Xây dựng**. Mỗi tài liệu có **mã cố định** như `DRW-E-001`, `BOQ-MEP-001`, `BIM-MEP-001`.
2. Mỗi cặp `(khối, mã hồ sơ)` có chuỗi revision độc lập. Tải tệp lần đầu tạo `R01`. Khi thay đổi, tải tệp mới **cùng mã**, hệ thống tạo `R02`, `R03`… (không ghi đè tệp cũ).
3. Ghi mô tả thay đổi; ở màn hình hồ sơ, bấm **Lịch sử** để xem revision và tải từng tệp gốc.
4. Các loại hồ sơ khác nhau có thể có cùng phiên bản R01 nhưng mã hồ sơ khác nhau. **Hệ thống không tự so sánh nội dung DWG/PDF/XLSX.**
5. Tệp upload hiện lưu trong **IndexedDB của trình duyệt hiện tại**, không tự đi vào `data/` hoặc `project_templates/`, cũng không tự đồng bộ lên Google Drive. Xóa dữ liệu trang web có thể làm mất file đã upload. Cần giữ file gốc bên ngoài ứng dụng.

## BOQ CSV

Tệp ví dụ: `data/samples/BOQ_DEMO.csv`.

5 cột bắt buộc/khuyến nghị: `code,description,unit,quantity,unitPrice`. Cần `quantity` và `unitPrice` để tính. Ứng dụng hỗ trợ phân cách dấu phẩy hoặc chấm phẩy, số thập phân kiểu Việt Nam. Thành tiền = khối lượng × đơn giá; **chưa** tính VAT, chiết khấu hay kiểm tra đơn giá thực tế.

Chọn **BOQ MEP** hoặc **BOQ Xây dựng**, sau đó nhập CSV qua **BOQ / Dự toán → Đọc CSV**. Nếu muốn lưu nguyên tệp dưới dạng hồ sơ có revision, tiếp tục dùng **Kho tài liệu → BOQ / Dự toán**.

## Kiểm thử đã thực hiện

- Lệnh `npm test` (không cần cài gói): kiểm thử logic V5.
- Kiểm tra cú pháp JS bằng `node --check`: PASS.
- Kiểm tra giao diện mô phỏng bằng trình duyệt giới hạn: phần UI, điều hướng, tạo nhiệm vụ, chọn phòng, mở form upload, BOQ mẫu và SVG isometric dự phòng có thể hiển thị; không phát hiện lỗi JS trong lần thử đó.
- **Chưa xác minh** khởi tạo WebGL trên thiết bị thực, tải IndexedDB trên trình duyệt có origin thông thường, và độ ổn định khi nhiều file lớn. Các chức năng này cần kiểm thử trên thiết bị đích trước nghiệm thu.

## Điều kiện để chuyển thành công ty MEP AI thật

Cần bổ sung backend, khóa API lưu phía server, điều phối Agent, công cụ tính toán kỹ thuật đã kiểm định, kho tệp phía server, phân quyền theo dự án, phê duyệt bởi kỹ sư, nhật ký bất biến và kết nối BIM. Xem `docs/AI_BACKEND_CONTRACT.md`.

**Bảo mật:** Mã nguồn demo chạy hoàn toàn trên trình duyệt và không gửi tệp lên server. Không lưu hồ sơ dự án bảo mật hoặc thông tin cá nhân trong demo. Mọi dữ liệu trong `data/samples` đều là minh họa, không dùng cho thiết kế hoặc nghiệm thu.

## V5.0 – Cách sử dụng nhánh Xây dựng

1. Truy cập **Khối Xây dựng** ở sidebar để quan sát 8 phòng trên tầng trên của văn phòng.
2. Trong **Nhân viên AI** và **Công việc**, chọn Toàn công ty / MEP / Xây dựng để xem đúng khối.
3. Trong **Kho tài liệu**, chọn khối rồi tải bản vẽ, kết cấu, BOQ, kế hoạch, vật tư hoặc checklist; mã giống ở hai khối được quản lý độc lập.
4. Trong **BOQ / Dự toán**, dùng nút BOQ MEP / BOQ Xây dựng và tệp CSV mẫu riêng.
5. Các bản demo đều không thay thế kết quả tính toán hay phê duyệt của kỹ sư có chuyên môn.


## V5.1 — Phối cảnh văn phòng chi tiết (15/11/2026)

Mặc định hiển thị hình dựng isometric ba tầng, gần phong cách ảnh mẫu: ban điều hành, MEP, Xây dựng, phòng họp và màn hình điều hành trung tâm. Bấm vào **điểm tròn** trên mỗi khu vực để xem nhân sự, nhiệm vụ và giao việc.

Nút **3D tương tác** chuyển lại WebGL gốc để xoay/zoom. Nút **Phối cảnh chi tiết** trở lại ảnh chất lượng cao có điểm chọn phòng. Trên điện thoại vuốt ngang để xem toàn bộ tòa nhà.

**Phân biệt rõ:** Phối cảnh chi tiết là ảnh 3D-rendered dạng tĩnh có hotspot; chế độ 3D tương tác mới là WebGL. Không tuyên bố đồ họa 3D ảnh tĩnh có thể xoay mọi góc. Không ảnh hưởng tệp hồ sơ, revision, BOQ hoặc dữ liệu cũ trong IndexedDB/localStorage.


## V5.2 — Bản WebGL để thử trên máy và web

Vào **Văn phòng 3D → 3D tương tác** để xem văn phòng ba tầng. Sử dụng **Phối cảnh, Mặt trước, Từ trên, Tầng MEP, Tầng XD**, nút zoom hoặc kéo chuột/ngón tay để xoay; có thể chọn **Tiết kiệm pin** trên điện thoại. **Phối cảnh chi tiết** vẫn là ảnh isometric 2D tương tác điểm bấm, không thể xoay camera.

Để triển khai GitHub Pages: mở Settings → Pages → Source: GitHub Actions; theo dõi workflow **Publish Web 3D (Pages)** và chỉ dùng link sau khi workflow thành công. Repository này không chứa hồ sơ khách hàng.

Đây vẫn là prototype chạy front-end, 18 Agent chưa gọi API AI thật và hồ sơ chưa đồng bộ cloud.


## Android APK V5.2.1 (bản thử)

Thư mục `android/` chứa wrapper WebView Android cho V5.2, đóng gói asset tĩnh offline qua HTTPS nội bộ. Vào GitHub Actions `Build Android APK - XD MEP AI 3D` để tải `app-debug.apk` khi build PASS. Xem `android/README_ANDROID.md` và `versions/V5_2_1_ANDROID_APK.md` về cách cài đặt, dữ liệu và giới hạn. **Chưa có signing key cố định và chưa đủ điều kiện phát hành Play Store.**


## V5.3 – Thư viện văn bản pháp luật và tiếng Việt

- Mục **Pháp luật & tiêu chuẩn** trên menu có bộ lọc hai lĩnh vực, tìm theo số hiệu, nguồn và liên kết văn bản chính thống.
- Sheet Excel: `data/legal/Thu_vien_phap_luat_MEPF_PCCC_Xay_dung_QLDA_2026.xlsx`, dữ liệu JSON/CSV cùng thư mục để cập nhật độc lập.
- Không lưu toàn văn TCVN bản quyền; chỉ trỏ nguồn VSQI, Bộ Xây dựng và Cổng văn bản Chính phủ.
- Sửa vị trí các ghim tại bàn làm việc thật; QA/QC MEP và Quản lý hiện trường XD hiện chưa có vùng riêng trên ảnh nên cung cấp nút chọn bổ sung.
- Những kết luận pháp lý vẫn cần kiểm tra theo thời điểm áp dụng và điều khoản chuyển tiếp.


## V5.4 — Thư viện TCVN theo QLDA_ver612_VPS và Tiếng Việt / English (15/11/2026)

- Nút chọn `Tiếng Việt / English` trên thanh công cụ đổi nhãn giao diện mà không thay đổi nhiệm vụ, hồ sơ hay dữ liệu gốc. Ngôn ngữ được nhớ trong `localStorage` riêng. **Tên nguyên bản tiếng Việt của văn bản pháp lý luôn được giữ trong dữ liệu**; những tiêu chuẩn đã có bản dịch tên sẽ hiển thị tên tiếng Anh khi chọn English.
- Nguồn nghiên cứu **phương pháp**: [`Manhhung114/QLDA_ver612_VPS`](https://github.com/Manhhung114/QLDA_ver612_VPS), tệp `src/qlda/runtime_core/legal_standards_backfill.py`: truy vấn nhóm, tra đúng số hiệu ưu tiên, loại dự thảo, loại trùng. Không dùng GitHub như một nguồn ban hành pháp luật hay tiêu chuẩn.
- Danh mục bổ sung gồm **16 bản ghi TCVN** tại `data/legal/TCVN_QLDA_VPS_verified.json`; tất cả đều dẫn đến [VSQI](https://tieuchuan.vsqi.gov.vn/) với thời điểm đối chiếu 15/11/2026. Bao gồm bản lịch sử TCVN 9362:2012 (đã bị thay thế bởi TCVN 9362:2026). TCVN 5738:2021 đã được đánh dấu trong danh mục V5.3 là hết hiệu lực.
- Tại **Pháp luật & tiêu chuẩn**: `Cập nhật từ GitHub` tải phiên bản JSON mới qua mạng; `Nhập JSON` nạp các mục từ tập tin theo `data/legal/TCVN_UPDATE_TEMPLATE.json`; `Đặt lại danh mục` xóa bộ nhớ cập nhật riêng, khôi phục danh mục đóng gói. Tệp thủ công được đánh dấu **Chờ đối chiếu nguồn**; ứng dụng từ chối đường dẫn không phải cổng chính thống hoặc mục dự thảo. Cập nhật mạng không chạy trong nền, không ảnh hưởng dữ liệu cũ.
- Xuất bản Excel `data/legal/Thu_vien_phap_luat_V5_4_TCVN_QLDA_VPS.xlsx`: sheet danh mục cũ, sheet TCVN bổ sung và sheet hướng dẫn cập nhật.
- **Giới hạn:** Giao diện hai ngôn ngữ là bản thử nghiệm; các thuật ngữ kỹ thuật, mô tả mẫu, hồ sơ và tiêu đề nguồn pháp lý vẫn có thể được giữ bằng tiếng Việt để bảo toàn căn cứ gốc. Không tự tải nội dung thương mại của TCVN hoặc tự kết luận tính bắt buộc của tiêu chuẩn.
- **Ứng dụng Android:** APK được đóng gói lại bằng workflow GitHub sau khi push; `versionCode=54`, `versionName=5.4.0-demo`. Nếu bản debug khác chữ ký thì không thể cài đè; sao lưu trước, không gỡ khi chưa bảo toàn hồ sơ.
