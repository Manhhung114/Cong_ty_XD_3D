"""Regression for V7.5.2 Agent dialog UnboundLocalError on Streamlit Cloud.

A late 'from drive_storage.hierarchy import require_qc_role' inside the
render() function used to make require_qc_role a local before its first use.
The real dialog raises UnboundLocalError without this test covering the path.
"""
import unittest
from unittest.mock import patch, Mock

from drive_storage.company_ui import company_dialog


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.errors = []

    def dialog(self, *args, **kwargs):
        # Streamlit decorators return a callable; company_dialog invokes render().
        return lambda func: func

    def button(self, *args, **kwargs):
        return False

    def error(self, text):
        self.errors.append(str(text))


class AgentDialogEarlyAuthorizationTests(unittest.TestCase):
    def test_agent_modal_checks_qa_guard_without_unboundlocal(self):
        st = _FakeStreamlit()
        identity = {"email": "engineer@example.com", "role": "update",
                    "projects": ["test-project"]}
        server = Mock()
        server.snapshot.return_value = {
            "projects": [{"id": "test-project"}],
            "tasks": [],
        }
        agent = {"id": "ELE", "title": "Kỹ sư Điện"}
        task = {"id": "test-task", "projectId": "test-project",
                "title": "Kiểm tra bản vẽ điện", "dept": "electrical"}
        qc_guard = Mock(side_effect=PermissionError("QA_GUARD_REACHED"))

        with (
            patch("drive_storage.company_ui.identity_for", return_value=identity),
            patch("drive_storage.company_ui.can_upload", return_value=True),
            patch("drive_storage.company_ui.service_for", return_value=server),
            patch("drive_storage.company_agents._task_context",
                  return_value=(agent, task, {}, [])),
            patch("drive_storage.hierarchy.require_operator") as operator,
            patch("drive_storage.hierarchy.require_qc_role", qc_guard),
        ):
            company_dialog(st, {
                "op": "agent_run", "projectId": "test-project",
                "taskId": "test-task", "agentId": "ELE",
            })
            operator.assert_called_once_with(identity, task)
            qc_guard.assert_called_once_with(identity, task, server.snapshot.return_value)
        self.assertEqual(st.errors, ["QA_GUARD_REACHED"])


if __name__ == "__main__":
    unittest.main()
