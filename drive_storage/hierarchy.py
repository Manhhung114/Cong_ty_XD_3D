"""V6.9: deterministic, auditable CEO -> PM -> Lead -> Expert -> QA routing.

The CEO Agent proposes a *plan*, never signs an approval or silently invokes
other AI providers. An authenticated Admin must approve dispatch. Each created
task is a signed child with a stage, owner, dependencies and immutable parent.
AI runs continue to require an explicit user action and human validation.
"""
from __future__ import annotations

import hashlib
import re
from drive_storage.access_control import clean_email
from drive_storage.v75_rollout import LEGACY_POLICY, QA_POLICY

MAX_DEPARTMENTS = 4
ORG_ROLES = {"director", "pm", "lead", "engineer", "qa", "none"}
STAGES = {"ceo", "pm", "lead", "expert", "qa"}

DEPT_LABELS = {
    "electrical": "Điện", "hvac": "HVAC", "plumbing": "Cấp thoát nước",
    "fire": "PCCC", "bim": "BIM MEP", "qs": "Dự toán MEP",
    "architecture": "Kiến trúc", "structure": "Kết cấu",
    "xd_bim": "BIM xây dựng", "xd_qs": "Dự toán XD",
    "xd_planning": "Kế hoạch", "xd_site": "Thi công",
    "xd_safety": "An toàn", "xd_material": "Vật tư",
}
KEYWORDS = {
    "electrical": ("điện", "tủ điện", "cáp", "mccb", "electrical", "transformer"),
    "hvac": ("hvac", "điều hòa", "thông gió", "chiller"),
    "plumbing": ("cấp nước", "thoát nước", "bơm nước", "plumbing"),
    "fire": ("pccc", "chữa cháy", "báo cháy", "sprinkler"),
    "bim": ("bim mep", "ifc mep"),
    "qs": ("boq mep", "khối lượng mep", "dự toán mep"),
    "architecture": ("kiến trúc", "architecture"),
    "structure": ("kết cấu", "cột", "dầm", "móng"),
    "xd_bim": ("bim xây dựng", "bim xd"),
    "xd_qs": ("boq xây dựng", "dự toán xây dựng"),
    "xd_planning": ("tiến độ", "kế hoạch", "schedule"),
    "xd_site": ("hiện trường", "thi công", "nghiệm thu"),
    "xd_safety": ("an toàn", "hse"),
    "xd_material": ("vật tư", "material"),
}


def specialist_agents() -> dict[str, str]:
    from drive_storage.company_agents import agents
    return {agent["department"]: agent["id"]
            for agent in agents().values()
            if agent["department"] in DEPT_LABELS and agent["id"] not in {"DOC", "QAC"}}


def normalize_departments(departments) -> list[str]:
    if not isinstance(departments, (list, tuple)):
        raise ValueError("Phải chọn nhóm bộ môn rõ ràng")
    valid = specialist_agents()
    unique = list(dict.fromkeys(departments))
    if (not 1 <= len(unique) <= MAX_DEPARTMENTS
            or len(unique) != len(departments)
            or any(not isinstance(d, str) or d not in valid for d in unique)):
        raise ValueError("Chỉ chọn 1–4 bộ môn chuyên ngành hợp lệ, không trùng")
    return unique


def suggest_departments(title: str, doc_code: str = "") -> list[str]:
    """Deterministic hints only. Empty means no evidence to route automatically."""
    content = (str(title) + " " + str(doc_code)).casefold()
    return [name for name, keywords in KEYWORDS.items()
            if any(word in content for word in keywords)][:MAX_DEPARTMENTS]


def deterministic_id(dispatch_id: str, node_key: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{32}", dispatch_id):
        raise ValueError("ID phân phối không hợp lệ")
    return hashlib.sha256(("XD_MEP_V690:" + dispatch_id + ":" + node_key)
                          .encode("utf-8")).hexdigest()[:32]


def role_owner(roles: list[dict], role: str, department: str) -> str:
    candidates = sorted(row["email"] for row in roles
                        if row.get("role") == role and
                        row.get("department") == department and row.get("active", True))
    return candidates[0] if candidates else ""


def plan_tasks(*, root: dict, departments: list[str], dispatch_id: str,
               proposal_id: str, roles: list[dict], policy_version=LEGACY_POLICY) -> list[dict]:
    """Build a complete, forward-referenced DAG: PM -> Lead -> Expert -> QA.

    The human role directory is signed and scoped by project. An unfilled role
    leaves assignee blank; it never grants permissions by itself.
    """
    if policy_version not in {LEGACY_POLICY, QA_POLICY}:
        raise ValueError("Phiên bản phân phối không hợp lệ")
    normalized = normalize_departments(departments)
    agents = specialist_agents()
    project_id = root["projectId"]
    template = {
        "project_id": project_id, "root_task_id": root["id"],
        "proposal_id": proposal_id, "doc_code": root.get("docCode", ""),
        "due_date": root.get("dueDate", ""), "priority": root.get("priority", "normal"),
    }
    nodes = []
    pm_id = deterministic_id(dispatch_id, "pm")
    nodes.append({
        **template, "id": pm_id, "parent_id": root["id"], "stage": "pm",
        "department": "director", "agent_id": "PM", "depends_on": [],
        "title": "PM · Điều phối và tổng hợp — " + root["title"][:150],
        "assignee": role_owner(roles, "pm", "director"),
    })
    for dept in normalized:
        label, expert = DEPT_LABELS[dept], agents[dept]
        lead_id = deterministic_id(dispatch_id, "lead_" + dept)
        expert_id = deterministic_id(dispatch_id, "expert_" + dept)
        qa_id = deterministic_id(dispatch_id, "qa_" + dept)
        construction = policy_version == QA_POLICY and (dept.startswith("xd_")
                                                        or dept in {"architecture", "structure"})
        qa_dept, qa_agent = ("xd_qc", "QCX") if construction else ("qa", "QAC")
        qc_owner = role_owner(roles, "qa", qa_dept)
        if construction and (not qc_owner or qc_owner in {
                role_owner(roles, "engineer", dept), role_owner(roles, "lead", dept),
                role_owner(roles, "engineer", "xd_safety"),
                role_owner(roles, "lead", "xd_safety"),
                str(root.get("assignee") or "").casefold()}):
            raise PermissionError("Cần phân công nhân sự QA/QC xây dựng độc lập")
        nodes.extend([
            {
                **template, "id": lead_id, "parent_id": pm_id, "stage": "lead",
                "department": dept, "agent_id": expert, "depends_on": [],
                "title": "Trưởng bộ môn " + label + " · Phân phối & kiểm tra",
                "assignee": role_owner(roles, "lead", dept),
            },
            {
                **template, "id": expert_id, "parent_id": lead_id, "stage": "expert",
                "department": dept, "agent_id": expert, "depends_on": [],
                "title": "Chuyên gia " + label + " · Phân tích hồ sơ và lập báo cáo",
                "assignee": role_owner(roles, "engineer", dept),
            },
            {
                **template, "id": qa_id, "parent_id": lead_id, "stage": "qa",
                "department": qa_dept, "agent_id": qa_agent,
                "depends_on": [expert_id],
                "title": "QA/QC · Kiểm tra độc lập hồ sơ " + label,
                "assignee": qc_owner,
            },
        ])
    return nodes


def dependencies_block(task: dict, tasks: list[dict]) -> list[str]:
    """A task cannot execute until explicit predecessor tasks are approved."""
    by_id = {t["id"]: t for t in tasks}
    ids = task.get("dependsOn", [])
    return [node_id for node_id in ids
            if node_id not in by_id or by_id[node_id]["status"] != "done"]


def unfinished_children(task: dict, tasks: list[dict]) -> list[dict]:
    return [item for item in tasks if item.get("parentTaskId") == task["id"]
            and item.get("status") != "done"]


def require_operator(identity: dict, task: dict, operation: str = "run"):
    if task.get("dept") == "xd_qc":
        from drive_storage.v75_rollout import qcx_enabled
        if not qcx_enabled(task["projectId"]):
            raise PermissionError("QCX hiện tạm dừng cho dự án này")
    if not task.get("hierarchyStage") or (identity.get("role") == "admin" and task.get("dept") != "xd_qc"):
        return
    expected = str(task.get("assignee") or "").strip().casefold()
    if not expected or clean_email(identity.get("email", "")) != expected:
        raise PermissionError("Nhiệm vụ phân cấp chỉ người được giao hoặc Admin thực hiện; "
                              "cần Admin cấu hình cơ cấu nhân sự/điều chỉnh phân công")


def require_qc_role(identity, task, state):
    if task.get("dept") != "xd_qc":
        return
    actor = clean_email(identity.get("email", ""))
    if not any(row.get("email") == actor and row.get("projectId") == task["projectId"]
               and row.get("department") == "xd_qc" and row.get("role") == "qa"
               and row.get("active") for row in state.get("orgRoles", [])):
        raise PermissionError("Quyền QA/QC xây dựng của người phụ trách không còn hiệu lực")
    predecessors = set(task.get("dependsOn", []))
    for row in state.get("tasks", []):
        if row["id"] in predecessors and actor in {
                str(row.get("assignee") or "").casefold(),
                str(row.get("lastSubmittedBy") or "").casefold()}:
            raise PermissionError("Người đã thực hiện hồ sơ không được kiểm tra QCX độc lập")


def describe_progress(task: dict, tasks: list[dict]) -> dict:
    children = [t for t in tasks if t.get("parentTaskId") == task["id"]]
    finished = sum(t["status"] == "done" for t in children)
    return {
        "total": len(children), "done": finished,
        "ready": not dependencies_block(task, tasks),
        "blockedBy": dependencies_block(task, tasks),
        "allChildrenDone": bool(children) and finished == len(children),
    }


def can_review_node(identity: dict, task: dict, tasks: list[dict]) -> bool:
    """Hierarchical manager may review own direct subordinate only.

    Root and independent QA still require Admin. An operator cannot approve
    their own assigned work, even if they also hold a manager position.
    """
    if task.get("hierarchyPolicyVersion") == QA_POLICY:
        actor = clean_email(identity.get("email", ""))
        if actor in {str(task.get(field) or "").casefold()
                     for field in ("assignee", "lastSubmittedBy")}:
            return False
    if identity.get("role") == "admin":
        return True
    if identity.get("role") != "update":
        return False
    parent_id = task.get("parentTaskId")
    if not parent_id or task.get("hierarchyStage") == "qa":
        return False
    parent = next((x for x in tasks if x["id"] == parent_id), None)
    expected = str(parent.get("assignee") or "").lower() if parent else ""
    assignee = str(task.get("assignee") or "").lower()
    actor = clean_email(identity.get("email", ""))
    return bool(expected and expected == actor and assignee != actor)
