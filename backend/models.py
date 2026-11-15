"""SQL schema for the V5.6/V5.7 multi-project command center."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

def utcnow(): return datetime.now(timezone.utc)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    global_role: Mapped[str] = mapped_column(String(32), default='user')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class SessionToken(Base):
    __tablename__='sessions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

class Project(Base):
    __tablename__='projects'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    client: Mapped[str] = mapped_column(String(200), default='')
    location: Mapped[str] = mapped_column(String(200), default='')
    status: Mapped[str] = mapped_column(String(35), default='active')
    start_date: Mapped[str] = mapped_column(String(20), default='')
    end_date: Mapped[str] = mapped_column(String(20), default='')
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Membership(Base):
    __tablename__='memberships'
    __table_args__=(UniqueConstraint('project_id','user_id'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(35), nullable=False)
    division: Mapped[str] = mapped_column(String(35), default='all')

class Task(Base):
    __tablename__='tasks'
    __table_args__=(UniqueConstraint('project_id','legacy_id'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    title: Mapped[str] = mapped_column(String(280), nullable=False)
    dept: Mapped[str] = mapped_column(String(80), nullable=False)
    assignee: Mapped[str] = mapped_column(String(120), default='')
    doc_code: Mapped[str] = mapped_column(String(120), default='')
    priority: Mapped[str] = mapped_column(String(30), default='normal')
    status: Mapped[str] = mapped_column(String(30), default='todo')
    creator_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    submitter_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    report: Mapped[str] = mapped_column(Text, default='')
    findings: Mapped[str] = mapped_column(Text, default='')
    review_stage: Mapped[str] = mapped_column(String(30), default='qa')
    legacy_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Approval(Base):
    __tablename__='approvals'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    stage: Mapped[str] = mapped_column(String(30), nullable=False)
    decision: Mapped[str] = mapped_column(String(35), nullable=False)
    note: Mapped[str] = mapped_column(Text, default='')
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Document(Base):
    __tablename__='documents'
    __table_args__=(UniqueConstraint('project_id','division','code','revision'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    division: Mapped[str] = mapped_column(String(30), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(140), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Audit(Base):
    __tablename__='audit_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey('projects.id'))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    action: Mapped[str] = mapped_column(String(90), nullable=False)
    target: Mapped[str] = mapped_column(String(200), nullable=False)
    details: Mapped[str] = mapped_column(Text, default='')
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AgentConfig(Base):
    __tablename__='agent_configs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default='none')
    model: Mapped[str] = mapped_column(String(100), default='')
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_budget: Mapped[int] = mapped_column(Integer, default=0)
    # No API keys in this table: keys live in server environment/secret manager.
