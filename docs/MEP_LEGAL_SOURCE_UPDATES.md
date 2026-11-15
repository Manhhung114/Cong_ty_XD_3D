# Cập nhật pháp luật/TCVN độc lập cho Công ty Xây dựng & MEP AI 3D

Không sửa dữ liệu, mã nguồn hoặc workflow của QLDA_ver612_VPS. Chỉ học phương pháp tra cứu theo số hiệu, nhóm chuyên ngành và nguồn chính thống.

## Đường dẫn tham khảo từ QLDA
| Nguồn | URL |
|---|---|
| VBPL – Bộ Xây dựng | https://vbpl.vn/boxaydung/Pages/Home.aspx |
| Chính phủ – hệ thống văn bản | https://vanban.chinhphu.vn/he-thong-van-ban |
| Công báo Chính phủ | https://congbao.chinhphu.vn/ |
| Bộ Xây dựng | https://www.moc.gov.vn/pl/pages/Vanban.aspx |
| VSQI – TCVN | https://tieuchuan.vsqi.gov.vn/tim-kiem |
| VSQI – Ngành Xây dựng | https://tieuchuanxaydung.vsqi.gov.vn/tim-kiem |

Mã QLDA tham khảo: src/qlda/runtime_core/legal_documents.py, legal_standards_backfill.py và legal_qlda.py. Nhóm ICS trong app: kết cấu 91.080, vật liệu 91.100, kỹ thuật trong nhà 91.140, chiếu sáng 91.160, PCCC 13.220, HVAC 23.120.

## Luồng cập nhật
1. Registry của app: data/legal/MEP_XD_source_registry.json.
2. Chạy tại GitHub Actions của Cong_ty_XD_3D: https://github.com/Manhhung114/Cong_ty_XD_3D/actions/workflows/refresh-mep-legal.yml (Run workflow hoặc lịch tuần).
3. Script chỉ đọc HTML nguồn chính thống, tìm liên kết chi tiết có số hiệu, loại trừ dự thảo, URL ngoài hostname cho phép, bản ghi trùng. Nguồn chặn bot/JavaScript có thể trả rỗng; không được kết luận không có văn bản mới.
4. Workflow chỉ ghi data/legal/MEP_XD_source_candidates.json (chờ đối chiếu), không sửa data/legal/MEP_XD_official_catalog.json (đã rà soát).
5. Kỹ sư kiểm tra số hiệu, ngày hiệu lực, văn bản thay thế/sửa đổi, phạm vi áp dụng tại nguồn gốc; sau đó cập nhật bản đã rà soát qua commit/pull request trong Cong_ty_XD_3D.
6. Trong app: Kiểm tra mục mới để xem riêng ứng viên; Cập nhật nguồn pháp lý để nhận bản đã rà soát.

## URL JSON trong app
- Đã rà soát: https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/MEP_XD_official_catalog.json
- Ứng viên: https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/MEP_XD_source_candidates.json
- Registry: https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/MEP_XD_source_registry.json
- TCVN: https://raw.githubusercontent.com/Manhhung114/Cong_ty_XD_3D/main/data/legal/TCVN_QLDA_VPS_verified.json

Trang web chính thống và đường dẫn đúng không tự chứng minh hiệu lực pháp lý. Không tự chép toàn văn TCVN có bản quyền. Không đồng bộ hay chỉnh sửa QLDA_ver612_VPS.
