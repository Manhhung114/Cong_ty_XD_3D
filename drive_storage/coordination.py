"""V7.5.2 signed, project-scoped interdisciplinary coordination meetings.

Meeting minutes are DRAFT until Admin approval. Approval creates up to six
traceable tasks in ONE signed event; no LLM or worker is auto-invoked.
"""
from __future__ import annotations

from datetime import datetime
import re

from drive_storage.access_control import can_admin, can_upload, clean_email
from drive_storage.shared_workspace import (
    DEPARTMENTS, CANARY_LEDGER_LIMIT, _clean_text, _require_id,
)

MAX_MEETING_TEAMS = 8
MAX_MEETING_TASKS = 5
MAX_ACTIONS = 6
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _meeting(workspace, identity, project_id, meeting_id):
    pid = workspace._check_project(identity, project_id, True)
    _require_id(meeting_id, "Mã cuộc họp")
    meeting = next((m for m in workspace.snapshot(identity).get("meetings", [])
                    if m["id"] == meeting_id and m["projectId"] == pid), None)
    if meeting is None:
        raise PermissionError("Cuộc họp không thuộc dự án được cấp quyền")
    return pid, meeting


def _capacity(workspace):
    # The ledger currently has a hard 2500-event limit.
    if len(workspace._records()) >= CANARY_LEDGER_LIMIT:
        raise PermissionError("Nhật ký gần đầy; tạm ngừng tạo luồng mới để bảo toàn dữ liệu")


def schedule_meeting(workspace, identity, *, project_id, title, agenda, task_ids,
                     departments, scheduled_at, event_id=None):
    if not can_upload(identity):
        raise PermissionError("Chỉ tài khoản được cập nhật mới được lập cuộc họp")
    pid = workspace._check_project(identity, project_id, True)
    current = workspace.snapshot(identity)
    valid_tasks = {t["id"]: t for t in current["tasks"]
                   if t["projectId"] == pid and t["status"] != "cancelled"}
    unique_tasks = list(dict.fromkeys(task_ids))
    unique_teams = list(dict.fromkeys(departments))
    if (not 1 <= len(unique_tasks) <= MAX_MEETING_TASKS or
            len(unique_tasks) != len(task_ids) or
            any(t not in valid_tasks for t in unique_tasks)):
        raise ValueError("Chọn 1–5 nhiệm vụ đang hoạt động trong đúng dự án")
    if (not 2 <= len(unique_teams) <= MAX_MEETING_TEAMS or
            len(unique_teams) != len(departments) or
            any(team not in DEPARTMENTS for team in unique_teams)):
        raise ValueError("Cuộc họp cần 2–8 bộ môn hợp lệ")
    title = _clean_text(title, 180, True)
    agenda = _clean_text(agenda, 1600, True)
    if len(title) < 5 or len(agenda) < 15:
        raise ValueError("Cần tên cuộc họp và nội dung phối hợp rõ ràng")
    try:
        scheduled = datetime.fromisoformat(scheduled_at)
    except (TypeError, ValueError) as exc:
        raise ValueError("Ngày giờ cuộc họp không hợp lệ") from exc
    if scheduled.tzinfo is None:
        raise ValueError("Phải ghi rõ múi giờ cuộc họp")
    _capacity(workspace)
    return workspace._append(
        identity=identity, project_id=pid, action="meeting.created",
        data={"title": title, "agenda": agenda, "tasks": unique_tasks,
              "departments": unique_teams, "scheduled_at": scheduled.isoformat()},
        event_id=event_id,
    )


def _actions(raw, participants):
    if not isinstance(raw, list) or len(raw) > MAX_ACTIONS:
        raise ValueError("Biên bản chỉ có tối đa 6 đầu việc được giao")
    seen = set()
    out = []
    from drive_storage.company_agents import agents
    catalog = agents()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("Dòng phân công không hợp lệ")
        dept = str(row.get("dept") or "")
        if dept not in participants or dept not in DEPARTMENTS:
            raise PermissionError("Không thể giao đầu việc cho bộ môn ngoài cuộc họp")
        title = _clean_text(row.get("title"), 240, True)
        if len(title) < 8:
            raise ValueError("Công việc sau họp phải mô tả rõ đầu ra")
        key = (dept, title.casefold())
        if key in seen:
            raise ValueError("Đầu việc sau họp bị trùng")
        seen.add(key)
        agent = str(row.get("agent_id") or "")
        if agent and (agent not in catalog or catalog[agent]["department"] != dept or
                      agent in {"LEG", "QCX"}):
            raise PermissionError("Agent không thuộc bộ môn hoặc chưa được cấp phép")
        due = str(row.get("due_date") or "")
        if due and (not _DATE.fullmatch(due)):
            raise ValueError("Hạn công việc phải ở định dạng YYYY-MM-DD")
        owner = clean_email(row.get("assignee"))
        priority = str(row.get("priority") or "normal")
        if priority not in {"low", "normal", "high", "critical"}:
            raise ValueError("Mức độ ưu tiên không hợp lệ")
        out.append({"title": title, "dept": dept, "assignee": owner,
                    "agent_id": agent, "due_date": due, "priority": priority})
    return out


def record_minutes(workspace, identity, *, project_id, meeting_id, minutes,
                   decisions, actions, event_id=None):
    if not can_upload(identity):
        raise PermissionError("Không có quyền ghi biên bản")
    pid, meeting = _meeting(workspace, identity, project_id, meeting_id)
    if meeting["status"] not in {"scheduled", "revision_requested"}:
        raise ValueError("Chỉ biên bản chưa duyệt mới được gửi lại")
    minutes = _clean_text(minutes, 3000, True)
    decisions = _clean_text(decisions, 2200, True)
    if len(minutes) < 25 or len(decisions) < 12:
        raise ValueError("Cần ghi diễn biến và kết luận họp rõ ràng")
    parsed = _actions(actions, meeting["departments"])
    _capacity(workspace)
    return workspace._append(
        identity=identity, project_id=pid, action="meeting.minutes",
        data={"meeting_id": meeting_id, "minutes": minutes,
              "decisions": decisions, "actions": parsed},
        event_id=event_id,
    )


def decide_meeting(workspace, identity, *, project_id, meeting_id, approve,
                   reason="", event_id=None):
    if not can_admin(identity):
        raise PermissionError("Chỉ Admin được duyệt kết luận và giao việc liên phòng")
    pid, meeting = _meeting(workspace, identity, project_id, meeting_id)
    if meeting["status"] != "pending_approval":
        raise ValueError("Biên bản chưa ở trạng thái chờ duyệt")
    if approve:
        action = "meeting.approved"
        data = {"meeting_id": meeting_id}
    else:
        reason = _clean_text(reason, 600, True)
        if len(reason) < 8:
            raise ValueError("Cần ghi lý do trả biên bản")
        action = "meeting.revision_requested"
        data = {"meeting_id": meeting_id, "reason": reason}
    _capacity(workspace)
    return workspace._append(identity=identity, project_id=pid, action=action,
                             data=data, event_id=event_id)


def close_meeting(workspace, identity, *, project_id, meeting_id, event_id=None):
    if not can_admin(identity):
        raise PermissionError("Chỉ Admin được đóng cuộc họp phối hợp")
    pid, meeting = _meeting(workspace, identity, project_id, meeting_id)
    if meeting["status"] != "in_progress" or not meeting["readyToClose"]:
        raise ValueError("Chưa hoàn thành và duyệt hết các đầu việc sau họp")
    _capacity(workspace)
    return workspace._append(
        identity=identity, project_id=pid, action="meeting.closed",
        data={"meeting_id": meeting_id}, event_id=event_id,
    )
