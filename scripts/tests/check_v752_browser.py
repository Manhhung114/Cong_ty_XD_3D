"""Browser smoke for 20-Agent task and meeting workflow (synthetic Drive only)."""
from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright

from drive_storage.company_agents import public_catalog
from scripts.build_streamlit_runtime_v2 import build


def check():
    pid = "v752-fixture-project"
    task_id = "f" * 32
    meeting_id = "a" * 32
    snapshot = {
        "enabled": True, "role": "admin", "actor": "admin@example.com",
        "selectedProjectId": pid, "meetingsAvailable": True,
        "projects": [{"id": pid, "name": "Dự án thử", "code": "V752"}],
        "agentsCatalog": public_catalog(pid), "agentRuns": [], "documents": [],
        "tasks": [{
            "id": task_id, "projectId": pid, "code": "CV-TEST", "title": "Phối hợp máng cáp và ống gió",
            "dept": "electrical", "assignedAgentId": "ELE", "assignee": "ele@example.com",
            "status": "working", "reviewHistory": [], "hierarchyStage": "",
            "hierarchyProgress": {"total": 0, "done": 0, "blockedBy": []},
        }],
        "meetings": [{
            "id": meeting_id, "projectId": pid, "title": "Họp MEP tầng 5",
            "agenda": "Đối chiếu bản vẽ máng cáp và ống gió tại tầng 5",
            "departments": ["electrical", "hvac"], "taskIds": [task_id],
            "scheduledAt": "2026-11-18T09:00:00+07:00", "status": "scheduled",
            "minutes": "", "decisions": "", "actionTaskIds": [],
            "totalActions": 0, "completedActions": 0, "readyToClose": False,
        }],
        "handoffs": [], "hierarchyPlans": [], "orgRoles": [], "events": [],
        "companyMetrics": {"projects": 1, "tasks": 1, "doing": 1, "review": 0,
                           "overdue": 0, "unassigned": 0, "highPriority": 0,
                           "documentPending": 0, "handoffsOpen": 0,
                           "departments": [], "alerts": []},
    }
    static = Path(__file__).resolve().parents[2] / "static"
    company_html = build(static, role="admin", initial_section="company",
                         cloud_snapshot=snapshot)
    tasks_html = build(static, role="admin", initial_section="tasks",
                       cloud_snapshot=snapshot)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-unsafe-swiftshader"])
        for width in (390, 820, 1440):
            page = browser.new_page(viewport={"width": width, "height": 900})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.route("https://fixture.invalid/**", lambda route: route.fulfill(
                content_type="text/html",
                body=company_html if route.request.url.endswith("/company") else tasks_html))
            page.goto("https://fixture.invalid/company")
            assert page.locator(".company-meetings").count() == 1
            assert page.get_by_text("Họp MEP tầng 5").count() >= 1
            assert page.locator('[data-company-action="meeting_create"]').count() == 1
            assert page.locator('[data-meeting-op="meeting_minutes"]').count() == 1
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), width
            page.goto("https://fixture.invalid/tasks")
            assert page.locator("[data-task-focus]").count() == 5
            assert page.locator('[data-workspace-op="meeting_create"]').count() >= 1
            page.locator('[data-task-focus="mine"]').click()
            assert page.locator(".portal-task:not([hidden])").count() == 0
            page.locator('[data-task-focus="cross"]').click()
            assert page.locator(".portal-task:not([hidden])").count() == 1
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), width
            assert not errors, errors
            page.close()
            print(f"V7.5.2 meeting/workflow {width}px PASS", flush=True)
        browser.close()


if __name__ == "__main__":
    check()
