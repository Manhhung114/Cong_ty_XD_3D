"""Integration harness using the production Celery task with an in-memory Drive."""
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from test_v59_v60_cloud_workflow import (
    FakeStorage, MediaUpload, PROJECT, SIGNING_KEY,
)
from drive_storage.shared_workspace import SharedWorkspace
from agent_runtime import worker


def fixture_drive_and_identity(job):
    if job.note == "revoked":
        raise PermissionError("runtime_project_access_revoked")
    if job.note in {"cancel", "heartbeat"}:
        time.sleep(11)
    storage = FakeStorage()
    workspace = SharedWorkspace(storage, SIGNING_KEY)
    identity = json.loads(job.identity_json)
    workspace.create_task(
        identity, project_id=PROJECT, title="Fixture synthetic electrical job",
        dept="electrical", agent_id="ELE", event_id=job.task_id,
    )
    return storage, workspace, identity, SIGNING_KEY


if __name__ == "__main__":
    with (patch.object(worker, "drive_and_identity", fixture_drive_and_identity),
          patch("googleapiclient.http.MediaIoBaseUpload", MediaUpload)):
        worker.celery_app.worker_main(sys.argv[1:])
