# V5.9 + V6.0 — Dữ liệu dự án dùng chung và phê duyệt trên Streamlit

## Tình trạng kiến trúc

Bản chạy trực tiếp từ GitHub trên Streamlit không có một máy chủ FastAPI/PostgreSQL chạy thường trực. V5.9/V6.0 tích hợp trực tiếp vào Streamlit, dùng Google Drive *đã kết nối* để lưu metadata bền vững; không dùng RAM/SQLite tạm của Streamlit Cloud làm cơ sở dữ liệu.

- **Tệp nghiệp vụ gốc**: giữ nguyên thư mục Google Drive từng dự án, bản vẽ, BOQ, BIM và revision R01/R02.
- **Cấp quyền**: đăng nhập Google OIDC, tệp chính sách phân quyền đã ký HMAC ở thư mục gốc Drive; Admin, Cập nhật, Chỉ đọc, phạm vi dự án.
- **Dữ liệu dùng chung**: mỗi giao dịch là một sự kiện JSON được máy chủ ký HMAC-SHA256 và thêm vào thư mục riêng `_XD_MEP_WORKSPACE_EVENTS_V59` trong root Drive.
- **Giao diện**: thay nội dung quản lý Dự án/Công việc/Chờ phê duyệt/Kho tài liệu/Nhật ký hoạt động bằng dữ liệu do máy chủ cấp. Các nút trong sheet mở hộp thoại Streamlit để tạo/sửa, không có trang tải file riêng.
- **Chưa triển khai PostgreSQL**: mã FastAPI hiện có chưa được đưa lên dịch vụ luôn hoạt động, không gọi đây là một hệ thống PostgreSQL production. Để nhiều dự án/người dùng quy mô lớn cần chuyển metadata và audit vào PostgreSQL có transaction, backup định kỳ, read replicas nếu cần.

## V5.9 — Quản lý dự án và công việc tập trung

1. Admin tạo mã/tên dự án; hệ thống tạo cấu trúc thư mục Google Drive theo dự án, không xóa hồ sơ cũ.
2. Admin hoặc người có quyền Cập nhật được giao công việc, gắn bộ môn, người nhận, mã hồ sơ và hạn.
3. Chỉ người có quyền theo dự án mới đọc được dự án hoặc tạo/sửa công việc; người Chỉ đọc không thể ghi dữ liệu máy chủ.
4. Màn hình Dự án, Công việc và dashboard Văn phòng 3D lấy danh sách công việc từ nguồn chung. Có nút **Làm mới dữ liệu** để nhận cập nhật của người khác.
5. Nhật ký lưu actor là email Google đã xác minh và thời điểm UTC tại máy chủ.
6. Nguyên bản localStorage/IndexedDB cũ được giữ trên trình duyệt; app không tự xóa hoặc nhập tự động.

### Chuyển dữ liệu cũ có xác nhận

Admin vào **Quản lý dự án → Sao lưu dữ liệu cũ trên thiết bị** để tải bản sao metadata JSON, tiếp tục **↑ Nhập bản sao dữ liệu cũ** và xác nhận.

- Chỉ nhập metadata dự án/công việc, tối đa 50 dự án, 500 nhiệm vụ và 1 MB JSON.
- Nhập lặp lại không tạo trùng nhiệm vụ; dự án có mã trùng mà tên khác bị từ chối để tránh trộn dữ liệu.
- Trạng thái/báo cáo cũ được lưu ở mục tham khảo `legacy`, trạng thái nhiệm vụ nhập vào bắt đầu từ **Chờ xử lý**. Không giả tạo chữ ký hoặc quyết định phê duyệt cũ.
- **Tệp nhị phân trong IndexedDB không được tự động đưa lên Drive.** Trước khi thay thiết bị, tải riêng tệp gốc và đưa lên qua Kho tài liệu.
- Nếu một đợt nhập lỗi giữa chừng, metadata đã nhập không bị xóa; có thể sửa rồi nhập lại.

## V6.0 — Phê duyệt và quản lý phiên bản

- Người Cập nhật/ Admin có thể **Bắt đầu → Gửi báo cáo**; báo cáo được lưu cùng actor và timestamp.
- Chỉ **Admin** hiện được **Phê duyệt** hoặc **Trả lại**. Trả lại yêu cầu ghi rõ lý do. Đây là quyết định quản lý nội bộ có truy vết, **không thay chữ ký số hoặc phê duyệt pháp lý**.
- Trong từng sheet liên quan, nút Google Drive tải/xem hồ sơ đúng dự án; trên hộp thoại có **Mã hồ sơ V6.0**, mô tả phiên bản và liên kết với công việc.
- Các tệp đã tải trước khi có V6.0 có thể dùng **Ghi hồ sơ hiện có vào sổ V6.0** để cập nhật sổ mà không upload lại.
- Sổ hồ sơ chứa file ID, code, category, revision, người thực hiện, mô tả và task ID; không sửa nội dung tệp gốc.

## Quy tắc an toàn

- Không nhập OAuth Client Secret/refresh token vào giao diện hoặc GitHub; giữ nguyên `[auth]` và `[drive]` trong Streamlit Secrets.
- **Giữ ổn định `[auth].cookie_secret`.** Tệp phân quyền và nhật ký dùng chung được ký bằng khóa này; đổi khóa mà không có quy trình ký lại sẽ chặn đọc dữ liệu cũ.
- Không cho tài khoản Chỉ đọc upload/đăng ký hồ sơ; từ chối tất cả hành động sai dự án ở phía Python.
- Khi không đọc được Drive hoặc xác minh chữ ký nhật ký thất bại, ứng dụng chặn thao tác (fail-closed) thay vì lặng lẽ dùng dữ liệu cục bộ cũ.
- Nhật ký hiện là append-only về logic, không phải WORM hoặc log bất biến trước tài khoản Google Drive có quyền chủ sở hữu; quyền xóa ở Google Drive và bản sao lưu cần bảo vệ ở cấp vận hành.
- Kho sự kiện có ngưỡng bảo vệ 2.500 sự kiện, không tối ưu cho tải đồng thời lớn; cần PostgreSQL cho production scale.
- Nếu nhiều Admin phê duyệt đồng thời, chưa có transaction khóa như cơ sở dữ liệu SQL. Phải kiểm thử và chuyển backend trước khi dùng với các quyết định rủi ro cao.
- Upload 500 MB phụ thuộc bộ nhớ và timeout thực tế của Streamlit. Tải qua nút native giới hạn 40 MB; tệp lớn mở trên Drive với quyền Google phù hợp.

## Checklist nghiệm thu trực tiếp

1. Mở app ở cửa sổ ẩn danh: chưa đăng nhập không hiển thị dữ liệu dự án.
2. Admin thấy Cài đặt và tạo dự án mới. Kiểm tra thư mục mới trên Drive.
3. Tài khoản Cập nhật được gán một dự án thấy đúng dự án đó, tạo công việc và trình báo cáo từ máy B.
4. Admin trên máy A bấm **Làm mới dữ liệu**, thấy báo cáo chờ duyệt, phê duyệt hoặc trả lại kèm lý do.
5. Máy B làm mới, thấy trạng thái và người duyệt; đăng xuất/đăng nhập vẫn giữ dữ liệu.
6. Tài khoản Chỉ đọc không có nút cập nhật, và lệnh gửi giả cũng bị máy chủ từ chối.
7. Upload BOQ_R01, R02, gắn mã BOQ và công việc; xem sổ hồ sơ từ máy khác.
8. Thử sao lưu và nhập metadata cũ; đối chiếu số dự án/nhiệm vụ, bảo đảm file IndexedDB chưa bị xóa.
9. Thử file 25/100/250/500 MB trên Streamlit thực, đo RAM và thời gian.
10. Thử nhiều người cùng thao tác; kiểm tra audit và quota Drive trước khi chấp nhận production.

## Chưa thuộc phạm vi V5.9/V6.0

Chưa có LLM Agent thực thi kỹ thuật, tự bóc tách DWG/RVT, IFC viewer thật, PostgreSQL triển khai, tự nhập file binary cũ, chữ ký số pháp lý hay kiểm thử tải nhiều người dùng quy mô lớn.
