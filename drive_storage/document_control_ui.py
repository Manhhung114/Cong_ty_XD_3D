"""V6.0.1 in-sheet document control: live Drive inventory, signed status & audit.

No separate uploader page. This is a Streamlit dialog launched from the existing
Documents sheet, and every read/mutation is gated by verified OIDC + project ACL.
"""
from __future__ import annotations

import csv
import io

from drive_storage.access_control import identity_for, can_admin, can_upload
from drive_storage.document_control import (
    STATUS_LABELS, archive_document, inventory, review_document,
    submit_document, update_metadata,
)
from drive_storage.manager import FOLDER_CATEGORIES
from drive_storage.workspace_ui import service_for

DOWNLOAD_LIMIT = 40 * 1024 * 1024


def _csv_cell(value):
    value = str(value if value is not None else "")
    # Excel/LibreOffice must not execute user-supplied document codes/names.
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value


def inventory_csv(items):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Mã hồ sơ", "Tên file", "Dự án", "Nhóm", "Phiên bản", "Mới nhất",
        "Trạng thái", "Dung lượng (bytes)", "Ngày tạo Drive", "Cập nhật Drive",
        "Người đăng ký trong app", "Ngày đăng ký", "Công việc", "Mô tả",
        "Đã ghi sổ", "Không tìm thấy", "File đã thay đổi", "File ID",
    ])
    for item in items:
        writer.writerow([_csv_cell(value) for value in (
            item["code"], item["filename"], item["projectId"],
            item["category"], item["revision"], "Có" if item["latest"] else "Không",
            STATUS_LABELS.get(item["status"], item["status"]), item["sizeBytes"],
            item["createdTime"], item["modifiedTime"], item["actor"],
            item["registeredAt"], item["taskId"], item["description"],
            "Có" if item["registered"] else "Chưa", "Có" if item["missing"] else "Không",
            "Có" if item["integrityWarning"] else "Không", item["id"],
        )])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def document_control_dialog(st, action):
    if action.get("op") != "document_manage" or action.get("section") != "documents":
        return

    @st.dialog("📚 Kho tài liệu · Kiểm kê & kiểm soát hồ sơ", width="large",
               on_dismiss=lambda: st.session_state.pop("xd_workspace_dialog", None))
    def render():
        actor = identity_for(st)
        if not actor:
            st.error("Phiên đăng nhập không còn hợp lệ")
            return
        if st.button("Đóng", key="v601_doc_close"):
            st.session_state.xd_workspace_dialog = None
            st.session_state.xd_doc_inventory_requested = True
            st.rerun()

        pid = str(action.get("projectId") or "")
        try:
            server = service_for(st)
            result = inventory(server, actor, pid)
            items = result["items"]
            counters = result["counts"]
            project = server.storage.project_by_id(pid)
        except (PermissionError, ValueError) as exc:
            st.error(str(exc))
            return
        except Exception:
            st.error("Không kiểm kê được Google Drive. Không thay đổi dữ liệu tài liệu.")
            return

        st.caption("Dự án: " + project["name"] + " • Nguồn kiểm kê: tất cả thư mục Drive thuộc dự án.")
        cols = st.columns(4)
        cols[0].metric("Tệp trên Drive / sổ", counters["total"])
        cols[1].metric("Chưa lập sổ", counters["unregistered"])
        cols[2].metric("Chờ duyệt", counters["pending"])
        cols[3].metric("Mất liên kết", counters["missing"])
        if counters["modified"]:
            st.warning(f'{counters["modified"]} tệp đã thay đổi dung lượng/checksum so với lần đăng ký. Kiểm tra trước khi phê duyệt.')
        if counters["unregistered"]:
            st.info(f'Còn {counters["unregistered"]} tệp Drive chưa lập sổ. Chọn tệp bên dưới để bổ sung mã hồ sơ và bộ môn.')

        with st.expander("📊 Xuất báo cáo kiểm kê CSV", expanded=False):
            st.download_button(
                "⬇ Tải danh mục và trạng thái", data=inventory_csv(items),
                file_name="XD_MEP_Kiem_ke_" + project["name"].split("_", 1)[0] + ".csv",
                mime="text/csv", key="v601_inventory_export",
            )
            st.caption("CSV gồm toàn bộ tệp đã và chưa lập sổ, phiên bản, trạng thái, người ghi sổ và cảnh báo kiểm soát.")

        if not items:
            st.info("Dự án chưa có tệp trong các thư mục Drive. Dùng nút Tải tệp lên ngay tại sheet Kho tài liệu.")
            return

        search = st.text_input("Tìm mã hồ sơ, tên file, người ghi sổ", key="v601_document_search")
        category = st.selectbox(
            "Lọc nhóm hồ sơ", ["all", *FOLDER_CATEGORIES],
            format_func=lambda v: "Tất cả nhóm" if v == "all" else " / ".join(FOLDER_CATEGORIES[v]),
            key="v601_document_category",
        )
        status = st.selectbox(
            "Lọc trạng thái", ["all", *STATUS_LABELS],
            format_func=lambda v: "Tất cả trạng thái" if v == "all" else STATUS_LABELS[v],
            key="v601_document_status",
        )
        q = search.strip().casefold()
        visible = [
            f for f in items
            if (category == "all" or f["category"] == category)
            and (status == "all" or f["status"] == status)
            and (not q or q in (" ".join((f["code"], f["filename"], f["actor"]))).casefold())
        ]
        if not visible:
            st.info("Không có tệp phù hợp bộ lọc.")
            return

        st.caption(f'Đang lọc {len(visible)}/{len(items)} tệp.')
        default = next((idx for idx, f in enumerate(visible)
                        if f["id"] == action.get("fileId")), 0)
        selected = st.selectbox(
            "Chọn hồ sơ để quản lý", visible, index=default,
            format_func=lambda f: (
                f'{f["code"]} · {f["revision"] or "-"} · '
                f'{STATUS_LABELS.get(f["status"], f["status"])} · {f["filename"]}'
            ),
            key="v601_selected_document",
        )
        st.divider()
        st.subheader("Chi tiết hồ sơ")
        st.text("Mã hồ sơ: " + selected["code"])
        st.text("Tên file Drive: " + selected["filename"])
        st.text("Nhóm: " + " / ".join(FOLDER_CATEGORIES[selected["category"]]))
        st.text("Phiên bản: " + (selected["revision"] or "Chưa đánh số"))
        st.text("Trạng thái: " + STATUS_LABELS.get(selected["status"], selected["status"]))
        st.text("Dung lượng: " + f'{selected["sizeBytes"] / 1048576:.2f} MB')
        st.text("Ngày tạo Drive: " + (selected["createdTime"] or "Không có metadata"))
        st.text("Cập nhật Drive: " + (selected["modifiedTime"] or "Không có metadata"))
        st.text("Người ghi sổ: " + (selected["actor"] or "Chưa xác định (tệp cũ)"))
        st.text("Ngày ghi sổ: " + (selected["registeredAt"] or "Chưa đăng ký"))
        st.text("Mô tả: " + (selected["description"] or "Chưa có"))
        if selected["integrityWarning"]:
            st.error("Checksum hoặc kích thước tệp khác bản đã ghi sổ. Không nên sử dụng như hồ sơ đã xác nhận.")
        if selected["missing"]:
            st.error("Tệp đã từng được ghi sổ nhưng không còn trong thư mục Drive đã kiểm kê. Không thể tải xuống hoặc duyệt.")
        elif selected["webViewLink"]:
            st.link_button("Mở tệp trên Google Drive", selected["webViewLink"])
        if not selected["missing"] and 0 < selected["sizeBytes"] <= DOWNLOAD_LIMIT:
            key = "v601_dl_" + selected["id"]
            if st.button("Chuẩn bị tệp tải xuống", key="v601_prepare_" + selected["id"]):
                try:
                    st.session_state[key] = server.storage.download_small_file(
                        project_id=pid, category=selected["category"], file_id=selected["id"],
                    )
                except Exception:
                    st.error("Không thể lấy tệp từ Drive. Kiểm tra quyền và vị trí tệp.")
            if key in st.session_state:
                st.download_button(
                    "⬇ Tải bản gốc", data=st.session_state[key],
                    file_name=selected["filename"], key="v601_download_" + selected["id"],
                )
        elif selected["sizeBytes"] > DOWNLOAD_LIMIT and not selected["missing"]:
            st.caption("Tệp trên 40 MB: tải trực tiếp qua Google Drive và cần quyền với thư mục. Chưa có proxy tải lớn.")

        family = [f for f in items if f["group"] == selected["group"]]
        if len(family) > 1:
            with st.expander(f"Lịch sử phiên bản ({len(family)} file)", expanded=False):
                st.dataframe([{
                    "Revision": f["revision"], "Tệp": f["filename"],
                    "Mới nhất": "Có" if f["latest"] else "Không",
                    "Trạng thái": STATUS_LABELS.get(f["status"], f["status"]),
                    "Ngày tải": f["createdTime"], "Người ghi sổ": f["actor"] or "Chưa rõ",
                } for f in family], hide_index=True, use_container_width=True)

        history = selected.get("history", [])
        if history:
            with st.expander(f"Lịch sử thao tác ({len(history)})", expanded=False):
                st.dataframe([{
                    "Thời điểm": h["at"], "Người thực hiện": h["actor"],
                    "Thao tác": h["action"], "Nội dung": h.get("note", ""),
                } for h in history], hide_index=True, use_container_width=True)
        else:
            st.info("Tệp chưa có lịch sử thao tác trong ứng dụng. Ngày tạo Drive không xác định được người tải qua app.")

        if selected["missing"] or selected["integrityWarning"]:
            st.warning("Đã khóa chỉnh sửa/trình duyệt cho tệp mất liên kết hoặc sai checksum. Admin kiểm tra bản gốc trước.")
            return
        tasks = [t for t in server.snapshot(actor)["tasks"] if t["projectId"] == pid]
        selected_task = selected.get("taskId") or ""
        choices = [""] + [t["id"] for t in tasks]
        task_names = {t["id"]: t["code"] + " · " + t["title"] for t in tasks}
        task_index = choices.index(selected_task) if selected_task in choices else 0

        def feedback(message):
            st.session_state.xd_workspace_feedback = message
            st.session_state.xd_doc_inventory_requested = True
            st.session_state.xd_workspace_dialog = None
            st.rerun()

        if can_upload(actor) and selected["status"] == "unregistered":
            with st.form("v601_register_document_" + selected["id"]):
                st.markdown("**Ghi hồ sơ có sẵn trên Drive vào sổ quản lý**")
                code = st.text_input("Mã hồ sơ", value=selected["code"], max_chars=80)
                desc = st.text_area("Mô tả / nội dung", max_chars=600)
                link = st.selectbox("Gắn công việc", choices, index=task_index,
                                    format_func=lambda v: task_names.get(v, "Không gắn công việc"))
                save = st.form_submit_button("📒 Lập sổ hồ sơ", type="primary")
            if save:
                try:
                    server.register_document(
                        actor, project_id=pid, category=selected["category"],
                        file_id=selected["id"], code=code, description=desc, task_id=link,
                    )
                    feedback("Đã lập sổ hồ sơ, bắt đầu theo dõi phiên bản và người phụ trách.")
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không thể lập sổ. Tệp vẫn nguyên vẹn trên Drive.")
            return

        if can_upload(actor) and selected["status"] in {"draft", "returned"}:
            with st.form("v601_edit_document_" + selected["id"]):
                st.markdown("**Cập nhật thông tin hồ sơ** (không thay đổi file gốc)")
                code = st.text_input("Mã hồ sơ", value=selected["code"], max_chars=80)
                desc = st.text_area("Mô tả", value=selected["description"], max_chars=600)
                link = st.selectbox("Công việc liên quan", choices, index=task_index,
                                    format_func=lambda v: task_names.get(v, "Không gắn công việc"))
                save = st.form_submit_button("Lưu thông tin")
            if save:
                try:
                    update_metadata(server, actor, project_id=pid, file_id=selected["id"],
                                    code=code, description=desc, task_id=link)
                    feedback("Đã cập nhật metadata, lịch sử chỉnh sửa được ghi lại.")
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không thể cập nhật thông tin hồ sơ.")
            with st.form("v601_submit_document_" + selected["id"]):
                st.markdown("**Trình hồ sơ để Admin duyệt**")
                comment = st.text_area("Ghi chú trình hồ sơ", max_chars=1000)
                submit = st.form_submit_button("Trình phê duyệt", type="primary")
            if submit:
                try:
                    submit_document(server, actor, project_id=pid,
                                    file_id=selected["id"], comment=comment)
                    feedback("Hồ sơ đã được trình duyệt và lưu người gửi trong lịch sử.")
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không thể trình duyệt hồ sơ.")

        if can_admin(actor) and selected["status"] == "pending":
            with st.form("v601_review_document_" + selected["id"]):
                st.markdown("**Phê duyệt hồ sơ bằng tài khoản Admin**")
                decision = st.radio(
                    "Quyết định", ["approve", "return"], horizontal=True,
                    format_func=lambda d: "Phê duyệt" if d == "approve" else "Trả lại",
                )
                comment = st.text_area("Nhận xét / lý do trả lại", max_chars=2000)
                confirmed = st.checkbox("Tôi đã kiểm tra tệp gốc và xác nhận quyết định")
                submit = st.form_submit_button("Lưu quyết định", type="primary")
            if submit:
                try:
                    if not confirmed:
                        raise PermissionError("Phải xác nhận đã kiểm tra tệp trước khi duyệt")
                    review_document(server, actor, project_id=pid, file_id=selected["id"],
                                    decision=decision, comment=comment)
                    feedback("Hồ sơ đã được phê duyệt." if decision == "approve" else
                             "Hồ sơ không được chấp thuận: đã trả lại để bổ sung. Xem lý do trong Kho tài liệu.")
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không thể lưu quyết định duyệt hồ sơ.")

        if can_admin(actor) and selected["status"] not in {"unregistered", "archived"}:
            with st.expander("Lưu trữ hồ sơ (không xóa tệp gốc)", expanded=False):
                with st.form("v601_archive_" + selected["id"]):
                    note = st.text_input("Lý do chuyển lưu trữ", max_chars=500)
                    accepted = st.checkbox("Xác nhận chỉ đổi trạng thái, không xóa file Drive")
                    submit = st.form_submit_button("Chuyển trạng thái Lưu trữ")
                if submit:
                    try:
                        if not accepted:
                            raise PermissionError("Cần xác nhận trước khi chuyển lưu trữ")
                        archive_document(server, actor, project_id=pid, file_id=selected["id"],
                                         comment=note)
                        feedback("Đã chuyển hồ sơ sang trạng thái lưu trữ, tệp gốc được giữ nguyên.")
                    except (ValueError, PermissionError) as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Không thể lưu trạng thái hồ sơ.")

    render()
