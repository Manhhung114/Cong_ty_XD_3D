"""Native Streamlit UX for signed interdisciplinary coordination meetings."""
from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from drive_storage.access_control import identity_for, can_admin, can_upload
from drive_storage.coordination import (
    MAX_ACTIONS, schedule_meeting, record_minutes, decide_meeting,
    close_meeting, meetings_enabled,
)


def meeting_dialog(st, action):
    from drive_storage.workspace_ui import service_for, DEPARTMENT_NAMES
    from drive_storage.shared_workspace import DEPARTMENTS
    from drive_storage.company_agents import agents

    op = action["op"]
    titles = {
        "meeting_create": "Họp phối hợp · Tạo cuộc họp liên bộ môn",
        "meeting_minutes": "Họp phối hợp · Kết luận và giao đầu việc",
        "meeting_approve": "Họp phối hợp · Phê duyệt biên bản",
        "meeting_close": "Họp phối hợp · Xác nhận hoàn thành",
    }
    if op not in titles:
        return

    @st.dialog(titles[op], width="large",
               on_dismiss=lambda: st.session_state.pop("xd_workspace_dialog", None))
    def render():
        identity = identity_for(st)
        if not identity or not can_upload(identity):
            st.error("Tài khoản không có quyền cập nhật dự án")
            return
        if not meetings_enabled(str(action.get("projectId") or "")):
            st.warning("Quy trình họp V7.5.2 chưa được bật trên máy chủ sau kiểm thử")
            return
        if op in {"meeting_approve", "meeting_close"} and not can_admin(identity):
            st.error("Chỉ Admin được phê duyệt và đóng cuộc họp")
            return
        if st.button("Đóng", key="v752_meeting_close_dialog"):
            st.session_state.xd_workspace_dialog = None
            st.rerun()
            return
        try:
            server = service_for(st)
            snapshot = server.snapshot(identity)
            pid = str(action.get("projectId") or "")
            if pid not in {p["id"] for p in snapshot["projects"]}:
                raise PermissionError("Dự án ngoài phạm vi được cấp")
        except (PermissionError, ValueError) as error:
            st.error(str(error))
            return
        except Exception:
            st.error("Không đọc được nhật ký Drive đã ký; dừng để bảo toàn dữ liệu")
            return

        def finish(message):
            st.session_state.xd_workspace_feedback = message
            st.session_state.xd_workspace_dialog = None
            st.rerun()

        task_rows = [t for t in snapshot["tasks"]
                     if t["projectId"] == pid and t["status"] != "cancelled"]
        tasks = {t["id"]: t for t in task_rows}
        meetings = {m["id"]: m for m in snapshot.get("meetings", [])
                    if m["projectId"] == pid}
        meeting = meetings.get(action.get("meetingId"))
        dept_options = sorted(DEPARTMENTS)
        catalog = agents()

        if op == "meeting_create":
            if not task_rows:
                st.info("Hãy tạo ít nhất một công việc trước khi mở cuộc họp")
                return
            selected_task = action.get("taskId")
            suggested = [selected_task] if selected_task in tasks else []
            teams = [tasks[t]["dept"] for t in suggested]
            if len(teams) < 2:
                teams.append("bim" if "bim" not in teams else "director")
            default_teams = [t for t in dict.fromkeys(teams) if t in DEPARTMENTS]
            now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
            st.caption("Kết nối các bộ môn để xử lý xung đột thiết kế, khối lượng, "
                       "tiến độ, hồ sơ hoặc vướng mắc hiện trường.")
            with st.form("v752_meeting_create"):
                title = st.text_input("Tên cuộc họp *", max_chars=180,
                                     placeholder="Họp phối hợp Điện – HVAC – PCCC tầng 5")
                chosen_tasks = st.multiselect(
                    "Các công việc đang vướng (1–5)", options=list(tasks),
                    default=suggested, max_selections=5,
                    format_func=lambda tid: tasks[tid]["code"] + " · " + tasks[tid]["title"][:90])
                chosen_teams = st.multiselect(
                    "Bộ môn tham gia (2–8)", options=dept_options,
                    default=default_teams, max_selections=8,
                    format_func=lambda d: DEPARTMENT_NAMES.get(d, d))
                date = st.date_input("Ngày họp", value=now.date(), format="DD/MM/YYYY")
                clock = st.time_input("Giờ họp (Việt Nam)", value=now.time().replace(
                    second=0, microsecond=0))
                agenda = st.text_area(
                    "Nội dung cần phối hợp *", max_chars=1600,
                    placeholder="Mô tả xung đột/vướng mắc, hồ sơ phiên bản và phương án cần thống nhất")
                confirmed = st.checkbox("Tôi xác nhận đúng dự án và bộ môn tham gia")
                submitted = st.form_submit_button("Tạo cuộc họp và ghi nhật ký", type="primary")
            if submitted:
                try:
                    if not confirmed:
                        raise ValueError("Cần xác nhận phạm vi cuộc họp")
                    local_dt = datetime.combine(date, clock, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
                    result = schedule_meeting(
                        server, identity, project_id=pid, title=title, agenda=agenda,
                        task_ids=chosen_tasks, departments=chosen_teams,
                        scheduled_at=local_dt.isoformat(),
                        event_id=action["actionId"])
                    finish("Đã tạo cuộc họp có mã " + result["id"][:8].upper() +
                           ". Sau khi họp, ghi biên bản và đầu việc để Admin duyệt.")
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không xác minh được việc lưu cuộc họp trên Drive")

        elif not meeting:
            st.error("Cuộc họp đã bị thu hồi quyền hoặc không tồn tại")
            return

        elif op == "meeting_minutes":
            if meeting["status"] not in {"scheduled", "revision_requested"}:
                st.warning("Biên bản đã gửi duyệt hoặc cuộc họp đã kết thúc")
                return
            st.markdown("**" + meeting["title"] + "**")
            st.caption("Bộ môn: " + " · ".join(
                DEPARTMENT_NAMES.get(d, d) for d in meeting["departments"]))
            st.write("**Nội dung cần giải quyết:** " + meeting["agenda"])
            # Only signed, already executed Agent reports are shown. Never
            # synthesize fictitious contributions on behalf of an Agent.
            evidence = [run for run in snapshot.get("agentRuns", [])
                        if run["projectId"] == pid
                        and run.get("taskId") in meeting["taskIds"]]
            with st.expander("🤖 Báo cáo chuyên gia đã chạy thật (" +
                             str(len(evidence)) + ")"):
                if evidence:
                    for run in evidence[:10]:
                        st.markdown("**" + str(run.get("agentId") or "Agent") +
                                    " · " + str(run.get("mode") or "Checklist") + "**")
                        st.caption("Nguồn nhiệm vụ: " + str(run.get("taskId") or "")[:12] +
                                   " · Báo cáo DRAFT chưa được thẩm tra")
                        st.code(str(run.get("result") or "")[:2000])
                else:
                    st.info("Chưa có báo cáo Agent đã ký từ công việc liên quan. "
                            "Có thể vào Công việc/Agent để chạy kiểm tra, sau đó "
                            "quay lại họp; không phát sinh lượt AI tự động.")
            if meeting.get("revisionReason"):
                st.warning("Yêu cầu sửa: " + meeting["revisionReason"])
            rows = st.selectbox("Số đầu việc cần giao sau họp", list(range(MAX_ACTIONS+1)),
                                index=1, key="v752_meeting_count_" + meeting["id"])
            with st.form("v752_meeting_minutes"):
                minutes = st.text_area("Biên bản trao đổi *", max_chars=3000,
                                       value=meeting.get("minutes") or "", height=120)
                decisions = st.text_area("Kết luận, phương án xử lý *", max_chars=2200,
                                         value=meeting.get("decisions") or "", height=100)
                actions = []
                for i in range(rows):
                    st.markdown("**Đầu việc " + str(i+1) + "**")
                    title = st.text_input("Công việc và sản phẩm cần bàn giao",
                                          max_chars=240, key="v752_action_title_"+str(i))
                    dept = st.selectbox(
                        "Bộ môn chịu trách nhiệm", meeting["departments"],
                        key="v752_action_dept_"+str(i),
                        format_func=lambda d: DEPARTMENT_NAMES.get(d, d))
                    owner = st.text_input(
                        "Email người chịu trách nhiệm *",
                        max_chars=160, key="v752_action_owner_"+str(i))
                    deadline = st.date_input(
                        "Hạn hoàn thành", value=None, format="DD/MM/YYYY",
                        key="v752_action_deadline_"+str(i))
                    priority = st.selectbox(
                        "Ưu tiên", ["normal", "high", "critical", "low"],
                        key="v752_action_priority_"+str(i),
                        format_func=lambda k: {"normal":"Bình thường", "high":"Cao",
                                               "critical":"Khẩn cấp", "low":"Thấp"}[k])
                    eligible = [a for a in catalog.values()
                                if a["department"] == dept and a["id"] not in {"LEG", "QCX"}]
                    agent = next((a["id"] for a in eligible if a["id"] != "DOC"), "")
                    actions.append({"title": title, "dept": dept, "assignee": owner,
                                    "agent_id": agent,
                                    "due_date": deadline.isoformat() if deadline else "",
                                    "priority": priority})
                st.caption("Sau khi gửi biên bản, các đầu việc vẫn chỉ là DỰ THẢO. "
                           "Admin phải duyệt thì công việc mới được tạo thật.")
                submit = st.form_submit_button("Gửi biên bản và đầu việc cho Admin duyệt",
                                               type="primary")
            if submit:
                try:
                    record_minutes(
                        server, identity, project_id=pid, meeting_id=meeting["id"],
                        minutes=minutes, decisions=decisions, actions=actions,
                        event_id=action["actionId"])
                    finish("Đã ghi biên bản chờ duyệt; chưa giao hoặc chạy Agent.")
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không xác minh được việc lưu biên bản lên Drive")

        elif op == "meeting_approve":
            if meeting["status"] != "pending_approval":
                st.info("Cuộc họp không có biên bản đang chờ duyệt")
                return
            st.markdown("**" + meeting["title"] + "**")
            st.write("**Biên bản:** " + meeting["minutes"])
            st.write("**Kết luận:** " + meeting["decisions"])
            for row in meeting["actions"]:
                st.markdown("- **" + row["dept"] + "** — " + row["title"] +
                            " · " + row["assignee"] + " · Hạn: " +
                            (row["due_date"] or "Chưa có"))
            with st.form("v752_meeting_approval"):
                decision = st.radio("Quyết định", ["approve", "reject"], horizontal=True,
                                    format_func=lambda d: "Duyệt và tạo công việc"
                                    if d=="approve" else "Trả lại biên bản")
                reason = st.text_area("Lý do yêu cầu sửa (nếu trả lại)", max_chars=600)
                consent = st.checkbox("Xác nhận bộ môn, người phụ trách, hạn và phạm vi dự án")
                submit = st.form_submit_button("Lưu quyết định", type="primary")
            if submit:
                try:
                    if not consent:
                        raise ValueError("Cần xác nhận nội dung trước khi duyệt")
                    decide_meeting(
                        server, identity, project_id=pid, meeting_id=meeting["id"],
                        approve=decision=="approve", reason=reason,
                        event_id=action["actionId"])
                    finish("Đã duyệt kết luận và tạo " +
                           str(len(meeting["actions"])) + " nhiệm vụ có mã riêng."
                           if decision=="approve" else
                           "Đã trả biên bản, yêu cầu điều chỉnh được ghi nhật ký.")
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không xác minh được quyết định ký trên Drive")

        elif op == "meeting_close":
            st.markdown("**" + meeting["title"] + "**")
            st.metric("Đầu việc hoàn thành", str(meeting["completedActions"]) +
                      "/" + str(meeting["totalActions"]))
            if not meeting.get("readyToClose"):
                st.warning("Còn đầu việc sau họp chưa được phê duyệt hoàn thành")
                return
            if st.button("Xác nhận đã giải quyết và đóng cuộc họp", type="primary"):
                try:
                    close_meeting(
                        server, identity, project_id=pid, meeting_id=meeting["id"],
                        event_id=action["actionId"])
                    finish("Đã đóng cuộc họp sau khi toàn bộ công việc được duyệt.")
                except (PermissionError, ValueError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Không xác minh được trạng thái cuộc họp trên Drive")

    render()
