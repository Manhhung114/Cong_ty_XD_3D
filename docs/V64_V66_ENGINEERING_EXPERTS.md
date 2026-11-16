# V6.4–V6.6: Chuyên gia lĩnh vực có bằng chứng kỹ thuật

## Kiến trúc hiện triển khai

Đăng nhập Google OIDC → quyền dự án → task của bộ môn → tệp **đã ghi sổ** trong chính dự án → so khớp thư mục/MD5/dung lượng → tải tối đa 8 MiB trong Streamlit → bộ đọc định dạng → bộ kiểm tra có công thức và nguồn → chuỗi chuyên gia/DOC/QAC/PM → một sự kiện `agent.completed` ký HMAC.

- **Không tải tệp Drive bất kỳ theo ID tùy ý.** Tệp bắt buộc phải thuộc dự án và nhóm hồ sơ đã cấp quyền, có trong sổ ký xác thực. Khi checksum hoặc kích thước khác, từ chối.
- File gốc không bị ghi đè, sửa hoặc gửi qua AI. Trích xuất chỉ dùng ở bộ nhớ máy chủ và không được đưa toàn bộ vào nhật ký.
- Mọi lần phân tích có `file_id`, revision, MD5, SHA-256 tính trên byte tải thật; kết quả nháp ghi email người chạy và bốn bước kiểm tra.
- Người dùng có thể chạy chuyên gia **không cần API** bằng bộ kiểm tra mã Python, hoặc chọn **AI + trích xuất file** sau khi xác nhận gửi mẫu trích xuất và cấu hình `[ai]` trong Streamlit Secrets.
- Hành vi chưa hỗ trợ phải báo lỗi và giữ nguyên Drive, không tạo kết quả giả.

## V6.4 — Đọc file thật

| Định dạng | Thực hiện | Giới hạn / nguồn đối chiếu |
|---|---|---|
| PDF văn bản | pypdf: tối đa 12 trang đầu, 300 dòng trích xuất; nguồn trang/dòng | PDF scan báo cần OCR, không tự suy diễn hình ảnh |
| XLSX | openpyxl: ô, sheet, dòng bảng và số; tối đa 5 sheet, 350 dòng/sheet, 300 ô ghi mẫu | `data_only`: công thức không có cache có thể trả rỗng; không chạy macro hay link |
| CSV | csv: bảng, ô và dòng, nguồn `CSV:row:col` | tối đa 350 dòng và 300 ô mẫu |
| DXF | ezdxf: layer, TEXT, INSERT, entity handle và thống kê loại đối tượng | Không xác nhận va chạm hình học, clearance, kích thước và đơn vị khi chưa có mô hình chuyên biệt |
| IFC | IfcOpenShell: phần tử IfcProduct, GlobalId, Name, loại và kiểm tra ID trùng | Chỉ kiểm kê tối đa 1500 phần tử; **chưa** chạy clash geometry |
| DWG, RVT, NWD, XLS | Từ chối phân tích trực tiếp và gợi ý chuyển DXF/IFC/XLSX bởi công cụ được phép | Chưa có bộ chuyển đổi trên Streamlit; không đổi tên đuôi để giả mạo |

**Giới hạn file 8 MB** áp dụng riêng cho bộ phân tích trên Streamlit, **không làm thay đổi giới hạn upload kho Drive 500 MB** (vẫn cần nghiệm thu thực tế). Với tài liệu lớn, phải triển khai worker/container tách biệt có giới hạn CPU/RAM, sandbox và hàng đợi công việc. Không chạy geometry hay bộ chuyển DWG trong Streamlit.

## V6.5 — Chuyên môn và phép tính có nguồn

Danh mục 18 chuyên gia không còn chỉ là vai trò chat; mỗi chuyên gia có yêu cầu chứng cứ, kiểm tra dữ liệu vào và công cụ xác định trong `drive_storage/expert_rules.py`.

**Các công cụ định lượng được triển khai và kiểm chứng độc lập:**

- QS MEP/XD/Vật tư: nếu bảng có chính xác các cột số lượng, đơn giá, thành tiền → so sánh `quantity × unit_price` với `amount`, báo dòng lệch, tổng mẫu và vị trí ô/dòng.
- Điện 3 pha: với các trường đầu vào tường minh `p_kw`, `v_ll_v`, `pf` và tùy chọn `efficiency` → `I=P×1000/(√3×V_LL×PF×η)`. Đây là dòng ước tính và không chứng minh chọn cáp/bảo vệ.
- HVAC: với `flow_m3h`, `room_volume_m3` → `ACH=Q/V`, không tự khẳng định đủ thông gió theo QCVN/TCVN.
- Cấp thoát nước/PCCC: `flow_m3h`, `pipe_diameter_mm` → `v=(Q/3600)/(π(D/1000)²/4)`. Chưa tính ma sát, áp lực, thiết kế chữa cháy.
- Kết cấu: nếu có `mass_kg` → `F=m×9.80665` minh họa lực trọng trường, **không** là mô hình kết cấu.
- BIM/kiến trúc/kết cấu: kiểm kê kiểu phần tử IFC, trùng GlobalId, layer/đối tượng DXF có handle; hình học 3D và clash chính xác chưa triển khai.
- PM/CEO/QAC/DOC/PLN/SIT/HSE/MAT: kiểm tra tồn đọng, nguồn/chứng cứ, revision và hồ sơ phối hợp, không thay nhận định chuyên môn hoặc phê duyệt.

**Quy tắc an toàn:** Không kết luận tuân thủ TCVN/QCVN khi chưa có điều khoản hiệu lực được chuyên gia xác minh, được số hóa theo rule ID, đơn vị, điều kiện áp dụng và test chuẩn. Trạng thái chuẩn luôn là `not_assessed`. Các phép tính ở trên chỉ là kiểm tra công thức trên dữ liệu có nhãn, không phải phương pháp thiết kế hoàn chỉnh.

## V6.6 — Hàng kiểm soát Agent

Một lượt xử lý có bốn giai đoạn:

1. **Agent chuyên ngành**: chọn nguồn đúng bộ môn và trích xuất thông số/bảng/đối tượng thật; ghi phát hiện và nguồn.
2. **DOC**: xác định mã tài liệu, file ID, revision, trạng thái đã ghi sổ và checksum, yêu cầu đối chiếu phiên bản.
3. **QAC**: đánh dấu các phép tính hợp lệ/sai khác, nguồn thiếu, và trạng thái chưa xác nhận tiêu chuẩn.
4. **PM**: xác định kỹ sư phụ trách và điểm cần xử lý, **không tự chuyển nhiệm vụ sang Đã duyệt**.

Chuỗi này là các *cổng kiểm soát tự động bằng quy tắc*, chưa phải bốn LLM độc lập chạy nền. Tất cả kết quả lưu trong **một** sự kiện ký HMAC để có thể truy vết, xem từ màn hình Nhân viên AI/Công việc/Chờ phê duyệt. Nếu gọi LLM thì chỉ một lần có sự đồng ý của người dùng; lệnh lặp kiểm tra ID trước khi phát sinh phí.

Không áp dụng tự ký, tự phê duyệt, tự kết luận an toàn PCCC hoặc pháp lý. Các phát hiện có thể được kỹ sư kiểm tra rồi lập báo cáo và trình duyệt bằng luồng đã có.

## Cách sử dụng

1. Admin/nhân viên Cập nhật vào Kho tài liệu, tải lên PDF/XLSX/CSV/DXF/IFC hợp lệ, **ghi vào sổ**, chọn đúng bộ môn và gắn công việc (hoặc xác định dự án).
2. Vào **Công việc**, tạo nhiệm vụ theo đúng bộ môn (ví dụ QS MEP, Điện), người phụ trách và mã hồ sơ.
3. Vào **Nhân viên AI**, chọn Agent đúng chuyên môn và nhiệm vụ → **Chạy Agent**.
4. Chọn **Chuyên gia phân tích file thật**, chọn file có trong sổ, bấm Chạy. Nếu có cấu hình AI, chọn **AI + trích xuất file** và xác nhận đồng ý truyền mẫu nội dung cho nhà cung cấp.
5. Xem phát hiện có nguồn, các bước DOC/QAC/PM và SHA-256 ở Nhật ký Agent hoặc ngay trong Công việc.
6. Kỹ sư kiểm tra bản gốc và lập báo cáo hoàn chỉnh; Admin kiểm tra và quyết định bằng chức năng phê duyệt nội bộ hiện có.

## Hướng dẫn nhập mẫu tính thử (Excel/CSV)

Lập bảng **hai cột** với tiêu đề bất kỳ; mỗi dòng là khóa và số:

```csv
key,value
p_kw,15
v_ll_v,400
pf,0.9
efficiency,0.95
flow_m3h,360
room_volume_m3,120
pipe_diameter_mm,50
mass_kg,10
```

Chọn Agent đúng chuyên môn để xem phép tính tương ứng; thiếu khóa thì không tự điền. Không dùng phép tính mẫu như giá trị bắt buộc theo tiêu chuẩn.

Với BOQ, dùng các cột `Quantity` / `Unit Price` / `Amount` hoặc `Khối lượng` / `Đơn giá` / `Thành tiền`, rồi chạy QSU hoặc XQS. Tệp trên 8 MB phải giảm kích thước hoặc đưa qua worker chuyên biệt sau này.

## Hạ tầng và kiểm thử

- Production đang sử dụng Streamlit + Google Drive signed event ledger, không có PostgreSQL deployed, không có worker chạy nền.
- Pip dependencies: `pypdf`, `openpyxl`, `ezdxf`, `ifcopenshell`. Máy chủ cần đủ bộ nhớ/cấu trúc wheel; CI cài đúng `requirements.txt`.
- Mọi quyền dự án và HMAC giữ nguyên; không đổi `[auth].cookie_secret` hoặc OAuth Secrets.
- Test tự động: CSV/XLSX/PDF/DXF/IFC file thật, công thức, mismatch, chứng cứ thiếu, phân quyền sai dự án, checksum thay đổi, idempotency và chuỗi 4 cổng.
- **Cần nghiệm thu trình duyệt thật** trên hai tài khoản, PDF/Excel/IFC dự án và giới hạn 8MB trước khi dùng nghiệp vụ. BIM clash, Revit RVT, DWG binary và phân tích hồ sơ pháp lý phải thêm worker chuyên ngành.

## Hướng mở rộng V6.7

Worker có giới hạn chạy trên VPS để xử lý DWG chuyển DXF, IFC geometry iterator/BRep clash có dung sai, full Excel/BOQ, OCR có kiểm soát, quy tắc TCVN/QCVN theo phiên bản đã phê duyệt, hàng đợi có transaction PostgreSQL và cơ chế báo cáo kiểm định độc lập. Không thể tuyên bố các chức năng này đã hoàn tất trong V6.6.
