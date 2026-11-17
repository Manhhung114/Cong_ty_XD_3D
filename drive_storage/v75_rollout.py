"""Catalog and an independent, explicitly scoped QCX execution switch."""
import os

BUILD_LABEL = "V7.5.3"
LEGACY_POLICY = "v690"
QA_POLICY = "v750"


def _canary_projects():
    return {project.strip() for project in os.getenv("XD_V75_CANARY_PROJECTS", "").split(",")}


def catalog_enabled(project_id):
    mode = os.getenv("XD_V75_CATALOG", "release")
    return bool(project_id and (mode == "release" or (mode == "1" and project_id in _canary_projects())))


def qcx_enabled(project_id):
    return (catalog_enabled(project_id) and os.getenv("XD_V75_QCX") == "1"
            and project_id in _canary_projects())
