"""Atomic SQL queue lifecycle, idempotency and conservative cost reservations."""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, func, create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base, AgentJob, JobEvent, utcnow

ACTIVE = {"queued", "running"}
TERMINAL = {"completed", "failed", "cancelled", "dispatch_failed"}
MAX_PENDING = 100
STILL_ALIVE_SECONDS = 90


def factory(url: str | None = None):
    url = url or os.getenv("AGENT_RUNTIME_DATABASE_URL", "")
    if not url:
        raise RuntimeError("Chưa cấu hình AGENT_RUNTIME_DATABASE_URL")
    if not url.startswith(("postgresql+", "postgresql://", "sqlite:///")):
        raise ValueError("Chỉ PostgreSQL hoặc SQLite (dùng thử) được hỗ trợ")
    if url.startswith("sqlite:///") and os.getenv("AGENT_RUNTIME_ALLOW_SQLITE") != "1":
        raise RuntimeError("Chỉ dùng SQLite trong kiểm thử; production yêu cầu PostgreSQL")
    engine = create_engine(url, pool_pre_ping=True,
                           connect_args={"check_same_thread": False} if url.startswith("sqlite:") else {})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def public(job: AgentJob) -> dict:
    def stamp(t): return t.isoformat() if t else None
    heartbeat = stamp(job.heartbeat_at)
    # Never claim a worker remains online if its last heartbeat is stale.
    live = job.state == "running" and job.heartbeat_at is not None and (
        utcnow().replace(tzinfo=None) - job.heartbeat_at.replace(tzinfo=None)
    ).total_seconds() <= STILL_ALIVE_SECONDS
    state = "unconfirmed" if job.state == "running" and not live else job.state
    return {
        "id": job.id, "projectId": job.project_id, "taskId": job.task_id,
        "agentId": job.agent_id, "mode": job.mode, "state": state,
        "phase": job.phase, "progress": job.progress, "createdAt": stamp(job.created_at),
        "startedAt": stamp(job.started_at), "heartbeatAt": heartbeat, "endedAt": stamp(job.ended_at),
        "failureCode": job.failure_code, "cancelRequested": job.cancel_requested,
        "resultEventId": job.result_event_id,
        "costReservedUsd": round(job.cost_estimate_usd, 4),
        "actualCostUsd": job.actual_cost_usd,  # null until verified provider usage
        "billingVerified": job.actual_cost_usd is not None,
        "hasHeartbeat": live,
    }


def event(s, job_id, state, code=""):
    s.add(JobEvent(job_id=job_id, state=state, note_code=code[:80]))


def enqueue(session, request, *, max_queue=MAX_PENDING, monthly_budget=10.0):
    # Callers must have signed server-to-server transport and Streamlit OAuth.
    # Queue capacity, budget and duplicate checks must see the previous
    # admission even when independent API processes receive simultaneous jobs.
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(750690)"))
    existing = session.get(AgentJob, request["job_id"])
    if existing:
        # A reused key must not submit a DIFFERENT project, actor or task.
        same = all([
            existing.project_id == request["project_id"],
            existing.task_id == request["task_id"],
            existing.actor == request["identity"]["email"],
            existing.agent_id == request["agent_id"],
            existing.mode == request["mode"],
            existing.file_id == request["file_id"],
            existing.note == request["note"],
            existing.consent == request["consent"],
        ])
        if not same:
            raise PermissionError("Mã lượt thực thi đã được dùng cho công việc khác")
        return existing, False
    busy = session.scalar(select(func.count()).select_from(AgentJob)
                          .where(AgentJob.state.in_(ACTIVE))) or 0
    if busy >= max_queue:
        raise ValueError("Hàng đợi đã đầy, cần đợi hoặc tăng số worker")
    already = session.scalar(select(func.count()).select_from(AgentJob)
                             .where(AgentJob.state.in_(ACTIVE),
                                    AgentJob.project_id == request["project_id"],
                                    AgentJob.task_id == request["task_id"],
                                    AgentJob.agent_id == request["agent_id"])) or 0
    if already:
        raise ValueError("Agent đã có phiên đang chờ/chạy trên công việc này")
    month_start = utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    reserved = session.scalar(select(func.sum(AgentJob.cost_estimate_usd)).where(
        AgentJob.created_at >= month_start,
        AgentJob.state.notin_(("cancelled", "dispatch_failed")))) or 0.0
    if reserved + request["estimated_usd"] > monthly_budget + 0.0000001:
        raise PermissionError("Vượt ngân sách ước tính API theo tháng; cần Admin cấp thêm")
    job = AgentJob(
        id=request["job_id"], project_id=request["project_id"], task_id=request["task_id"],
        agent_id=request["agent_id"], file_id=request["file_id"], actor=request["identity"]["email"],
        identity_json=json.dumps(request["identity"], ensure_ascii=False),
        mode=request["mode"], note=request["note"], consent=request["consent"],
        state="queued", cost_estimate_usd=request["estimated_usd"],
    )
    session.add(job)
    session.flush()
    event(session, job.id, "queued")
    return job, True


def claim(session, job_id):
    updated = session.execute(update(AgentJob).where(AgentJob.id == job_id,
        AgentJob.state == "queued", AgentJob.cancel_requested.is_(False)).values(
        state="running", phase="validating", started_at=utcnow(),
        heartbeat_at=utcnow(), updated_at=utcnow(), progress=2))
    if updated.rowcount != 1:
        return None
    event(session, job_id, "running")
    session.commit()
    return session.get(AgentJob, job_id)


def mark(session, job_id, state, phase="", code="", result_id=""):
    if state not in TERMINAL | {"running"}:
        raise ValueError("Trạng thái worker không hợp lệ")
    job = session.get(AgentJob, job_id)
    if not job:
        raise ValueError("Job không tồn tại")
    if job.state in TERMINAL:
        return job
    job.state = state
    job.phase = (phase or state)[:70]
    job.updated_at = utcnow()
    job.heartbeat_at = utcnow()
    if state in TERMINAL:
        job.ended_at = utcnow()
        job.progress = 100 if state == "completed" else job.progress
    job.failure_code = code[:32]
    job.result_event_id = result_id[:32]
    event(session, job_id, state, code)
    return job


def request_cancel(session, job: AgentJob):
    if job.state in TERMINAL:
        return job
    job.cancel_requested = True
    if job.state == "queued":
        return mark(session, job.id, "cancelled", "cancelled_before_start")
    event(session, job.id, "cancel_requested")
    return job
