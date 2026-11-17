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
               proposal_id: str, roles: list[dict]) -> list[dict]:
    """Build a complete, forward-referenced DAG: PM -> Lead -> Expert -> QA.

    The human role directory is signed and scoped by project. An unfilled role
    leaves assignee blank; it never grants permissions by itself.
    """
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
                "department": "qa", "agent_id": "QAC",
                "depends_on": [expert_id],
                "title": "QA/QC · Kiểm tra độc lập hồ sơ " + label,
                "assignee": role_owner(roles, "qa", "qa"),
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
    if not task.get("hierarchyStage") or identity.get("role") == "admin":
        return
    expected = str(task.get("assignee") or "").strip().casefold()
    if not expected or clean_email(identity.get("email", "")) != expected:
        raise PermissionError("Nhiệm vụ phân cấp chỉ người được giao hoặc Admin thực hiện; "
                              "cần Admin cấu hình cơ cấu nhân sự/điều chỉnh phân công")


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
