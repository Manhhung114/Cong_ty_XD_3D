"""Independent SQLAlchemy Agent execution state; never overwrites Drive event ledger."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow(): return datetime.now(timezone.utc)


class Base(DeclarativeBase): pass


class AgentJob(Base):
    __tablename__ = "v74_agent_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(160), index=True)
    task_id: Mapped[str] = mapped_column(String(32), index=True)
    agent_id: Mapped[str] = mapped_column(String(8), index=True)
    file_id: Mapped[str] = mapped_column(String(160), default="")
    actor: Mapped[str] = mapped_column(String(254), index=True)
    # Current access policy is re-read from Drive before worker executes.
    identity_json: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(String(700), default="")
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[str] = mapped_column(String(25), index=True, default="queued")
    phase: Mapped[str] = mapped_column(String(70), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_code: Mapped[str] = mapped_column(String(32), default="")
    result_event_id: Mapped[str] = mapped_column(String(32), default="")
    cost_estimate_usd: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


class JobEvent(Base):
    __tablename__ = "v74_agent_job_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("v74_agent_jobs.id"), index=True)
    state: Mapped[str] = mapped_column(String(25))
    note_code: Mapped[str] = mapped_column(String(80), default="")
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReferenceDocument(Base):
    __tablename__ = "v74_reference_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(160), index=True)
    source_id: Mapped[str] = mapped_column(String(160))
    source_version: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(260))
    citation: Mapped[str] = mapped_column(String(300))
    effective_date: Mapped[str] = mapped_column(String(30), default="")
    copyright_permitted: Mapped[bool] = mapped_column(Boolean, default=False)
    text_excerpt: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("project_id", "source_id", "source_version", "sha256"),)
