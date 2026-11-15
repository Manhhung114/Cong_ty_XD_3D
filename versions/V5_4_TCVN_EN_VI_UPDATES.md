# V5.4 — Tiếng Việt / English, TCVN bổ sung từ tra cứu QLDA

- **Phạm vi**: Hai lĩnh vực MEPF–PCCC / Xây dựng–QLDA, tách nhóm điện/HVAC/nước/PCCC và kết cấu/móng.
- **Nguồn nghiên cứu**: [`QLDA_ver612_VPS`](https://github.com/Manhhung114/QLDA_ver612_VPS/blob/main/src/qlda/runtime_core/legal_standards_backfill.py) (cơ chế tìm theo họ + exact-number backfill); **nguồn tiêu chuẩn**: VSQI theo URL chi tiết trong từng bản ghi.
- **Danh mục chính**: `data/legal/danh_muc_van_ban_chinh_thong.json` 29 mục giữ nguyên. **Danh mục mở rộng**: `data/legal/TCVN_QLDA_VPS_verified.json` 16 mục; 1 mục là TCVN 9362:2012 đã thay thế.
- **Tính năng cập nhật**: Nút GitHub đọc tệp JSON tại repo `Cong_ty_XD_3D`, nhập JSON cho nội dung được phê duyệt về sau; mọi mục nhập thủ công chờ kiểm tra nguồn. Không có crawler tự chạy trên thiết bị.
- **Ngôn ngữ**: đổi Tiếng Việt / English trong thanh công cụ, lưu tùy chọn riêng theo thiết bị; giữ mã/số hiệu/tệp gốc.
- **Bảo mật**: chỉ chấp nhận địa chỉ HTTPS của cổng cơ quan chính thống; không đưa file khách hàng lên GitHub.
- **Nghiệm thu**: chạy Node test, kiểm tra lọc theo ngành/tình trạng, HTML Android/PC, build APK và kiểm tra trên điện thoại thật.
