"""V6.6 user-triggered specialist → DOC → QAC → PM review pipeline.

No invisible agent actions, no automatic approvals. A single bounded signed
agent.completed event records document hash, actual parser findings and
independent quality gates; a human engineer remains accountable.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from pathlib import PurePath

from drive_storage.access_control import can_upload
from drive_storage.company_agents import (
    agents, _task_context, preflight, call_provider, _quota_check,
)
from drive_storage.expert_tools import extract_registered, concise_evidence
from drive_storage.expert_rules import analyze
from drive_storage.v75_registers import IFC_AGENTS, compare_inventory
from drive_storage.shared_workspace import _require_id, _clean_text

MAX_RENDERED_RESULT = 4200


def _check_steps(parsed, review, task, doc, profile):
    findings = review["findings"]
    problems = sum(f["level"] in {"mismatch", "invalid_input"} for f in findings)
    computed = sum(f["level"] == "calculated" for f in findings)
    sources = sum(bool(f["sources"]) for f in findings)
    stages = [
        {"expert": profile["id"], "role": "Bộ môn chuyên gia", "status": "analyzed",
         "detail": f"Đã dùng bộ đọc {parsed['type']} và xét {len(findings)} phát hiện",
         "evidence": sources},
        {"expert": "DOC", "role": "Kiểm soát hồ sơ", "status": "review_required",
         "detail": "Mã: " + str(doc["code"]) + " · revision " + str(doc.get("revision") or "?") +
                  " · trạng thái " + str(doc.get("status", "chưa rõ")),
         "evidence": 1},
        {"expert": "QAC", "role": "Kiểm soát chất lượng", "status": "review_required",
         "detail": f"{problems} sai khác số học/dữ liệu; {computed} phép tính công thức; "
                   "chưa đánh giá tiêu chuẩn áp dụng",
         "evidence": sources},
        {"expert": "PM", "role": "Điều phối & giao người thẩm tra", "status": "awaiting_engineer",
         "detail": "Chuyển người phụ trách: " + str(task.get("assignee") or "CHƯA PHÂN CÔNG") +
                   "; không thay đổi trạng thái nhiệm vụ/hồ sơ",
         "evidence": 1},
    ]
    return stages


def _pretty(profile, task, parsed, analysis, steps):
    lines = [
        "V6.6 · QUY TRÌNH CHUYÊN GIA CÓ BẰNG CHỨNG THẬT",
        f"Chuyên gia: {profile['title']} | Công việc: {task['title']}",
        "Tệp: " + parsed["provenance"]["filename"],
        "Bằng chứng: Drive file " + parsed["provenance"]["fileId"] +
            " | SHA-256 " + parsed["provenance"]["sha256"],
        f"Đã đọc mẫu {parsed['recordCount']} nguồn ({parsed['type']}).",
        "V6.5 · PHÁT HIỆN KIỂM TRA CÓ CÔNG THỨC:",
    ]
    for f in analysis["findings"][:8]:
        values = json.dumps(f["values"], ensure_ascii=False, separators=(",", ":"))
        lines.append(f"- [{f['level']}] {f['rule']}: {f['message']}")
        lines.append("  Nguồn: " + ", ".join(f["sources"][:3]))
        if values != "{}":
            lines.append("  Giá trị: " + values[:280])
    lines.append("V6.6 · HÀNG KIỂM SOÁT ĐỘC LẬP:")
    for s in steps:
        lines.append(f"- {s['expert']}: {s['detail']}")
    lines.extend([
        "TRẠNG THÁI: CẦN KỸ SƯ KIỂM CHỨNG; chưa được phê duyệt.",
        "Không chứng nhận tuân thủ TCVN/QCVN, tính toán thiết kế hoàn chỉnh hoặc clash geometry.",
    ])
    return "\n".join(lines)[:MAX_RENDERED_RESULT]


def _ifc_pair(documents, baseline_id, current, profile, mode):
    if mode != "expert" or not profile.get("skill_version") or profile["id"] not in IFC_AGENTS:
        raise PermissionError("Đối chiếu phiên bản chỉ chạy nội bộ bằng BIM/XBI V7.5")
    baseline = next((doc for doc in documents if doc["id"] == baseline_id
                     and doc["projectId"] == current["projectId"]), None)
    if (baseline is None or baseline_id == current["id"]
            or baseline["category"] != current["category"]
            or baseline["code"].casefold() != current["code"].casefold()
            or any(doc.get("status") != "approved"
                   or PurePath(doc["filename"]).suffix.casefold() != ".ifc"
                   for doc in (baseline, current))):
        raise PermissionError("Cần hai tệp IFC đã duyệt, cùng mã hồ sơ và nhóm tài liệu trong dự án")
    versions = [doc.get("revision", "") for doc in (baseline, current)]
    if (any(not re.fullmatch(r"R[0-9]{2,4}", version) for version in versions)
            or int(versions[0][1:]) >= int(versions[1][1:])):
        raise ValueError("Phiên bản IFC gốc phải có số revision nhỏ hơn bản hiện tại")
    return baseline


def _source_evidence(doc, parsed):
    return {"code": doc["code"], "revision": doc.get("revision", ""),
            "status": doc.get("status", ""), "fileId": doc["id"],
            "sha256": parsed["hashes"]["sha256"]}


def run_expert(workspace, identity, *, project_id, task_id, agent_id,
               file_id, mode="expert", note="", consent=False,
               ai_config=None, event_id=None, opener=None, baseline_file_id=""):
    if not can_upload(identity):
        raise PermissionError("Tài khoản Chỉ đọc không được chạy chuyên gia")
    if mode not in {"expert", "expert_llm"}:
        raise ValueError("Chế độ chuyên gia không hợp lệ")
    pid = workspace._check_project(identity, project_id, True)
    _require_id(task_id, "Công việc")
    fid = _require_id(file_id, "Tệp kỹ thuật")
    baseline_id = _require_id(baseline_file_id, "Tệp IFC gốc") if baseline_file_id else ""
    if event_id:
        if not re.fullmatch(r"[0-9a-f]{32}", str(event_id)):
            raise ValueError("Mã lượt thực thi chuyên gia không hợp lệ")
        # Deduplicate before touching a paid model or reading the file.
        for prior in workspace.events():
            if prior["id"] != event_id:
                continue
            old = prior.get("data", {})
            if (prior["action"] != "agent.completed" or prior["project_id"] != pid
                    or prior["actor"] != identity["email"]
                    or old.get("task_id") != task_id
                    or old.get("agent_id") != agent_id or old.get("mode") != mode
                    or old.get("file_id") != fid or (old.get("baseline_file_id") or "") != baseline_id):
                raise PermissionError("Mã giao dịch đã được dùng cho thao tác khác")
            return {"eventId": event_id, "existing": True, "draft": old.get("result", ""),
                    "stages": old.get("workflowStages", []),
                    "evidence": old.get("expertEvidence", {}),
                    "reviewRequired": True}
    state = workspace.snapshot(identity)
    profile, task, project, docs = _task_context(state, pid, task_id, agent_id)
    from drive_storage.hierarchy import require_operator, require_qc_role, dependencies_block
    require_operator(identity, task)
    require_qc_role(identity, task, state)
    if agent_id == "QCX" and (mode != "expert" or fid not in {doc["id"] for doc in docs}):
        raise PermissionError("QCX chỉ đọc hồ sơ đã duyệt gắn với nhiệm vụ, không gửi ra AI ngoài")
    if dependencies_block(task, state["tasks"]):
        raise PermissionError("Chưa thể chạy Agent: nhiệm vụ trước trong luồng phân cấp chưa được duyệt")
    registered = next((d for d in state["documents"]
                       if d["id"] == fid and d["projectId"] == pid), None)
    if registered is None:
        raise PermissionError("Tệp chưa ghi sổ trong dự án")
    if registered["category"] not in profile.get("expected_categories", []):
        if agent_id not in {"CEO", "PM", "DOC", "QAC"}:
            raise PermissionError("File không đúng loại bằng chứng chuyên môn của Agent")
    baseline = _ifc_pair(state["documents"], baseline_id, registered, profile, mode) if baseline_id else None
    note = _clean_text(note, 700)
    parsed = extract_registered(workspace, identity, project_id=pid, file_id=fid)
    findings = analyze(agent_id, parsed, registered, v75=bool(profile.get("skill_version")))
    sources = [_source_evidence(registered, parsed)]
    older = None
    if baseline:
        older = extract_registered(workspace, identity, project_id=pid, file_id=baseline_id)
        if older["type"] != "ifc" or parsed["type"] != "ifc":
            raise ValueError("Đối chiếu yêu cầu hai tệp IFC")
        sources.append(_source_evidence(baseline, older))
        findings["findings"] = [*compare_inventory(older, parsed), *findings["findings"]][:20]
    stages = _check_steps(parsed, findings, task, registered, profile)
    body = _pretty(profile, task, parsed, findings, stages)
    if baseline:
        body = ("IFC gốc · " + baseline["revision"] + " · SHA-256 " +
                older["hashes"]["sha256"] + "\n" + body)[:MAX_RENDERED_RESULT]
    vendor = "none"
    if mode == "expert_llm":
        if not consent:
            raise PermissionError("Cần đồng ý gửi trích xuất dữ liệu kỹ thuật cho nhà cung cấp AI")
        _quota_check(state, identity)
        snippets = [
            {"source": r["source"], "text": r["text"][:160]}
            for r in parsed["records"][:25]
        ]
        context = {
            "fileEvidence": {
                "type": parsed["type"], "file": parsed["provenance"]["filename"],
                "sha256": parsed["provenance"]["sha256"], "sample": snippets,
                "warnings": parsed["warnings"][:5],
            },
            "engineeringFindings": findings["findings"][:8],
            "standardsStatus": "not_assessed",
            "task": {"title": task["title"], "dept": task["dept"]},
            "userInstruction": note,
        }
        vendor, llm_text = call_provider(ai_config or {}, profile, context, opener=opener)
        body = (body[:2400] + "\n\nDỰ THẢO AI TRÊN TRÍCH XUẤT CÓ NGUỒN (CHƯA THẨM TRA):\n"
                + llm_text[:1700])[:MAX_RENDERED_RESULT]
    evidence = concise_evidence(parsed)
    if baseline:
        evidence["baseline"] = concise_evidence(older)
    # One signed event for the full pipeline; no tools can approve/publish files.
    data = {
        "task_id": task_id, "agent_id": agent_id,
        "attempt_id": str(event_id or ""),
        "file_id": fid, "mode": mode, "provider": vendor,
        **({"baseline_file_id": baseline_id} if baseline_id else {}),
        "model": str((ai_config or {}).get("model") or "")[:90] if mode == "expert_llm" else "",
        "result": body, "workflowStages": stages,
        "expertEvidence": evidence,
        "evidence": sources,
        "missing": findings["warnings"][:5],
        "risks": [f["message"][:200] for f in findings["findings"]
                  if f["level"] in {"mismatch", "invalid_input"}][:8],
        "reviewRequired": True, "qualityGate": "human_review_required",
        "standardCheck": "not_assessed", "note": note,
    }
    # Never make the signed ledger reject a valid file due to unbounded detail.
    for stage in data["workflowStages"]:
        stage["detail"] = stage["detail"][:240]
    if len(json.dumps(data, ensure_ascii=False).encode("utf8")) > 16_000:
        raise ValueError("Báo cáo quá lớn, cần xuất chứng cứ qua worker")
    result = workspace._append(
        identity=identity, project_id=pid, action="agent.completed",
        data=data, event_id=event_id,
    )
    return {
        "eventId": result["id"], "existing": result["existing"],
        "draft": body, "stages": stages, "evidence": evidence,
        "reviewRequired": True,
    }
