"""Native, authenticated V6.9 organizational routing dialogs.

This UI is invoked from a project task card, never directly from an untrusted
frontend. All business mutations revalidate Google identity and project scope
in SharedWorkspace, creating HMAC-signed immutable events.
"""
from __future__ import annotations

from drive_storage.access_control import identity_for, can_admin, can_upload
from drive_storage.hierarchy import (
    DEPT_LABELS, ORG_ROLES, MAX_DEPARTMENTS,
    plan_tasks, suggest_departments,
)


def hierarchy_dialog(st, action):
    from drive_storage.workspace_ui import service_for, DEPARTMENT_NAMES
    op = action["op"]
    titles = {
        "org_roles": "V6.9 · Cơ cấu nhân sự và cấp bậc",
        "hierarchy_propose": "V6.9 · Giám đốc AI lập phương án phân phối",
        "hierarchy_review": "V6.9 · Duyệt phân phối và giao xuống các cấp",
        "hierarchy_stop": "V6.9 · Dừng toàn bộ cây phân phối",
    }
    if op not in titles:
        return

    @st.dialog(titles[op], width="large",
               on_dismiss=lambda: st.session_state.pop("xd_workspace_dialog", None))
    def render():
        identity = identity_for(st)
        if not identity or not can_upload(identity):
            st.error("Bạn không có quyền điều phối trong dự án")
            return
        if st.button("Đóng", key="v690_hierarchy_close"):
            st.session_state.xd_workspace_dialog = None
            st.rerun()
            return
        try:
            service = service_for(st)
            state = service.snapshot(identity)
            pid = str(action["projectId"])
            if pid not in {p["id"] for p in state["projects"]}:
                raise PermissionError("Dự án không thuộc phạm vi được cấp")
        except (PermissionError, ValueError) as exc:
            st.error(str(exc))
            return
        except Exception:
            st.error("Không đọc được nhật ký dự án đã ký. Thao tác bị chặn để bảo toàn dữ liệu.")
            return

        def success(message):
            st.session_state.xd_workspace_feedback = message
            st.session_state.xd_workspace_dialog = None
            st.rerun()

        if op == "org_roles":
            if not can_admin(identity):
                st.error("Chỉ Admin được cấu hình nhân sự từng cấp")
                return
            st.info("Vị trí tổ chức chỉ điều phối công việc, KHÔNG tự cấp quyền "
                    "đăng nhập hoặc truy cập dự án. Tài khoản phải được Admin cấp "
                    "quyền Cập nhật và đúng dự án trong Cài đặt phân quyền.")
            known = [x for x in state.get("orgRoles", []) if x["projectId"] == pid
                     and x.get("active")]
            if known:
                st.dataframe([{
                    "Email": x["email"], "Vị trí": x["role"],
                    "Bộ môn": DEPARTMENT_NAMES.get(x["department"], x["department"]),
                    "Cập nhật lúc": x["updatedAt"],
                } for x in known], use_container_width=True, hide_index=True)
            else:
                st.caption("Chưa có nhân sự được gắn vị trí. Hệ thống vẫn phân "
                           "công Agent, nhưng người phụ trách cấp dưới để trống.")
            with st.form("v690_org_role_form"):
                email = st.text_input("Email nhân sự đã có quyền dự án",
                                      max_chars=254).strip().lower()
                role = st.selectbox("Vị trí", ["director", "pm", "lead",
                                               "engineer", "qa", "none"],
                                    format_func=lambda r: {
                                        "director": "Giám đốc", "pm": "Quản lý dự án (PM)",
                                        "lead": "Trưởng bộ môn", "engineer": "Kỹ sư",
                                        "qa": "QA/QC", "none": "Ngừng phân công vị trí",
                                    }[r])
                department = st.selectbox(
                    "Bộ môn", ["director", "qa", *DEPT_LABELS],
                    format_func=lambda d: DEPARTMENT_NAMES.get(d, d))
                approved = st.checkbox("Xác nhận cập nhật cơ cấu nhân sự dự án")
                submitted = st.form_submit_button("Lưu vị trí và ghi nhật ký", type="primary")
            if submitted:
                try:
                    if not approved:
                        raise PermissionError("Cần xác nhận thay đổi vị trí")
                    service.set_org_role(identity, project_id=pid,
                                         email=email, role=role,
                                         department=department,
                                         event_id=action["actionId"])
                    success("Đã cập nhật vị trí nhân sự dự án; phân quyền "
                            "Google và dữ liệu hồ sơ không thay đổi.")
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không ghi được cơ cấu nhân sự lên Drive.")

        elif op == "hierarchy_propose":
            task = next((t for t in state["tasks"]
                         if t["id"] == action.get("taskId")
                         and t["projectId"] == pid), None)
            if not task:
                st.error("Không tìm thấy công việc gốc")
                return
            if task["dept"] != "director" or task["assignedAgentId"] != "CEO":
                st.error("Chỉ lập sơ đồ tự động cho công việc giao Giám đốc AI (CEO)")
                return
            if not can_admin(identity) and (
                    str(task.get("assignee") or "").lower() != identity["email"].lower()):
                st.error("Chỉ Giám đốc được giao hoặc Admin được tạo phương án")
                return
            plans = [p for p in state.get("hierarchyPlans", [])
                     if p["rootTaskId"] == task["id"]]
            if any(p["status"] in {"pending", "dispatched"} for p in plans):
                st.warning("Công việc đã có phương án đang chờ duyệt hoặc đã phân phối. "
                           "Không được tạo cây công việc trùng.")
                return
            st.markdown("**Công việc cấp Giám đốc:** " + task["title"])
            hints = suggest_departments(task["title"], task.get("docCode", ""))
            st.caption("CEO định tuyến dựa trên tên và mã hồ sơ bằng quy tắc minh bạch. "
                       "Bạn có thể chỉnh bộ môn trước khi gửi. Đây chưa phải suy luận "
                       "của mô hình Gemini/OpenAI; không sinh chi phí API.")
            if hints:
                st.info("Bộ môn gợi ý: " + ", ".join(DEPT_LABELS[x] for x in hints))
            with st.form("v690_ceo_plan_form"):
                depts = st.multiselect(
                    "Bộ môn cần phân phối (1–4)",
                    options=list(DEPT_LABELS),
                    default=hints,
                    max_selections=MAX_DEPARTMENTS,
                    format_func=lambda d: DEPT_LABELS[d],
                )
                instructions = st.text_area(
                    "Chỉ dẫn của Giám đốc cho PM / trưởng bộ môn",
                    max_chars=500,
                    placeholder="Ví dụ: ưu tiên bản vẽ R01, yêu cầu QA/QC độc lập trước khi tổng hợp",
                )
                st.caption("Luồng tạo sau khi Admin duyệt: CEO → PM → "
                           "Trưởng bộ môn → Chuyên gia → QA/QC; "
                           "các bước phụ thuộc không thể chạy trước.")
                submitted = st.form_submit_button(
                    "Gửi phương án cho Admin phê duyệt", type="primary")
            if submitted:
                try:
                    service.propose_hierarchy(
                        identity, project_id=pid, task_id=task["id"],
                        departments=depts, instructions=instructions,
                        event_id=action["actionId"],
                    )
                    success("Giám đốc đã đề xuất phương án phân phối. "
                            "Chờ Admin phê duyệt để tự tạo và giao việc các cấp.")
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không ghi được phương án CEO lên Drive.")

        elif op == "hierarchy_review":
            if not can_admin(identity):
                st.error("Chỉ Admin được duyệt kế hoạch phân phối tự động")
                return
            pending = [p for p in state.get("hierarchyPlans", [])
                       if p["projectId"] == pid and p["status"] == "pending"]
            if not pending:
                st.info("Không có phương án cấp Giám đốc chờ duyệt")
                return
            target = action.get("taskId")
            with st.form("v690_hierarchy_review"):
                plan = st.selectbox(
                    "Phương án đang chờ", pending,
                    index=next((i for i, p in enumerate(pending)
                                if p["rootTaskId"] == target), 0),
                    format_func=lambda x: (
                        x["id"][:8].upper() + " · " +
                        ", ".join(DEPT_LABELS[d] for d in x["departments"])),
                )
                root = next((t for t in state["tasks"]
                             if t["id"] == plan["rootTaskId"]), None)
                if root:
                    st.caption("Công việc CEO: " + root["title"])
                st.write("Đề xuất: " + plan["instructions"])
                st.caption("Sau khi chấp thuận, hệ thống tạo " +
                           str(1 + 3 * len(plan["departments"])) +
                           " nhiệm vụ con có mã riêng, liên kết cha–con. "
                           "KHÔNG tự gọi Agent AI hoặc tự phê duyệt kỹ thuật.")
                preview = plan_tasks(
                    root=root, departments=plan["departments"],
                    dispatch_id="0" * 32, proposal_id=plan["id"],
                    roles=[r for r in state.get("orgRoles", [])
                           if r["projectId"] == pid],
                ) if root else []
                st.dataframe([{
                    "Cấp": node["stage"].upper(),
                    "Công việc": node["title"],
                    "Agent": node["agent_id"],
                    "Người phụ trách": node["assignee"] or "Chưa gán",
                } for node in preview], use_container_width=True, hide_index=True)
                decision = st.radio(
                    "Quyết định", ["approve", "reject"], horizontal=True,
                    format_func=lambda d: "Chấp thuận và phân phối" if d == "approve"
                    else "Trả phương án về Giám đốc sửa",
                )
                reason = st.text_area("Lý do trả lại (bắt buộc nếu từ chối)", max_chars=600)
                confirmed = st.checkbox(
                    "Tôi xác nhận đúng dự án, nhiệm vụ và các cấp được phân phối")
                submitted = st.form_submit_button(
                    "Xác nhận quyết định phân phối", type="primary")
            if submitted:
                try:
                    if not confirmed:
                        raise PermissionError("Cần xác nhận quyền duyệt và sơ đồ phân phối")
                    service.review_hierarchy(
                        identity, project_id=pid, proposal_id=plan["id"],
                        decision=decision, reason=reason,
                        event_id=action["actionId"],
                    )
                    if decision == "approve":
                        success("Đã duyệt kế hoạch CEO. Hệ thống tạo và giao "
                                "các nhiệm vụ PM → trưởng bộ môn → chuyên gia "
                                "→ QA/QC; phải chạy từng Agent có xác nhận.")
                    else:
                        success("Đã trả phương án về Giám đốc với lý do được lưu.")
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không lưu được quyết định phân phối; "
                             "không có nhiệm vụ giả được ghi nhận.")

        elif op == "hierarchy_stop":
            if not can_admin(identity):
                st.error("Chỉ Admin được dừng cây phân phối")
                return
            root = next((t for t in state["tasks"]
                         if t["id"] == action.get("taskId") and t["projectId"] == pid),
                        None)
            active = next((p for p in state.get("hierarchyPlans", [])
                           if root and p["rootTaskId"] == root["id"]
                           and p["status"] == "dispatched"), None)
            if not root or not active or root["status"] in {"done", "cancelled"}:
                st.error("Không có cây phân phối còn hoạt động để dừng")
                return
            members = [t for t in state["tasks"] if t.get("rootTaskId") == root["id"]]
            open_tasks = [t for t in members if t["status"] != "done"]
            st.warning("Dừng toàn bộ cây sẽ chuyển " + str(len(open_tasks)) +
                       " công việc chưa duyệt sang Đã hủy, thu hồi người và Agent. "
                       "Báo cáo, hồ sơ và những nhiệm vụ đã được phê duyệt "
                       "VẪN ĐƯỢC GIỮ NGUYÊN, không thể chạy lại các việc đã hủy.")
            st.markdown("**Công việc gốc:** " + root["title"])
            with st.form("v690_stop_hierarchy"):
                reason = st.text_area("Lý do dừng toàn bộ phân phối",
                                      max_chars=600)
                confirmed = st.checkbox(
                    "Tôi hiểu thao tác sẽ hủy tất cả nhiệm vụ chưa hoàn thành "
                    "trong cây, không xóa báo cáo và nhật ký.")
                submit = st.form_submit_button(
                    "Dừng và thu hồi toàn bộ phân phối", type="primary")
            if submit:
                try:
                    if not confirmed:
                        raise PermissionError("Cần xác nhận dừng toàn bộ cây")
                    service.stop_hierarchy(
                        identity, project_id=pid, task_id=root["id"],
                        reason=reason, event_id=action["actionId"])
                    success("Đã dừng cây phân phối, thu hồi các nhiệm vụ chưa duyệt "
                            "và lưu lý do vào nhật ký Google Drive.")
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không dừng được cây; dữ liệu hiện tại được giữ nguyên.")

    render()
