"""V7.0 server-only projection of signed Agent execution *attempts*.

An agent.started event means an authenticated execution was entered, not proof
a worker remains alive. There is NO durable heartbeat yet: after 120 seconds
an unfinished attempt becomes unconfirmed, never "running" indefinitely.
The browser gets only allowlisted project metadata and short status codes.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

ATTEMPT = re.compile(r"^[0-9a-f]{32}$")
LIVE_WINDOW_SECONDS = 120
MAX_PUBLIC_AGENTS = 100
ERROR_CODES = frozenset({
    "provider", "quota", "network", "drive", "validation",
    "permission", "resource", "internal",
})


def execution_event_id(attempt_id: str, phase: str) -> str:
    if not ATTEMPT.fullmatch(str(attempt_id)) or phase not in {"started", "failed"}:
        raise ValueError("Mã phiên Agent không hợp lệ")
    return hashlib.sha256(("XD_MEP_V700:" + attempt_id + ":" + phase).encode()).hexdigest()[:32]


def safe_failure_code(exc: BaseException) -> str:
    # Never forward raw exception messages, provider payloads, URL, file path
    # or API key to the shared activity UI.
    from urllib.error import HTTPError, URLError
    if isinstance(exc, PermissionError):
        return "permission"
    if isinstance(exc, ValueError):
        return "validation"
    if isinstance(exc, (HTTPError,)):
        return "provider"
    if isinstance(exc, (URLError, TimeoutError, ConnectionError)):
        return "network"
    message = str(exc).lower()
    if "429" in message or "hạn mức" in message or "giới hạn lượt" in message:
        return "quota"
    if any(p in message for p in ("google drive", "drive", "checksum", "file")):
        return "drive"
    if any(p in message for p in ("memory", "worker", "quá lớn")):
        return "resource"
    return "internal"


def _time(value: str):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, AttributeError, OverflowError):
        return None


def project_agent_activity(snapshot: dict, signed_events: list[dict], *,
                           now: datetime | None = None) -> list[dict]:
    """Return last verifiable status for each (project,Agent), never mock runs."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Cần thời gian UTC có múi giờ")
    now = now.astimezone(timezone.utc)
    allowed = {x["id"] for x in snapshot.get("projects", [])}
    task_by_id = {t["id"]: t for t in snapshot.get("tasks", [])
                  if t["projectId"] in allowed}
    events = []
    for event in signed_events:
        if event.get("project_id") not in allowed:
            continue
        action = event.get("action")
        if action not in {"agent.started", "agent.failed", "agent.completed"}:
            continue
        data = event.get("data") or {}
        task_id = str(data.get("task_id") or "")
        task = task_by_id.get(task_id)
        if not task or task["projectId"] != event["project_id"]:
            continue
        agent = str(data.get("agent_id") or "")[:16]
        when = _time(event.get("at"))
        if not when or when > now:
            continue
        events.append((when, event["id"], action, event, task, agent))
    events.sort(key=lambda r:(r[0],r[1]))
    latest_by_agent = {}
    # Later failure/completion of the same attempt supersedes start.
    # Legacy completion events lacking attempt_id are still valid evidence.
    for when,eid,action,event,task,agent in events:
        data=event.get("data") or {}
        attempt=str(data.get("attempt_id") or eid)
        key=(task["projectId"],agent)
        if action=="agent.started":
            state="started"
        elif action=="agent.failed":
            state="failed"
        else:
            state="completed"
        age=max(0,(now-when).total_seconds())
        if state=="started":
            state="started_unconfirmed" if age<=LIVE_WINDOW_SECONDS else "stale"
        record={
            "projectId":task["projectId"],
            "agentId":agent,
            "taskId":task["id"],
            "taskCode":str(task.get("code") or "")[:30],
            "taskTitle":str(task.get("title") or "")[:160],
            "department":str(task.get("dept") or "")[:40],
            "attemptId":attempt if ATTEMPT.fullmatch(attempt) else "",
            "state":state,"at":when.isoformat(),"elapsedSeconds":int(age),
            "mode":str(data.get("mode") or "")[:20],
            "failureCode":(str(data.get("code") or "internal")[:20]
                            if action=="agent.failed" else ""),
            "hasHeartbeat":False,
            "evidence":action,
        }
        # Compare only latest event per Agent, never mark a task started due
        # to a mere assigned/working state.
        latest_by_agent[key] = record
    # Keep only latest 100 states for bounded Streamlit iframe payload.
    return sorted(latest_by_agent.values(),key=lambda x:x["at"],reverse=True)[:MAX_PUBLIC_AGENTS]
