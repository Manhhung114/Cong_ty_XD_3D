"""Private HMAC-authenticated V7.1–V7.4 FastAPI control plane.

Run behind HTTPS; expose only to trusted Streamlit server, NEVER to iframe.
This service has its OWN database and does not silently replace the dormant
V5 FastAPI account database, Google OIDC or signed Drive ledger.
"""
from __future__ import annotations
import json
import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from .models import AgentJob
from .queue import factory, enqueue, public, mark, request_cancel
from .security import verify_request, validate_request, GOOGLE_ID
from .standards import query_refs, ingest_reference


class Submission(BaseModel):
    jobId: str
    projectId: str
    taskId: str
    agentId: str
    mode: str
    fileId: str = ""
    note: str = Field(default="", max_length=700)
    consent: bool = False
    identity: dict


class JobQuery(BaseModel):
    projectId: str
    identity: dict


class JobCancel(BaseModel):
    jobId: str
    projectId: str
    identity: dict


class StandardsQuery(BaseModel):
    projectId: str
    text: str = Field(min_length=2, max_length=300)
    identity: dict


class StandardsIngest(BaseModel):
    projectId: str
    identity: dict
    sourceId: str = Field(min_length=2,max_length=160)
    version: str = Field(min_length=1,max_length=100)
    title: str = Field(min_length=2,max_length=260)
    citation: str = Field(min_length=2,max_length=300)
    effectiveDate: str = Field(default="",max_length=30)
    text: str = Field(min_length=2,max_length=200000)
    copyrightPermitted: bool = False


def create_runtime_app(db_url=None, dispatcher=None):
    app = FastAPI(title="XD MEP Agent Runtime (private)", version="7.4.0",
                  docs_url=None, redoc_url=None)
    dbmaker = factory(db_url)
    app.state.dbmaker = dbmaker

    async def signed(req: Request):
        body = await req.body()
        secret = os.getenv("AGENT_RUNTIME_SECRET", "")
        if not verify_request(secret, req.headers.get("x-xd-timestamp", ""),
                              req.headers.get("x-xd-signature", ""),
                              req.method, req.url.path, body):
            raise HTTPException(401, "Chữ ký máy chủ không hợp lệ hoặc đã hết hạn")
        if len(body) > 7000:
            raise HTTPException(413, "Yêu cầu quá lớn")
        return body

    def authorized(body, *, write=True):
        identity = body.get("identity") if isinstance(body, dict) else None
        project = str(body.get("projectId", "")) if isinstance(body, dict) else ""
        if not GOOGLE_ID.fullmatch(project) or not isinstance(identity, dict):
            raise HTTPException(403, "Dự án hoặc tài khoản không hợp lệ")
        if (identity.get("role") not in {"admin", "update", "read"}
                or (write and identity.get("role") == "read")
                or (identity.get("role") != "admin"
                    and project not in identity.get("projects", [])
                    and "*" not in identity.get("projects", []))):
            raise HTTPException(403, "Ngoài phạm vi dự án")
        return identity

    @app.get("/api/runtime/health")
    def health():
        return {"version": "7.4.0", "service": "agent-runtime",
                "queueConfigured": bool(os.getenv("CELERY_BROKER_URL")),
                "oidcRevalidationOnWorker": True,
                "heartbeatSeconds": 10, "humanReviewRequired": True}

    @app.post("/api/runtime/jobs")
    async def create_job(req: Request):
        raw = await signed(req)
        try:
            payload = validate_request(json.loads(raw))
        except PermissionError as exc:
            raise HTTPException(403, str(exc))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(422, str(exc))
        if not os.getenv("CELERY_BROKER_URL"):
            raise HTTPException(503, "Chưa kết nối Redis/Celery; không tạo tác vụ giả")
        with dbmaker() as db:
            try:
                job, fresh = enqueue(
                    db, payload, max_queue=min(500, max(1, int(os.getenv("AGENT_QUEUE_MAX", "100")))),
                    monthly_budget=max(0, float(os.getenv("AGENT_MONTHLY_RESERVE_USD", "10"))))
                db.commit()
                response = public(job)
            except PermissionError as exc:
                db.rollback()
                raise HTTPException(403, str(exc))
            except ValueError as exc:
                db.rollback()
                raise HTTPException(409, str(exc))
        if fresh:
            try:
                if dispatcher is not None:
                    dispatcher(payload["job_id"])
                else:
                    from .worker import celery_app
                    celery_app.send_task("agent_runtime.execute", args=[payload["job_id"]],
                                         queue="agent_v74")
            except Exception:
                with dbmaker() as db:
                    mark(db, payload["job_id"], "dispatch_failed", "redis_unavailable", "network")
                    db.commit()
                raise HTTPException(503, "Redis không nhận tác vụ; đã ghi thất bại, không báo đang chạy")
        return response

    @app.post("/api/runtime/jobs/query")
    async def list_jobs(req: Request):
        raw = await signed(req)
        try:
            b = JobQuery.model_validate_json(raw)
            authorized(b.model_dump(),write=False)
        except Exception:
            raise HTTPException(403, "Không thể đọc tác vụ ngoài phạm vi")
        with dbmaker() as db:
            rows = db.scalars(select(AgentJob).where(
                AgentJob.project_id == b.projectId).order_by(
                AgentJob.created_at.desc()).limit(150)).all()
            return {"projectId": b.projectId, "jobs": [public(row) for row in rows]}

    @app.post("/api/runtime/jobs/cancel")
    async def cancel_job(req: Request):
        raw = await signed(req)
        try:
            b = JobCancel.model_validate_json(raw)
            authorized(b.model_dump())
        except Exception:
            raise HTTPException(403, "Không có quyền thu hồi")
        with dbmaker() as db:
            job = db.get(AgentJob, b.jobId)
            if not job or job.project_id != b.projectId:
                raise HTTPException(404, "Không có công việc trong dự án")
            if b.identity.get("role") != "admin" and job.actor != str(b.identity.get("email", "")).lower():
                raise HTTPException(403, "Chỉ người giao việc hoặc Admin được hủy")
            request_cancel(db, job)
            db.commit()
            return public(job)

    @app.post("/api/runtime/standards/search")
    async def standards(req: Request):
        raw = await signed(req)
        try:
            b = StandardsQuery.model_validate_json(raw)
            authorized(b.model_dump(),write=False)
        except Exception:
            raise HTTPException(403, "Không có quyền tra cứu")
        with dbmaker() as db:
            return {"references": query_refs(db, b.projectId, b.text),
                    "note": "Tài liệu chỉ là nguồn đối chiếu, chưa xác nhận TCVN/QCVN"}

    @app.post("/api/runtime/standards/ingest")
    async def add_standard(req: Request):
        raw = await signed(req)
        try:
            b = StandardsIngest.model_validate_json(raw)
            actor = authorized(b.model_dump())
            if actor.get("role") != "admin":
                raise PermissionError("Chỉ Admin được nhập tài liệu tham chiếu")
            if not b.copyrightPermitted:
                raise PermissionError("Chưa có quyền sử dụng văn bản nguồn")
        except Exception:
            raise HTTPException(403, "Chưa đủ quyền nhập tiêu chuẩn/tài liệu")
        with dbmaker() as db:
            doc=ingest_reference(db,project_id=b.projectId,source_id=b.sourceId,
                 version=b.version,title=b.title,citation=b.citation,
                 text=b.text,copyright_permitted=b.copyrightPermitted,
                 effective_date=b.effectiveDate)
            db.commit()
            return {"id":doc.id,"sourceId":doc.source_id,"version":doc.source_version,
                    "sha256":doc.sha256,"complianceVerified":False}

    return app


# App is initialized at start by ASGI worker, not by Streamlit.
# Absent production configuration must fail startup, rather than fall back to
# a public in-memory database that could fabricate completed jobs.
if os.getenv("AGENT_RUNTIME_DATABASE_URL"):
    app = create_runtime_app()
else:
    app = FastAPI(title="Agent Runtime (not configured)", docs_url=None)
    @app.get("/api/runtime/health")
    def _unconfigured():
        return {"version": "7.4.0", "service": "not-configured",
                "queueConfigured": False, "humanReviewRequired": True}
