"""Real PostgreSQL + Redis + Celery prefork acceptance with synthetic Drive.

Run against a disposable database and broker only. No provider calls are made.
"""
import concurrent.futures
from contextlib import contextmanager
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from agent_runtime.api import create_runtime_app
from agent_runtime.models import AgentJob, JobEvent
from agent_runtime.security import signature

PROJECT = "project-folder-000001"
IDENTITY = {"role": "update", "email": "fixture@example.com", "projects": [PROJECT]}
SECRET = os.environ.get("AGENT_RUNTIME_SECRET", "")


def post(http, action, data):
    path = "/api/runtime/jobs" + action
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ts = int(time.time())
    return http.post(path, content=raw, headers={
        "Content-Type": "application/json", "X-XD-Timestamp": str(ts),
        "X-XD-Signature": signature(SECRET, ts, "POST", path, raw),
    })


def payload(note=""):
    return {"jobId": uuid4().hex, "taskId": uuid4().hex, "projectId": PROJECT,
            "agentId": "ELE", "mode": "preflight", "note": note, "identity": IDENTITY}


@contextmanager
def worker(slots):
    from agent_runtime.worker import celery_app
    with tempfile.TemporaryDirectory() as folder:
        log_path = Path(folder) / "celery.log"
        with log_path.open("w+") as log:
            process = subprocess.Popen([
                sys.executable, "-m", "agent_runtime.integration.v750_worker",
                "worker", "-l", "INFO", "-Q", "agent_v74", "-c", str(slots),
                "-n", f"v750-{slots}@%h",
            ], stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 25
                while time.monotonic() < deadline and process.poll() is None:
                    if celery_app.control.ping(timeout=1):
                        break
                else:
                    raise RuntimeError(log_path.read_text()[-3500:])
                yield
            except Exception:
                print(log_path.read_text()[-4500:], file=sys.stderr)
                raise
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


def await_states(http, predicate, deadline=45):
    end = time.monotonic() + deadline
    jobs = {}
    while time.monotonic() < end:
        response = post(http, "/query", {"projectId": PROJECT, "identity": IDENTITY})
        response.raise_for_status()
        jobs = {job["id"]: job for job in response.json()["jobs"]}
        if predicate(jobs):
            return jobs
        time.sleep(.2)
    raise AssertionError(f"Không đạt trạng thái mong đợi: {[(j['state'], j['failureCode']) for j in jobs.values()]}")


def main():
    url = os.environ["AGENT_RUNTIME_DATABASE_URL"]
    assert url.startswith("postgresql"), "Campaign requires PostgreSQL"
    assert os.environ["CELERY_BROKER_URL"].startswith(("redis://", "redis+socket://"))
    assert os.environ.get("XD_V750_DISPOSABLE_RUNTIME") == "1"
    app = create_runtime_app(url)
    assert app.state.dbmaker.kw["bind"].dialect.name == "postgresql"
    with app.state.dbmaker() as db:
        assert db.scalar(select(AgentJob.id).limit(1)) is None, "Use an empty, disposable DB"
    http = TestClient(app)
    blocked = payload()
    blocked["agentId"] = "LEG"
    assert post(http, "", blocked).status_code == 403
    cancelled_before = payload()
    post(http, "", cancelled_before).raise_for_status()
    cancel = {"jobId": cancelled_before["jobId"], "projectId": PROJECT, "identity": IDENTITY}
    assert post(http, "/cancel", cancel).json()["state"] == "cancelled"
    samples = []
    for slots in (2, 4, 8, 12, 18):
        with worker(slots):
            batch = [payload() for _ in range(slots)]
            ids = {body["jobId"] for body in batch}
            started = time.monotonic()
            with concurrent.futures.ThreadPoolExecutor(max_workers=slots) as submitters:
                responses = list(submitters.map(lambda body: post(http, "", body), batch))
            for response in responses:
                response.raise_for_status()
            assert post(http, "", batch[0]).status_code == 200
            jobs = await_states(http, lambda rows: ids <= rows.keys() and
                                all(rows[key]["state"] == "completed" for key in ids))
            latency = []
            for key in ids:
                job = jobs[key]
                assert job["resultEventId"] == key and job["costReservedUsd"] == 0
                from datetime import datetime
                latency.append((datetime.fromisoformat(job["endedAt"]) -
                                datetime.fromisoformat(job["createdAt"])).total_seconds())
            with app.state.dbmaker() as db:
                done = db.scalars(select(JobEvent.job_id).where(
                    JobEvent.job_id.in_(ids), JobEvent.state == "completed")).all()
                assert set(done) == ids and len(done) == slots
            sample = {"worker_slots": slots, "completed": slots,
                      "elapsed_s": round(time.monotonic() - started, 3),
                      "median_job_latency_s": round(statistics.median(latency), 3),
                      "max_job_latency_s": round(max(latency), 3)}
            samples.append(sample)
            print(json.dumps(sample), flush=True)
            if slots == 2:
                revoked, cancelled = payload("revoked"), payload("cancel")
                post(http, "", revoked).raise_for_status()
                post(http, "", cancelled).raise_for_status()
                key = cancelled["jobId"]
                await_states(http, lambda rows: rows.get(key, {}).get("hasHeartbeat") is True)
                post(http, "/cancel", {**cancel, "jobId": key}).raise_for_status()
                results = await_states(http, lambda rows: rows[key]["state"] == "cancelled" and
                                       rows[revoked["jobId"]]["state"] == "failed")
                assert results[key]["resultEventId"] in ("", None)
                print("revocation fixture, real worker heartbeat and checkpoint cancellation passed", flush=True)
    print("PostgreSQL, Redis and Celery smoke/load campaign passed with synthetic Drive.", flush=True)


if __name__ == "__main__":
    main()
