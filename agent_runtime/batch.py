"""Admin-approved optional batch preflight for V6.9 hierarchy.

This starts ONLY free deterministic checklist tasks with signed dispatch.
It never auto-sends project data to an LLM, never executes QA before its
approved prerequisites, and never auto-approves a task.
"""
from __future__ import annotations
import hashlib
from drive_storage.hierarchy import dependencies_block
from drive_storage.access_control import can_admin


def scheduled_id(plan_id, task_id):
    return hashlib.sha256(
        ("XD_V74_PREFLIGHT:"+plan_id+":"+task_id).encode()).hexdigest()[:32]


def batch_preflight(client, workspace, identity, *, project_id, proposal_id):
    if not can_admin(identity):
        raise PermissionError("Chỉ Admin được kích hoạt hàng đợi đồng loạt")
    state=workspace.snapshot(identity)
    plan=next((p for p in state.get("hierarchyPlans",[])
               if p["id"]==proposal_id and p["projectId"]==project_id),None)
    if not plan or plan["status"]!="dispatched":
        raise ValueError("Phương án chưa được phê duyệt")
    nodes=[t for t in state["tasks"] if t.get("delegationPlanId")==proposal_id
           and t.get("hierarchyStage") not in {"ceo","qa"}
           and t["projectId"]==project_id and t["status"]=="todo"
           and t.get("assignedAgentId")]
    success=[];failed=[];skipped=[]
    for task in nodes:
        if dependencies_block(task,state["tasks"]):
            skipped.append(task["code"])
            continue
        try:
            result=client.send("/api/runtime/jobs",{
                "jobId":scheduled_id(proposal_id,task["id"]),
                "projectId":project_id,"taskId":task["id"],
                "agentId":task["assignedAgentId"],"mode":"preflight",
                "fileId":"","note":"Checklist phân tuyến có nguồn, chưa duyệt kỹ thuật",
                "consent":False,"identity":identity,
            })
            success.append({"code":task["code"],"jobId":result["id"]})
        except Exception:
            # Group approval is already signed in Drive. Never hide partial
            # enqueue failures or assert all Agents started.
            failed.append(task["code"])
    return {"queued":success,"failed":failed,"blockedByDependency":skipped}
