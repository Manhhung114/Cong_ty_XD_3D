"""V6.9 signed hierarchical task orchestration regression tests.

Realistic CEO -> PM -> Lead -> Expert + independent QA -> PM -> CEO
stages. All Drive interactions use the existing fake in-memory media provider.
No real AI call, no background execution, no invented approvals.
"""
import unittest

from test_v59_v60_cloud_workflow import CloudWorkflowTests, PROJECT
from drive_storage.company_agents import run_agent
from drive_storage.hierarchy import (
    MAX_DEPARTMENTS, DEPT_LABELS, deterministic_id, normalize_departments,
    plan_tasks, suggest_departments, can_review_node, dependencies_block,
)


class HierarchyPureTests(unittest.TestCase):
    def test_department_routing_is_explicit_and_bounded(self):
        self.assertIn("electrical", suggest_departments("Kiểm tra bản vẽ tủ điện R01"))
        self.assertIn("fire", suggest_departments("Rà soát PCCC"))
        self.assertEqual(suggest_departments("Nhiệm vụ không rõ chuyên ngành"), [])
        self.assertEqual(MAX_DEPARTMENTS, 4)
        self.assertEqual(normalize_departments(["electrical", "hvac"]),
                         ["electrical", "hvac"])
        for invalid in ([], ["electrical"] * 2,
                        ["garbage"], list(DEPT_LABELS)[:5]):
            with self.assertRaises(ValueError):
                normalize_departments(invalid)

    def test_deterministic_ids_and_parent_dependency_topology(self):
        root = {"id": "a" * 32, "projectId": PROJECT, "title": "Kiểm tra tủ điện",
                "docCode": "R01", "priority": "high", "dueDate": "2026-12-01"}
        nodes = plan_tasks(root=root, departments=["electrical", "hvac"],
                           dispatch_id="b" * 32, proposal_id="c" * 32, roles=[])
        self.assertEqual(len(nodes), 7)
        self.assertEqual([n["stage"] for n in nodes],
                         ["pm", "lead", "expert", "qa", "lead", "expert", "qa"])
        self.assertEqual(len({n["id"] for n in nodes}), 7)
        self.assertEqual(nodes[0]["parent_id"], root["id"])
        self.assertEqual(nodes[1]["parent_id"], nodes[0]["id"])
        self.assertEqual(nodes[2]["parent_id"], nodes[1]["id"])
        self.assertEqual(nodes[3]["parent_id"], nodes[1]["id"])
        self.assertEqual(nodes[3]["depends_on"], [nodes[2]["id"]])
        self.assertEqual(nodes[3]["agent_id"], "QAC")
        self.assertEqual(nodes[5]["agent_id"], "HVA")
        self.assertTrue(all(node["root_task_id"] == root["id"] for node in nodes))
        self.assertEqual(nodes, plan_tasks(
            root=root, departments=["electrical", "hvac"],
            dispatch_id="b" * 32, proposal_id="c" * 32, roles=[]))
        self.assertEqual(len(deterministic_id("a" * 32, "lead_electrical")), 32)


class HierarchyFlowTests(unittest.TestCase):
    def setUp(self):
        CloudWorkflowTests.setUp(self)
        self.pm = {"email": "pm@example.com", "role": "update", "projects": [PROJECT]}
        self.lead = {"email": "lead@example.com", "role": "update", "projects": [PROJECT]}
        self.engineer = {"email": "engineer@example.com", "role": "update",
                         "projects": [PROJECT]}
        self.qa = {"email": "qa@example.com", "role": "update", "projects": [PROJECT]}
        self.root_id = self.ws.create_task(
            self.editor, project_id=PROJECT, dept="director", agent_id="CEO",
            assignee=self.editor["email"], title="Kiểm tra bản vẽ tủ điện R01",
            doc_code="R01", priority="high",
        )["id"]

    def tearDown(self):
        CloudWorkflowTests.tearDown(self)

    def state(self):
        return self.ws.snapshot(self.admin)

    def node(self, stage):
        return next(t for t in self.state()["tasks"] if t.get("hierarchyStage") == stage)

    def assign_people(self):
        for email, role, dept in [
            (self.editor["email"], "director", "director"),
            (self.pm["email"], "pm", "director"),
            (self.lead["email"], "lead", "electrical"),
            (self.engineer["email"], "engineer", "electrical"),
            (self.qa["email"], "qa", "qa"),
        ]:
            self.ws.set_org_role(self.admin, project_id=PROJECT,
                                 email=email, role=role, department=dept)

    def dispatch(self, departments=None):
        self.assign_people()
        proposal = self.ws.propose_hierarchy(
            self.editor, project_id=PROJECT, task_id=self.root_id,
            departments=departments or ["electrical"],
            instructions="Cần độc lập QA và lưu báo cáo gắn bản vẽ R01",
        )
        self.ws.review_hierarchy(
            self.admin, project_id=PROJECT, proposal_id=proposal["id"],
            decision="approve", event_id="b" * 32,
        )
        return proposal["id"]

    def test_propose_approve_does_not_fake_agent_runs_and_is_idempotent(self):
        self.dispatch(["electrical", "hvac"])
        state = self.state()
        self.assertEqual(len(state["tasks"]), 8)
        self.assertEqual(len(state["agentRuns"]), 0)
        self.assertEqual(len(state["hierarchyPlans"]), 1)
        self.assertEqual(state["hierarchyPlans"][0]["status"], "dispatched")
        self.assertEqual(state["hierarchyPlans"][0]["reviewedBy"], self.admin["email"])
        self.assertEqual(len(state["orgRoles"]), 5)
        root = next(t for t in state["tasks"] if t["id"] == self.root_id)
        self.assertEqual(root["hierarchyStage"], "ceo")
        self.assertEqual(root["hierarchyProgress"]["total"], 1)
        child = next(t for t in state["tasks"] if t["hierarchyStage"] == "pm")
        self.assertEqual(child["assignee"], self.pm["email"])
        self.assertEqual(child["parentTaskId"], self.root_id)
        self.assertEqual(child["assignedAgentId"], "PM")
        # No duplicate dispatch, even if browser retries.
        with self.assertRaises(ValueError):
            self.ws.propose_hierarchy(self.editor, project_id=PROJECT,
                                      task_id=self.root_id,
                                      departments=["electrical"])
        with self.assertRaises(ValueError):
            self.ws.review_hierarchy(self.admin, project_id=PROJECT,
                                     proposal_id=state["hierarchyPlans"][0]["id"],
                                     decision="approve")

    def test_complete_chain_requires_verified_manager_and_independent_qa(self):
        self.dispatch()
        pm, lead, expert, qa = [self.node(s) for s in ("pm", "lead", "expert", "qa")]
        self.assertEqual(lead["assignee"], self.lead["email"])
        self.assertEqual(expert["assignee"], self.engineer["email"])
        self.assertEqual(qa["assignee"], self.qa["email"])
        self.assertEqual(qa["dependsOn"], [expert["id"]])
        self.assertEqual(dependencies_block(qa, self.state()["tasks"]), [expert["id"]])
        with self.assertRaises(PermissionError):
            self.ws.start_task(self.qa, project_id=PROJECT, task_id=qa["id"])
        with self.assertRaises(PermissionError):
            run_agent(self.ws, self.qa, project_id=PROJECT,
                      task_id=qa["id"], agent_id="QAC", mode="preflight")
        with self.assertRaises(PermissionError):
            self.ws.submit_task(self.pm, project_id=PROJECT, task_id=pm["id"],
                                summary="Trình PM khi trưởng bộ môn chưa xong")
        with self.assertRaises(PermissionError):
            self.ws.start_task(self.engineer, project_id=PROJECT, task_id=lead["id"])
        with self.assertRaises(PermissionError):
            self.ws.review_task(self.editor, project_id=PROJECT,
                                task_id=self.root_id, decision="approve")
        self.ws.start_task(self.engineer, project_id=PROJECT, task_id=expert["id"])
        run = run_agent(self.ws, self.engineer, project_id=PROJECT,
                        task_id=expert["id"], agent_id="ELE", mode="preflight")
        self.assertTrue(run["reviewRequired"])
        self.assertEqual(self.node("expert")["status"], "working")
        self.ws.submit_task(self.engineer, project_id=PROJECT, task_id=expert["id"],
                            summary="Đã kiểm tra lớp mẫu DXF và lập danh sách thiếu")
        with self.assertRaises(PermissionError):
            self.ws.review_task(self.engineer, project_id=PROJECT,
                                task_id=expert["id"], decision="approve")
        self.assertTrue(can_review_node(self.lead, self.node("expert"), self.state()["tasks"]))
        self.ws.review_task(self.lead, project_id=PROJECT,
                            task_id=expert["id"], decision="approve")
        self.ws.start_task(self.qa, project_id=PROJECT, task_id=qa["id"])
        self.ws.submit_task(self.qa, project_id=PROJECT, task_id=qa["id"],
                            summary="QA đối chiếu độc lập bản vẽ và nguồn bằng chứng")
        with self.assertRaises(PermissionError):
            self.ws.review_task(self.lead, project_id=PROJECT,
                                task_id=qa["id"], decision="approve")
        self.ws.review_task(self.admin, project_id=PROJECT,
                            task_id=qa["id"], decision="approve")
        self.ws.start_task(self.lead, project_id=PROJECT, task_id=lead["id"])
        self.ws.submit_task(self.lead, project_id=PROJECT, task_id=lead["id"],
                            summary="Trưởng bộ môn xác nhận chuyên gia và QA đã hoàn thành")
        self.ws.review_task(self.pm, project_id=PROJECT,
                            task_id=lead["id"], decision="approve")
        self.ws.start_task(self.pm, project_id=PROJECT, task_id=pm["id"])
        self.ws.submit_task(self.pm, project_id=PROJECT, task_id=pm["id"],
                            summary="PM đã tổng hợp và kiểm tra tiến độ thực hiện")
        self.ws.review_task(self.editor, project_id=PROJECT,
                            task_id=pm["id"], decision="approve")
        self.ws.start_task(self.editor, project_id=PROJECT, task_id=self.root_id)
        self.ws.submit_task(self.editor, project_id=PROJECT, task_id=self.root_id,
                            summary="Giám đốc đã xem xét tổng hợp và QA/QC độc lập")
        self.ws.review_task(self.admin, project_id=PROJECT,
                            task_id=self.root_id, decision="approve")
        self.assertEqual(next(t for t in self.state()["tasks"]
                              if t["id"] == self.root_id)["status"], "done")
        self.assertEqual(sum(t["status"] == "done" for t in self.state()["tasks"]), 5)
        self.assertEqual(len(self.state()["agentRuns"]), 1)

    def test_reject_plan_requires_reason_and_allows_reproposal(self):
        proposal = self.ws.propose_hierarchy(self.editor, project_id=PROJECT,
                                             task_id=self.root_id,
                                             departments=["electrical"])
        with self.assertRaises(PermissionError):
            self.ws.review_hierarchy(self.editor, project_id=PROJECT,
                                     proposal_id=proposal["id"], decision="approve")
        with self.assertRaises(ValueError):
            self.ws.review_hierarchy(self.admin, project_id=PROJECT,
                                     proposal_id=proposal["id"], decision="reject",
                                     reason="Sai")
        self.ws.review_hierarchy(self.admin, project_id=PROJECT,
                                 proposal_id=proposal["id"], decision="reject",
                                 reason="Cần bổ sung nhóm HVAC cho dự án")
        self.assertEqual(self.state()["hierarchyPlans"][0]["status"], "rejected")
        self.assertEqual(len(self.state()["tasks"]), 1)
        self.ws.propose_hierarchy(self.editor, project_id=PROJECT,
                                  task_id=self.root_id,
                                  departments=["electrical", "hvac"])

    def test_roles_and_scope_fail_closed(self):
        with self.assertRaises(PermissionError):
            self.ws.set_org_role(self.editor, project_id=PROJECT,
                                 email=self.pm["email"], role="pm",
                                 department="director")
        with self.assertRaises(ValueError):
            self.ws.set_org_role(self.admin, project_id=PROJECT,
                                 email=self.pm["email"], role="pm",
                                 department="electrical")
        with self.assertRaises(PermissionError):
            self.ws.propose_hierarchy(self.pm, project_id=PROJECT,
                                      task_id=self.root_id,
                                      departments=["electrical"])
        with self.assertRaises(PermissionError):
            self.ws.propose_hierarchy(self.editor,
                                      project_id="project-folder-000002",
                                      task_id=self.root_id,
                                      departments=["electrical"])

    def test_parent_cannot_be_cancelled_while_descendants_exist(self):
        self.dispatch()
        with self.assertRaises(PermissionError):
            self.ws.cancel_task(self.admin, project_id=PROJECT,
                                task_id=self.root_id,
                                reason="Không được bỏ lại nhiệm vụ con")
        self.assertEqual(next(t for t in self.state()["tasks"] if t["id"] == self.root_id)
                         ["status"], "todo")

if __name__ == "__main__":
    unittest.main()
