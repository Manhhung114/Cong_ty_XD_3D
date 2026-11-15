# Chữ ký Android cố định (V5.5+)

- Package ID: `vn.congtyxd3d.app` (không đổi).
- `versionCode` phải tăng ở mỗi lần phát hành và giữ cùng keystore.
- Khóa và mật khẩu phát hành nằm trong gói **riêng tư** giao chủ dự án, tuyệt đối không commit GitHub công khai.
- Vào GitHub `Settings → Secrets and variables → Actions`, tạo: `XD_MEP_KEYSTORE_BASE64`, `XD_MEP_STORE_PASSWORD`, `XD_MEP_KEY_ALIAS`, `XD_MEP_KEY_PASSWORD`.
- Khi đủ bí mật, workflow `Build Android APK` sẽ biên dịch bản `assembleRelease` được ký bằng khóa cố định và xuất artifact `..._Signed_Release_APK`.
- Bản debug vẫn được xuất cho thử nghiệm nhưng **KHÔNG** bảo đảm nâng cấp giữ dữ liệu và không thay cho bản release.
- APK debug V5.4 cũ có khả năng khác chứng chỉ. Không thể cài đè bằng bản release mới nếu không cùng chữ ký; trước khi chuyển khóa cần sao lưu dữ liệu.
- Giữ bản sao `.p12` an toàn ngoài GitHub. Mất khóa không thể tiếp tục cập nhật APK đã ký với khóa này.
- Sau khi nhận bản release đã ký, xác minh fingerprint trong `CERTIFICATE_SHA256.txt` của gói riêng.
- Đây là chữ ký APK để cập nhật, **không** phải chữ ký số hồ sơ pháp lý, cũng không chứng minh phê duyệt kỹ thuật.
