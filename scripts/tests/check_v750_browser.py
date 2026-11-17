"""Exercise the deployed Streamlit bundle with a synthetic authenticated snapshot."""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from drive_storage.company_agents import public_catalog
from scripts.build_streamlit_runtime_v2 import build


def check():
    project = "v750-fixture-project"
    os.environ.update(XD_V75_CATALOG="1", XD_V75_CANARY_PROJECTS=project)
    snapshot = {
        "enabled": True, "role": "admin", "selectedProjectId": project,
        "projects": [{"id": project, "code": "FIXTURE", "name": "Test"}],
        "agentsCatalog": public_catalog(project), "runtimeJobs": [],
    }
    public_path = Path(__file__).resolve().parents[2] / "static"
    hub = build(public_path, role="admin", initial_section="agents", cloud_snapshot=snapshot)
    office = build(public_path, role="admin", initial_section="overview", cloud_snapshot=snapshot)
    with sync_playwright() as playwright:
        args = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
        options = {"executable_path": os.environ["CHROMIUM_BIN"]} if "CHROMIUM_BIN" in os.environ else {}
        browser = playwright.chromium.launch(args=args, **options)
        for width in (390, 820, 1440):
            for force_fallback in (False, True):
                page = browser.new_page(viewport={"width": width, "height": 900})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                if force_fallback:
                    page.add_init_script("""
                      const originalContext=HTMLCanvasElement.prototype.getContext;
                      HTMLCanvasElement.prototype.getContext=function(type,...args){
                        return type.startsWith('webgl') ? null : originalContext.call(this,type,...args);
                      };
                    """)
                page.route("https://fixture.invalid/**", lambda route: route.fulfill(
                    content_type="text/html", body=hub if route.request.url.endswith("/agents") else office))
                page.goto("https://fixture.invalid/agents")
                assert page.locator(".company-agent-card").count() == 20, errors
                assert page.locator(".company-agent-card .company-avatar").all_text_contents().count("LEG") == 1
                page.goto("https://fixture.invalid/office")
                page.locator('[data-office-render="live"]').click()
                if force_fallback:
                    assert page.locator("[data-svg-dept]").count() == 16
                else:
                    assert page.locator("#officeShell canvas").count() == 1
                    assert page.locator(".office-svg-fallback").count() == 0
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                assert not errors, errors
                page.close()
                print(f"{width}px · {'SVG fallback' if force_fallback else 'WebGL'} PASS", flush=True)
        browser.close()


if __name__ == "__main__":
    check()
