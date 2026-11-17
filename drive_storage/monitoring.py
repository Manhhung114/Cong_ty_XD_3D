"""V6.7 monitoring projection from signed, project-scoped Drive events.

Read-only, no synthetic counts, no browser secrets, no unverified status.
The browser receives authorized, capped event metadata for near-real-time
rendering. MEP and XD are distinct systems with cross-system handoffs.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

MEP_DEPARTMENTS = frozenset({
    "electrical", "hvac", "plumbing", "fire", "bim", "qs", "qa",
})
XD_DEPARTMENTS = frozenset({
    "architecture", "structure", "xd_bim", "xd_qs", "xd_planning",
    "xd_site", "xd_safety", "xd_material",
})
SHARED_DEPARTMENTS = frozenset({"director"})
ALL_DEPARTMENTS = MEP_DEPARTMENTS | XD_DEPARTMENTS | SHARED_DEPARTMENTS

MAX_MONITOR_EVENTS = 900
MAX_MONITOR_HANDOFFS = 300
MAX_MONITOR_TASKS = 1000
MAX_MONITOR_RUNS = 300
WINDOW_DAYS = 7


def system_for(department: str) -> str:
    if department in MEP_DEPARTMENTS:
        return "mep"
    if department in XD_DEPARTMENTS:
        return "xd"
    return "shared"


def relation(source_dept: str, target_dept: str) -> str:
    a, b = system_for(source_dept), system_for(target_dept)
    if a in {"mep", "xd"} and b in {"mep", "xd"}:
        return a + "_to_" + b
    return "shared"


def _parse_time(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def build_monitor_packet(identity, snapshot: dict, signed_events: list[dict],
                         *, now: datetime | None = None) -> dict:
    """Summarize only projects in verified user's *snapshot*.

    Signed events can include other projects in a shared Drive; filtering
    must happen BEFORE building any counts or client-visible detail.
    """
    if not identity or identity.get("role") not in {"admin", "update", "read"}:
        raise PermissionError("Chưa có quyền xem bảng giám sát")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Giám sát yêu cầu thời điểm có múi giờ")
    now = now.astimezone(timezone.utc)
    window_start = now - timedelta(days=WINDOW_DAYS)
    allowed = {p["id"] for p in snapshot.get("projects", [])}
    if any(p not in allowed for p in
           (t.get("projectId") for t in snapshot.get("tasks", []))):
        raise PermissionError("Dữ liệu công việc không thuộc dự án được cấp")
    tasks = [t for t in snapshot.get("tasks", []) if t["projectId"] in allowed]
    handoffs = [h for h in snapshot.get("handoffs", [])
                if h.get("projectId") in allowed]
    runs = [a for a in snapshot.get("agentRuns", [])
            if a.get("projectId") in allowed]
    if len(tasks) > MAX_MONITOR_TASKS:
        # Never silently report incomplete "all company" operational totals.
        raise RuntimeError("Trên 1.000 nhiệm vụ; cần PostgreSQL để phân trang giám sát")
    if len(handoffs) > MAX_MONITOR_HANDOFFS:
        raise RuntimeError("Trên 300 phiếu phối hợp; cần phân trang từ máy chủ")
    task_dept = {t["id"]: t.get("dept", "") for t in tasks}
    handoff_by_id = {h["id"]: h for h in handoffs}
    doc_by_id = {d["id"]: d for d in snapshot.get("documents", [])
                 if d.get("projectId") in allowed}
    from drive_storage.company_agents import agents
    agent_dept = {key: profile["department"] for key, profile in agents().items()}
    events = []
    eligible = 0
    for raw in signed_events:
        pid = raw.get("project_id")
        if pid not in allowed:
            continue
        at = _parse_time(raw.get("at"))
        if at is None:
            raise ValueError("Sự kiện có ngày giờ không hợp lệ")
        if at > now + timedelta(minutes=5) or at < window_start:
            continue
        eligible += 1
        data = raw.get("data", {})
        action = str(raw.get("action") or "")
        agent_id = str(data.get("agent_id") or "")
        task_id = str(data.get("task_id") or "")
        source = str(data.get("source_dept") or "")
        target = str(data.get("target_dept") or "")
        if action == "handoff.resolved":
            original = handoff_by_id.get(str(data.get("handoff_id") or ""), {})
            source = original.get("sourceDept", "")
            target = original.get("targetDept", "")
        dept = (
            agent_dept.get(agent_id, "")
            or source
            or str(data.get("dept") or "")
            or task_dept.get(task_id, "")
        )
        system = system_for(dept)
        if agent_id in {"CEO", "PM", "DOC"}:
            system = "shared"
        if action.startswith("document.") and not dept:
            doc = doc_by_id.get(str(data.get("file_id") or ""), {})
            category = str(data.get("category") or doc.get("category") or "").lower()
            system = ("xd" if category.endswith("_xd") or category in
                      {"drawings_xd", "bim_xd", "boq_xd", "reports_xd"}
                      else "mep" if category.endswith("_mep") or category in
                      {"fire", "boq_mep", "drawings_mep", "bim_mep", "reports_mep"}
                      else "shared")
        # Preserve only display metadata. Reports, passwords, document bytes,
        # untrusted raw event payloads, and OAuth tokens NEVER enter the client.
        events.append({
            "id": raw["id"], "at": at.isoformat(),
            "actor": str(raw.get("actor") or "")[:254],
            "projectId": pid, "action": action,
            "agentId": agent_id[:16], "taskId": task_id[:160],
            "department": dept[:40], "system": system,
            "sourceDept": source[:40], "targetDept": target[:40],
            "relation": relation(source, target) if source and target else "",
        })
    # Retain latest events; display clearly if full 7d history is truncated.
    events.sort(key=lambda x: (x["at"], x["id"]), reverse=True)
    limited = events[:MAX_MONITOR_EVENTS]
    # KPI activity runs are inferred from completed events, not claimed live execution.
    # The runtime currently has no agent heartbeat/worker event.
    packet_handoffs = [
        {
            "id": h["id"], "projectId": h["projectId"],
            "taskId": h.get("taskId", ""),
            "sourceDept": h["sourceDept"], "targetDept": h["targetDept"],
            "relation": relation(h["sourceDept"], h["targetDept"]),
            "status": h["status"], "createdAt": h["createdAt"],
            "resolvedAt": h.get("resolvedAt", ""),
            "title": str(h.get("title") or "")[:140],
        } for h in handoffs
    ]
    packet_tasks = [{
        "id": t["id"], "projectId": t["projectId"],
        "dept": t["dept"], "system": system_for(t["dept"]),
        "status": t["status"], "dueDate": t.get("dueDate", ""),
        "reviewSince": next(
            (str(h.get("at") or "") for h in reversed(t.get("reviewHistory", []))
             if h.get("decision") == "submitted"), ""
        ) if t["status"] == "review" else "",
        "createdAt": t.get("createdAt", ""),
        "code": str(t.get("code") or "")[:30],
        "priority": t.get("priority", "normal"),
    } for t in tasks]
    return {
        "schema": "XD_MEP_MONITOR_V67",
        "readOnly": True, "authorizedProjects": len(allowed),
        "asOf": now.isoformat(), "pollSeconds": 15,
        "windowDays": WINDOW_DAYS, "events": limited,
        "eventsAvailable": eligible, "eventsTruncated": eligible > len(limited),
        "tasks": packet_tasks, "handoffs": packet_handoffs,
        "capabilities": {
            "mode": "polling_near_realtime",
            "agentRunningHeartbeat": False,
            "crossSystemHandoffs": True,
            "websocket": False,
        },
    }
