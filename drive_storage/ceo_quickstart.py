"""One-submit CEO work intake: create a signed task and propose a signed plan.

No LLM call, auto-approval or paid worker execution. All authorization remains in
SharedWorkspace; failures after creating the task are reported as partial success.
"""
from __future__ import annotations

from hashlib import sha256

from drive_storage.hierarchy import normalize_departments, suggest_departments


def create_with_optional_ceo_plan(
        workspace, identity, *, project_id, title, dept, assignee,
        agent_id, doc_code="", priority="normal", due_date="", event_id,
        auto_plan=False, selected_departments=()):
    """Create once; for an authorized CEO task, queue an auditable draft for Admin.

    A retry uses the same task event and a deterministic second event ID.
    An empty/ambiguous specialty match leaves the work item intact for manual
    selection; it NEVER dispatches an arbitrary department.
    """
    is_ceo = dept == "director" and agent_id == "CEO"
    if auto_plan and not is_ceo:
        raise ValueError("Tự lập phương án chỉ áp dụng cho nhiệm vụ CEO")
    explicit = normalize_departments(list(selected_departments)) if (
        is_ceo and auto_plan and selected_departments) else []
    departments = explicit or (suggest_departments(title, doc_code)
                               if auto_plan else [])
    task = workspace.create_task(
        identity, project_id=project_id, title=title, dept=dept,
        assignee=assignee, agent_id=agent_id, doc_code=doc_code,
        priority=priority, due_date=due_date, event_id=event_id,
    )
    result = {"task": task, "proposal": None, "departments": departments,
              "status": "created"}
    if not auto_plan:
        return result
    if not departments:
        result["status"] = "choose_departments"
        return result
    if task.get("existing"):
        state = workspace.snapshot(identity)
        if any(p.get("rootTaskId") == task["id"] and
               p.get("status") in {"pending", "dispatched"}
               for p in state.get("hierarchyPlans", [])):
            result["status"] = "already_proposed"
            return result
    proposal_id = sha256(("v752:ceo-plan:" + str(event_id)).encode("utf8")).hexdigest()[:32]
    try:
        proposal = workspace.propose_hierarchy(
            identity, project_id=project_id, task_id=task["id"],
            departments=departments,
            instructions=("Phương án sơ bộ tự lập theo tên việc và mã hồ sơ; "
                          "yêu cầu Admin kiểm tra lại bộ môn, nhân sự và phụ thuộc. "
                          + str(title)[:190]),
            event_id=proposal_id,
        )
    except (ValueError, PermissionError) as exc:
        result.update(status="proposal_requires_review", reason=str(exc))
        return result
    except Exception:
        # The signed task may already be saved; never claim the proposal is
        # persisted without being able to confirm the second Drive append.
        result.update(status="proposal_unconfirmed")
        return result
    result.update(status="pending_approval", proposal=proposal)
    return result
