"""Real Celery worker: Google Drive permissions rechecked before every run.

Worker cannot trust queued identity snapshots. Heartbeat is committed every
10 seconds in its own transaction. Agent output remains an unsigned-for-approval
draft inside the existing HMAC Drive journal; it never approves a task.
"""
from __future__ import annotations
import json, os, threading
from celery import Celery
from sqlalchemy import update
from .models import AgentJob, utcnow
from .queue import factory, claim, mark

BROKER = os.getenv("CELERY_BROKER_URL", "")
celery_app = Celery("xd_mep_agents", broker=BROKER or "redis://localhost:6379/1")
celery_app.conf.update(task_default_queue="agent_v74", task_acks_late=True,
    worker_prefetch_multiplier=1, task_reject_on_worker_lost=True,
    task_serializer="json", accept_content=["json"], task_time_limit=900,
    task_soft_time_limit=840, worker_max_tasks_per_child=15,
    task_publish_retry=False)


def drive_and_identity(job):
    from drive_storage.manager import from_streamlit_secrets
    from drive_storage.access_control import read_policy, clean_email, can_upload, allows_project
    from drive_storage.shared_workspace import SharedWorkspace
    secret = os.getenv("XD_AUTH_COOKIE_SECRET", "")
    if len(secret) < 32:
        raise PermissionError("runtime_identity_secret_missing")
    cfg = {key: os.getenv(env, "") for key,env in {
        "root_folder_id":"XD_DRIVE_ROOT_FOLDER_ID",
        "client_id":"XD_DRIVE_CLIENT_ID",
        "client_secret":"XD_DRIVE_CLIENT_SECRET",
        "refresh_token":"XD_DRIVE_REFRESH_TOKEN"}.items()}
    storage = from_streamlit_secrets(cfg)
    original = json.loads(job.identity_json)
    email = clean_email(original.get("email"))
    owner = clean_email(os.getenv("XD_OWNER_EMAIL", ""))
    if email == owner:
        identity = {"email":email, "role":"admin", "projects":["*"], "active":True}
    else:
        _, policy = read_policy(storage, secret)
        if not policy:
            raise PermissionError("runtime_permission_policy_missing")
        user = policy["users"].get(email)
        if not user or user.get("active") is not True:
            raise PermissionError("runtime_permission_revoked")
        identity = {"email":email, **user}
    if not can_upload(identity) or not allows_project(identity, job.project_id):
        raise PermissionError("runtime_project_access_revoked")
    return storage, SharedWorkspace(storage, secret), identity, secret


def ai_config(storage, secret, agent_id, mode):
    if mode not in {"llm","expert_llm"}:
        return {}
    from .providers import optional_config
    optional = optional_config()
    if optional:
        return {"provider":optional["provider"],"model":optional["model"],
                "api_key":"worker_env_only"}
    from drive_storage.ai_vault import read_shared
    _, cfg = read_shared(storage, secret)
    if not cfg or cfg.get("disabled"):
        raise ValueError("runtime_api_not_configured")
    return {"provider":cfg["provider"],"model":cfg.get("agent_models",{}).get(
        agent_id,cfg["model"]),"api_key":cfg["api_key"]}


def _pulse(dbmaker, job_id, stop):
    while not stop.wait(10):
        try:
            with dbmaker() as db:
                db.execute(update(AgentJob).where(AgentJob.id==job_id,
                    AgentJob.state=="running").values(
                    heartbeat_at=utcnow(),updated_at=utcnow()))
                db.commit()
        except Exception:
            # A missing heartbeat will be shown as unconfirmed.
            pass


def _stage(dbmaker, job_id, name, progress):
    with dbmaker() as db:
        job=db.get(AgentJob,job_id)
        if not job or job.state!="running":
            raise RuntimeError("runtime_claim_lost")
        if job.cancel_requested:
            raise InterruptedError("runtime_cancel_requested")
        job.phase=name[:70];job.progress=min(95,max(1,progress))
        job.heartbeat_at=utcnow();job.updated_at=utcnow();db.commit()


@celery_app.task(name="agent_runtime.execute", bind=True, max_retries=0)
def execute(self, job_id):
    from drive_storage.live_agents import safe_failure_code
    if not BROKER or not os.getenv("AGENT_RUNTIME_DATABASE_URL"):
        raise RuntimeError("Celery/PostgreSQL chưa được cấu hình")
    maker=factory()
    with maker() as db:
        job=claim(db,job_id)
        if job is None:
            return {"state":"not_claimed"}
    stop=threading.Event()
    pulse=threading.Thread(target=_pulse,args=(maker,job_id,stop),daemon=True)
    pulse.start()
    workspace=None;identity=None;started=False
    try:
        storage,workspace,identity,secret=drive_and_identity(job)
        _stage(maker,job_id,"role_verified",10)
        snapshot=workspace.snapshot(identity)
        task=next((t for t in snapshot["tasks"] if t["id"]==job.task_id
                   and t["projectId"]==job.project_id),None)
        from drive_storage.company_agents import _task_context
        from drive_storage.hierarchy import require_operator, dependencies_block
        if task is None or task["status"] in {"review","done","cancelled"}:
            raise PermissionError("runtime_task_closed_or_missing")
        _task_context(snapshot,job.project_id,job.task_id,job.agent_id)
        require_operator(identity,task)
        if dependencies_block(task,snapshot["tasks"]):
            raise PermissionError("runtime_predecessors_not_approved")
        _stage(maker,job_id,"input_verified",25)
        existing=workspace.record_agent_start(identity,project_id=job.project_id,
            task_id=job.task_id,agent_id=job.agent_id,mode=job.mode,attempt_id=job.id)
        if existing.get("completed"):
            with maker() as db:
                mark(db,job.id,"completed","already_signed_draft",result_id=job.id);db.commit()
            return {"state":"completed","existing":True}
        if existing.get("existing"):
            # Never repeat an in-flight or previously charged API call.
            raise RuntimeError("runtime_attempt_previously_started")
        started=True
        _stage(maker,job_id,"reading_and_analyzing",45)
        config=ai_config(storage,secret,job.agent_id,job.mode)
        from .standards import query_refs
        with maker() as refdb:
            refs=query_refs(refdb,job.project_id,task["title"],limit=3)
        citations="; ".join(r["citation"]+" ["+r["version"]+"]" for r in refs)
        note=(job.note+(" | Tham khảo chưa xác minh: "+citations if citations else ""))[:700]
        kw={"project_id":job.project_id,"task_id":job.task_id,"agent_id":job.agent_id,
            "mode":job.mode,"note":note,"consent":job.consent,
            "ai_config":config,"event_id":job.id}
        if job.mode in {"expert","expert_llm"}:
            from drive_storage.expert_orchestrator import run_expert
            result=run_expert(workspace,identity,file_id=job.file_id,**kw)
        else:
            from drive_storage.company_agents import run_agent
            result=run_agent(workspace,identity,**kw)
        from .graph import next_review
        gate=next_review({"task_id":job.task_id,"qa_decision":"pending"},
                         use_langgraph=True)
        if gate["next_action"]!="human_qa_review":
            raise RuntimeError("Không thể xác minh cổng kiểm duyệt")
        _stage(maker,job_id,"signed_draft_saved",95)
        with maker() as db:
            mark(db,job.id,"completed","human_review_required",
                 result_id=str(result.get("eventId") or ""))
            db.commit()
        return {"state":"completed","humanReviewRequired":True}
    except Exception as exc:
        code="cancelled" if isinstance(exc,InterruptedError) else safe_failure_code(exc)
        if started and workspace is not None:
            try:
                workspace.record_agent_failure(identity,project_id=job.project_id,
                    task_id=job.task_id,agent_id=job.agent_id,mode=job.mode,
                    attempt_id=job.id,code=code if code!="cancelled" else "internal")
            except Exception:
                pass
        with maker() as db:
            mark(db,job.id,"cancelled" if code=="cancelled" else "failed",
                 "stopped_or_failed",code=code)
            db.commit()
        return {"state":"cancelled" if code=="cancelled" else "failed","failureCode":code}
    finally:
        stop.set();pulse.join(timeout=2)
