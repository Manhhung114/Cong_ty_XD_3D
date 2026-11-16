# V6.0.1 — Kho tài liệu có kiểm kê và kiểm soát toàn bộ file Google Drive

## Lý do nâng cấp

V6.0 hiển thị hồ sơ đã **ghi vào sổ** nhưng chưa kiểm kê tất cả file gốc đã upload vào Google Drive; người sử dụng không biết file nào chưa đăng ký, đã tạo lúc nào, đã trình duyệt hay được trả lại, bản R01/R02 nào còn trên Drive. V6.0.1 bổ sung ngay trong sheet **Kho tài liệu** (không thêm trang upload độc lập).

## Giao diện

- Khi mở Kho tài liệu, ứng dụng yêu cầu máy chủ kiểm kê toàn bộ 18 nhóm thư mục thuộc **dự án đã chọn**. Có thể bấm **↻ Kiểm kê toàn bộ file Drive** để cập nhật thủ công.
- Bảng **Mã hồ sơ/Tên file – Nhóm – Revision – Trạng thái – Ngày tải – Người ghi sổ – Dung lượng – Thao tác**. Có tìm kiếm, lọc nhóm, lọc trạng thái, lọc revision gần nhất, sắp xếp và xuất CSV.
- Thống kê **Tổng tệp, Đã ghi sổ, Chưa ghi sổ, Chờ duyệt, Đã duyệt, Mất liên kết, File đã thay đổi**.
- Bấm **Chi tiết** hoặc **Quản lý hồ sơ / duyệt / tải bản gốc** để mở hộp thoại trong ứng dụng; có nút tải file gốc, liên kết Drive, lịch sử phiên bản, lịch sử người thao tác, chỉnh metadata và trình/duyệt/đưa vào lưu trữ.
- Với dự án nhiều tệp, bảng được giới hạn 500 tệp đầu tiên để không làm quá tải trang iframe. Hộp thoại quản lý trên máy chủ vẫn quét toàn bộ tệp (tối đa ngưỡng vận hành 3.000 tệp) và **Xuất báo cáo kiểm kê CSV đầy đủ**.

## Quy trình dùng

1. Admin đăng nhập Google, chọn dự án S234 (hoặc dự án được cấp quyền), mở **Kho tài liệu**.
2. Bấm kiểm kê: file từ trước có thể hiện **Chưa lập sổ**, còn tệp đã ghi từ V6.0 hiện **Mới lập sổ**.
3. Nhấn **Chi tiết** → **Lập sổ hồ sơ** nếu chưa đăng ký, điền mã tài liệu ổn định, mô tả và công việc liên quan.
4. Nhân viên quyền **Cập nhật** mở tệp đã lập sổ, gửi **Trình phê duyệt**, có thể ghi lưu ý.
5. Admin kiểm tra tệp và quyết định **Phê duyệt** hoặc **Trả lại**; trả lại phải nêu lý do. Lịch sử lưu email Google và thời điểm.
6. Nếu hồ sơ đã duyệt cần sửa nội dung, **không ghi đè** file đó: tải bản mới lên cùng bộ môn → phiên bản R02/R03..., ghi sổ với cùng mã hồ sơ.
7. Admin có thể **Lưu trữ** hồ sơ cũ với lý do mà không xóa dữ liệu trên Drive.
8. Bấm **Xuất danh mục CSV** để báo cáo hồ sơ, trạng thái, revision, người ghi sổ, dấu hiệu mất file.

## Các trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| Chưa lập sổ | File tồn tại trên Drive nhưng chưa có metadata ký trên hệ thống |
| Mới lập sổ | Đã đăng ký vào sổ, chờ kỹ sư hoàn thiện và gửi duyệt |
| Chờ duyệt | Đã trình bằng tài khoản Google, Admin cần kiểm tra |
| Đã duyệt | Admin duyệt nội bộ, lưu lịch sử actor/time |
| Yêu cầu sửa | Admin trả hồ sơ kèm lý do; nhân viên sửa metadata hoặc tải revision mới |
| Lưu trữ | Admin lưu trữ hồ sơ, **không xóa file gốc** |
| Không tìm thấy trên Drive | Sổ còn bản ghi nhưng file bị xóa/chuyển đi hoặc không nằm đúng thư mục dự án |

## Phân quyền thực tế

| Hành động | Chỉ đọc | Cập nhật | Admin |
|---|:---:|:---:|:---:|
| Kiểm kê/tìm kiếm/xuất CSV/tải file được cấp | Có | Có | Có |
| Ghi sổ/chỉnh metadata khi chưa duyệt | Không | Có | Có |
| Trình hồ sơ | Không | Có | Có |
| Phê duyệt/trả lại/lưu trữ | Không | Không | Có |
| Xóa file gốc trên Drive từ ứng dụng | Không | Không | **Không có chức năng này** |

Mọi thao tác ghi đều được kiểm tra lại phía Python, yêu cầu email OIDC đã xác minh và quyền với đúng project/folder. Không mở quyền Drive công khai và không truyền refresh token vào iframe.

**Người ghi sổ khác người upload lên Drive**: những tệp được tải lên trước khi chức năng audit hoạt động không thể truy ra email người thao tác qua OAuth dùng chung. Cột hiển thị **Chưa xác định** thay vì suy đoán từ Drive owner (đó thường là chủ tài khoản OAuth của ứng dụng).

## Kiểm soát phiên bản và tính toàn vẹn

- Tên file _R01 / _R02 / _R03 được nhóm theo mã hồ sơ và loại thư mục. File R01 vẫn giữ nguyên, không bị upload R02 ghi đè.
- Khi file được ghi sổ, hệ thống lưu kích thước và mã MD5 do Drive cung cấp (nếu có). Khi kiểm kê/duyệt, khác biệt checksum/kích thước sẽ được cảnh báo và **chặn thao tác ghi/trình duyệt ở máy chủ**. Đây là cơ chế phát hiện thay đổi, không phải kiểm định nội dung kỹ thuật.
- Các sự kiện metadata/status được ký HMAC-SHA256 bằng `[auth].cookie_secret` đã có, giữ lại trên Google Drive event ledger. Không thay cookie_secret nếu chưa có kế hoạch ký lại sự kiện.
- File được di chuyển/xóa khỏi thư mục nguồn sẽ hiện **Không tìm thấy trên Drive**; ứng dụng không tự xóa bản ghi trong sổ. Muốn khôi phục cần kiểm tra Google Drive (Trash/đường dẫn/quyền).
- Không cho phép ghi đè metadata của hồ sơ đã duyệt: muốn sửa nội dung phải lập revision mới.

## Giới hạn & nghiệm thu

1. Thử 2 tài khoản Admin / Cập nhật và một tài khoản Chỉ đọc trên hai trình duyệt.
2. Upload một file R01 và R02, kiểm kê: đúng 2 file, đúng một revision gần nhất. Không đánh mất bản cũ.
3. File cũ trên Drive chưa ghi sổ phải hiện **Chưa lập sổ** và có thể đăng ký mà không cần upload lại.
4. Trình duyệt rồi trả lại, ghi chú xuất hiện trong lịch sử. Tài khoản Cập nhật không thể tự duyệt.
5. Di chuyển thử một tệp trong Drive sang thư mục khác: sổ xuất hiện **Không tìm thấy**. Khôi phục thư mục để xác nhận.
6. Thay đổi file Drive đã ghi sổ: hệ thống nhận diện sai checksum/kích thước nếu Drive hỗ trợ trường MD5.
7. Tải file dưới 40 MB qua Streamlit; file lớn qua đường dẫn Drive đòi quyền tương ứng. **500 MB upload chưa được bảo đảm bằng thử tải thực tế trên Streamlit Cloud**.
8. Dữ liệu IndexedDB, file Drive và các revision cũ không bị reset hoặc xóa.
9. Với hơn 3.000 file / 2.500 sự kiện nghiệp vụ, cần chuyển sang cơ sở dữ liệu PostgreSQL, phân trang theo máy chủ và lịch sử audit có lưu trữ dài hạn.

**Trạng thái phát hành**: kiểm thử tự động cho luồng Drive giả lập và code JavaScript. Kiểm thử trình duyệt Streamlit thật và tải đồng thời vẫn cần hoàn thành trước khi dùng cho hồ sơ pháp lý/nhạy cảm.
