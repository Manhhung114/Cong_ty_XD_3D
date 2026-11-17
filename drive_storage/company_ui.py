"""Authenticated native V6.1-V6.3 agent and whole-company work dialogs.

No browser-side secret and no autonomous write/approval. Server verifies OAuth,
project ACL, agent specialization and user consent on each execution.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from drive_storage.access_control import identity_for, can_upload, can_admin
from drive_storage.company_agents import (
    agents, run_agent, create_handoff, resolve_handoff, company_metrics,
    export_integrity_report,
)
from drive_storage.workspace_ui import service_for, DEPARTMENT_NAMES
from drive_storage.expert_orchestrator import run_expert
from drive_storage.expert_tools import MAX_BYTES, SUPPORTED, NOT_SUPPORTED
from drive_storage.ai_vault import effective_config
from drive_storage.live_agents import safe_failure_code

OPS = {"agent_run", "handoff_create", "handoff_resolve", "ops_audit"}


def ai_status(st):
    """Expose only non-secret status; a corrupt shared vault disables AI."""
    from drive_storage.ai_vault import safe_status
    try:
        return safe_status(st)
    except Exception:
        # The dashboard stays usable even if the secret vault needs recovery.
        # Any real AI run will fail closed when resolving its credentials.
        return {"configured": False, "provider": "none", "model": "",
                "shared": False, "mode": "server_only", "error": "vault_unavailable"}


def company_dialog(st, action):
    op = action.get("op")
    if op not in OPS:
        return
    titles = {
        "agent_run": "V6.1 · Chạy chuyên viên AI theo nhiệm vụ",
        "handoff_create": "V6.2 · Yêu cầu phối hợp liên phòng",
        "handoff_resolve": "V6.2 · Xác nhận bàn giao liên phòng",
        "ops_audit": "V6.3 · Kiểm soát vận hành & sao lưu dữ liệu",
    }

    @st.dialog(titles[op], width="large",
               on_dismiss=lambda: st.session_state.pop("xd_workspace_dialog", None))
    def render():
        identity = identity_for(st)
        if not identity:
            st.error("Tài khoản Google không còn quyền truy cập")
            return
        if op != "ops_audit" and not can_upload(identity):
            st.error("Quyền Chỉ đọc không được tạo kết quả Agent hoặc thay đổi nhiệm vụ")
            return
        if op == "ops_audit" and not can_admin(identity):
            st.error("Chỉ Admin được xuất dữ liệu kiểm soát của công ty")
            return
        if st.button("Đóng", key="v63_company_dialog_close"):
            st.session_state.xd_workspace_dialog = None
            st.rerun()
        try:
            server = service_for(st)
            state = server.snapshot(identity)
            pid = str(action.get("projectId") or "")
            allowed = {p["id"] for p in state["projects"]}
            if op != "ops_audit" and pid not in allowed:
                raise PermissionError("Dự án không nằm trong phạm vi được cấp")
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
            return
        except Exception:
            st.error("Không tải được dữ liệu máy chủ đã ký. Tạm dừng thao tác.")
            return

        def done(message):
            st.session_state.xd_workspace_feedback = message
            st.session_state.xd_workspace_dialog = None
            st.rerun()

        tasks = [t for t in state["tasks"] if t["projectId"] == pid]
        if op == "agent_run":
            task_id = str(action.get("taskId") or "")
            agent_id = str(action.get("agentId") or "")
            profile = agents().get(agent_id)
            task = next((x for x in tasks if x["id"] == task_id), None)
            if not profile or not task:
                st.error("Agent hoặc công việc không tồn tại trong dự án")
                return
            if task.get("status") == "cancelled":
                st.error("Công việc đã hủy; không thể chạy Agent.")
                return
            if profile["department"] != task["dept"] and agent_id not in {"CEO", "PM", "DOC", "QAC"}:
                st.error("Agent chuyên ngành không khớp bộ môn công việc")
                return
            st.markdown("**" + profile["title"] + "**")
            st.caption("Nhiệm vụ: " + task["title"] + " · Bộ môn: " +
                       DEPARTMENT_NAMES.get(task["dept"], task["dept"]))
            st.write("Đầu ra dự kiến: " + profile["output"])
            st.info(
                "V6.4 đọc có giới hạn các file PDF, Excel (.xlsx), CSV, DXF và "
                "phần tử IFC đã ghi sổ trên Drive (tối đa 50 MB/file). "
                "V6.5 kiểm tra công thức với nguồn đối chiếu; V6.6 tổ chức "
                "chuyên gia → DOC → QA/QC → PM. DWG/RVT, IFC geometry clash "
                "và file lớn vẫn cần bộ chuyển đổi/worker riêng. "
                "Kết quả không thay thế nghiệm thu và chữ ký kỹ sư."
            )
            configured = ai_status(st)
            from pathlib import PurePath
            allowed_categories = set(profile.get("expected_categories", []))
            file_docs = [
                d for d in state["documents"]
                if d["projectId"] == pid
                and (d["category"] in allowed_categories
                     or agent_id in {"CEO", "PM", "DOC", "QAC"})
                and PurePath(d["filename"]).suffix.lower() in SUPPORTED
                and (not d.get("sizeBytes") or int(d["sizeBytes"]) <= MAX_BYTES)
                and d.get("status") not in {"archived"}
            ]
            if not file_docs:
                st.warning(
                    "Không có file kỹ thuật phù hợp để Agent đọc. Hãy kiểm tra đúng dự án, "
                    "đã ghi sổ hồ sơ, nhóm tài liệu của Agent, định dạng PDF/XLSX/CSV/DXF/IFC "
                    "và dung lượng tối đa 50 MB. DWG/RVT chưa được đọc trực tiếp."
                )
            else:
                st.caption(f"Đã tìm thấy {len(file_docs)} file phù hợp trong sổ hồ sơ "
                           "của dự án. Giới hạn 50 MB/file; Agent chỉ trích xuất mẫu "
                           "theo giới hạn an toàn, không xác nhận đã đọc toàn bộ file.")
            with st.form("v61_agent_run_form"):
                choices = ["preflight", "expert"]
                if configured["configured"]:
                    choices += ["llm", "expert_llm"]
                mode = st.radio(
                    "Cách thực hiện", choices, horizontal=True,
                    format_func=lambda x: {
                        "preflight": "Checklist hồ sơ",
                        "expert": "Chuyên gia phân tích file thật",
                        "llm": f'AI metadata · {configured["provider"]}',
                        "expert_llm": f'AI + trích xuất file · {configured["provider"]}',
                    }[x],
                )
                selected = st.selectbox(
                    "File kỹ thuật đã ghi sổ (áp dụng khi chọn Chuyên gia)",
                    [None, *file_docs],
                    format_func=lambda d: "— Chưa chọn file —" if d is None else
                        d["code"] + " · " + d.get("revision", "") + " · " + d["filename"],
                )
                note = st.text_area("Yêu cầu bổ sung cho Agent (tùy chọn)",
                                    max_chars=700, height=110)
                consent = st.checkbox(
                    "Nếu chạy AI: tôi đồng ý gửi metadata hoặc trích xuất MẪU "
                    "từ file kỹ thuật đến nhà cung cấp AI. Không gửi tệp nhị phân.",
                    value=False,
                )
                submit = st.form_submit_button(
                    "Chạy chuyên gia và lưu báo cáo nháp", type="primary"
                )
            if not configured["configured"]:
                st.caption("Chưa kích hoạt nhà cung cấp AI trên máy chủ. "
                           "Admin vào Cài đặt → API dùng chung để lưu khóa trên Drive. "
                           "Checklist vẫn hoạt động độc lập.")
            if submit:
                started = False
                attempt_id = action["actionId"]
                def note_failure(exc):
                    if not started:
                        return
                    try:
                        server.record_agent_failure(
                            identity, project_id=pid, task_id=task_id,
                            agent_id=agent_id, mode=mode, attempt_id=attempt_id,
                            code=safe_failure_code(exc),
                        )
                    except Exception:
                        # Never replace the original error with another error,
                        # and never assert a signed failure was saved if not.
                        st.warning("Không ghi được trạng thái lỗi vào nhật ký "
                                   "giám sát. Kiểm tra lại kết nối Drive.")
                try:
                    if mode in {"llm", "expert_llm"} and not consent:
                        raise PermissionError("Chưa xác nhận truyền dữ liệu đến nhà cung cấp AI")
                    if mode in {"expert", "expert_llm"} and selected is None:
                        raise ValueError("Cần chọn file đã ghi sổ để phân tích kỹ thuật")
                    attempt = server.record_agent_start(
                        identity, project_id=pid, task_id=task_id,
                        agent_id=agent_id, mode=mode, attempt_id=attempt_id,
                    )
                    if attempt.get("completed"):
                        done("Lượt Agent này đã được lưu trước đó; "
                             "không chạy lại để tránh nhân đôi kết quả/chi phí.")
                        return
                    if attempt.get("existing"):
                        st.warning("Lượt Agent này đã được bắt đầu trước đó. "
                                   "Không thực thi lại cùng mã để tránh phát sinh "
                                   "phí AI hoặc báo cáo trùng. Đóng và mở lại "
                                   "công việc để tạo yêu cầu mới.")
                        return
                    started = True
                    if mode in {"expert", "expert_llm"}:
                        result = run_expert(
                            server, identity, project_id=pid, task_id=task_id,
                            agent_id=agent_id, file_id=selected["id"], mode=mode,
                            note=note, consent=consent,
                            ai_config=effective_config(st, agent_id) if mode == "expert_llm" else {},
                            event_id=action["actionId"],
                        )
                    else:
                        result = run_agent(
                            server, identity, project_id=pid,
                            task_id=task_id, agent_id=agent_id,
                            mode=mode, note=note, consent=consent,
                            ai_config=effective_config(st, agent_id) if mode == "llm" else {},
                            event_id=action["actionId"],
                        )
                    done("Agent đã chạy và lưu báo cáo nháp có nguồn. "
                         "Công việc chưa được duyệt. Kỹ sư cần kiểm chứng, "
                         "sau đó bấm Gửi báo cáo phê duyệt trên thẻ công việc.")
                except (PermissionError, ValueError, RuntimeError) as exc:
                    note_failure(exc)
                    st.error("Chưa lưu báo cáo Agent: " + str(exc))
                    st.info("Cửa sổ vẫn mở để bạn sửa lựa chọn rồi thử lại. "
                            "Nếu Gemini bị giới hạn lượt gọi, có thể chọn "
                            "'Chuyên gia phân tích file thật' để phân tích "
                            "không dùng API. Không tạo báo cáo giả.")
                except Exception as exc:
                    note_failure(exc)
                    st.error("Agent chưa hoàn thành, không lưu kết quả mới. "
                             "Kiểm tra tình trạng Google Drive, giới hạn máy chủ "
                             "và nhật ký ứng dụng trước khi thử lại.")
        elif op == "handoff_create":
            tasks = [task for task in tasks if task.get("status") != "cancelled"]
            if not tasks:
                st.info("Dự án chưa có công việc đang hoạt động để chuyển phối hợp")
                return
            with st.form("v62_handoff_new"):
                selected_task = st.selectbox(
                    "Công việc cần phối hợp", tasks,
                    index=next((i for i,t in enumerate(tasks)
                                if t["id"] == action.get("taskId")), 0),
                    format_func=lambda t: t["code"] + " · " + t["title"],
                )
                targets = sorted(set(p["department"] for p in agents().values())
                                 - {selected_task["dept"]})
                target = st.selectbox(
                    "Phòng nhận phối hợp", targets,
                    format_func=lambda dept: DEPARTMENT_NAMES.get(dept, dept),
                )
                reason = st.text_area("Vấn đề cần xử lý / dữ liệu cần bàn giao",
                                      max_chars=800, height=140)
                submit = st.form_submit_button("Gửi yêu cầu phối hợp", type="primary")
            if submit:
                try:
                    create_handoff(
                        server, identity, project_id=pid, task_id=selected_task["id"],
                        target_department=target, reason=reason,
                        event_id=action["actionId"],
                    )
                    done("Đã gửi yêu cầu phối hợp có mã, người gửi và phòng nhận.")
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không lưu được yêu cầu phối hợp.")
        elif op == "handoff_resolve":
            handoffs = [h for h in state.get("handoffs", [])
                        if h["projectId"] == pid and h["status"] == "open"]
            handoff = next((h for h in handoffs
                            if h["id"] == action.get("handoffId")), None)
            if not handoff:
                st.error("Không tìm thấy yêu cầu phối hợp đang mở")
                return
            st.markdown("**" + handoff["title"] + "**")
            st.write("Phòng nhận: " + DEPARTMENT_NAMES.get(handoff["targetDept"], handoff["targetDept"]))
            st.write("Yêu cầu: " + handoff["reason"])
            st.caption("Người đề nghị: " + handoff["actor"])
            with st.form("v62_handoff_resolve"):
                response = st.text_area("Nội dung trả lời / kết quả phối hợp",
                                         max_chars=900, height=150)
                confirmed = st.checkbox("Tôi xác nhận đã kiểm tra nội dung bàn giao")
                submit = st.form_submit_button("Ghi nhận đã phối hợp", type="primary")
            if submit:
                try:
                    if not confirmed:
                        raise PermissionError("Cần xác nhận nội dung phối hợp")
                    resolve_handoff(
                        server, identity, project_id=pid,
                        handoff_id=handoff["id"], response=response,
                        event_id=action["actionId"],
                    )
                    done("Đã ghi nhận trả lời phối hợp và đóng luồng bàn giao.")
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không cập nhật được yêu cầu phối hợp.")

        elif op == "ops_audit":
            st.markdown("**Kiểm tra tình trạng công ty và sao lưu metadata**")
            st.caption(
                "Kiểm tra chữ ký HMAC trên sự kiện, ghi nhật ký, trạng thái dự án. "
                "Không sao lưu file gốc Google Drive và không có thao tác khôi phục ghi đè."
            )
            metrics = company_metrics(state)
            columns = st.columns(4)
            columns[0].metric("Dự án", metrics["projects"])
            columns[1].metric("Quá hạn", metrics["overdue"])
            columns[2].metric("Chờ duyệt", metrics["review"])
            columns[3].metric("Chờ phối hợp", metrics["handoffsOpen"])
            if metrics["alerts"]:
                for alert in metrics["alerts"]:
                    st.warning(alert["title"] + " → " + alert["action"])
            try:
                report = export_integrity_report(server, identity, state)
            except Exception:
                st.error("Không thể xác minh toàn bộ nhật ký ký số HMAC; không xuất bản sao chưa kiểm chứng.")
                return
            if report["validation"]["passed"]:
                st.success(f'Đã xác minh {report["eventCount"]} sự kiện trong kho nhật ký.')
            else:
                st.error("Báo cáo phát hiện bất thường: " +
                         ", ".join(report["validation"]["warnings"]))
            data = json.dumps(report, ensure_ascii=False, indent=2).encode("utf8")
            st.download_button(
                "⬇ Xuất bản sao metadata & lịch sử đã kiểm chứng",
                data=data,
                file_name="XD_MEP_BACKUP_V63_" +
                          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json",
                mime="application/json", key="v63_audit_backup_download",
            )
            st.info(
                "Khôi phục chưa được phép tự động để tránh xung đột với file đang hoạt động. "
                "Lưu cả bản sao dữ liệu và bản sao Google Drive ở nơi an toàn do công ty kiểm soát."
            )
    render()
