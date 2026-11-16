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

OPS = {"agent_run", "handoff_create", "handoff_resolve", "ops_audit"}


def ai_status(st):
    """Only expose the configured state, never an API key or URL."""
    config = dict(st.secrets.get("ai", {}))
    provider = str(config.get("provider") or "").lower()
    model = str(config.get("model") or "")
    configured = provider in {"openai", "gemini"} and bool(config.get("api_key")) and bool(model)
    return {"configured": configured, "provider": provider if configured else "none",
            "model": model[:100] if configured else "", "mode": "server_only_optional"}


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

    @st.dialog(titles[op], width="large")
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
            if profile["department"] != task["dept"] and agent_id not in {"CEO", "PM", "DOC", "QAC"}:
                st.error("Agent chuyên ngành không khớp bộ môn công việc")
                return
            st.markdown("**" + profile["title"] + "**")
            st.caption("Nhiệm vụ: " + task["title"] + " · Bộ môn: " +
                       DEPARTMENT_NAMES.get(task["dept"], task["dept"]))
            st.write("Đầu ra dự kiến: " + profile["output"])
            st.warning(
                "Agent chỉ đọc metadata công việc và hồ sơ đã ghi sổ; KHÔNG đọc "
                "hình học DWG/IFC, thông số trong PDF/Excel hay tự kiểm định tiêu chuẩn. "
                "Kết quả là nháp, kỹ sư phải kiểm chứng và quyết định."
            )
            configured = ai_status(st)
            with st.form("v61_agent_run_form"):
                choices = ["preflight"] + (["llm"] if configured["configured"] else [])
                mode = st.radio(
                    "Cách thực hiện", choices, horizontal=True,
                    format_func=lambda x: "Kiểm tra checklist (không AI)" if x == "preflight"
                    else f'Chạy AI thực · {configured["provider"]}/{configured["model"]}',
                )
                note = st.text_area("Yêu cầu bổ sung cho Agent (tùy chọn)",
                                    max_chars=1200, height=110)
                consent = st.checkbox(
                    "Tôi đồng ý gửi metadata công việc/dự án/hồ sơ cho nhà cung cấp AI "
                    "(nếu chọn chạy AI). Không gửi file nhị phân.",
                    value=False,
                )
                submit = st.form_submit_button(
                    "Chạy kiểm tra và lưu báo cáo nháp", type="primary"
                )
            if not configured["configured"]:
                st.caption("Chưa kích hoạt nhà cung cấp AI trên máy chủ. "
                           "Admin cấu hình [ai] provider/api_key/model trong Streamlit Secrets. "
                           "Checklist vẫn hoạt động độc lập.")
            if submit:
                try:
                    if mode == "llm" and not consent:
                        raise PermissionError("Chưa xác nhận truyền dữ liệu qua nhà cung cấp AI")
                    # One unique event ID per opened dialog; duplicate submissions
                    # never create a second signed report.
                    result = run_agent(
                        server, identity, project_id=pid,
                        task_id=task_id, agent_id=agent_id,
                        mode=mode, note=note, consent=consent,
                        ai_config=dict(st.secrets.get("ai", {})),
                        event_id=action["actionId"],
                    )
                    done("Đã lưu kết quả nháp của Agent vào lịch sử dự án. "
                         "Cần kỹ sư kiểm tra trước khi sử dụng.")
                except (PermissionError, ValueError, RuntimeError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Không thực hiện được Agent. Không ghi một kết quả giả vào lịch sử.")
        elif op == "handoff_create":
            if not tasks:
                st.info("Dự án chưa có công việc để chuyển phối hợp")
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
