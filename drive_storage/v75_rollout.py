"""Server-side V7.5 canary switches. Missing configuration keeps V7.4 active."""
import os

LEGACY_POLICY = "v690"
QA_POLICY = "v750"


def catalog_enabled(project_id):
    projects = {project.strip() for project in os.getenv("XD_V75_CANARY_PROJECTS", "").split(",")}
    return bool(project_id and os.getenv("XD_V75_CATALOG") == "1" and project_id in projects)


def qcx_enabled(project_id):
    return catalog_enabled(project_id) and os.getenv("XD_V75_QCX") == "1"
