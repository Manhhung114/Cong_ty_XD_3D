"""V6.7 server-projected authorized signed event monitoring, including MEP↔XD."""
from datetime import datetime, timedelta, timezone
import unittest

from drive_storage.monitoring import (
    build_monitor_packet, system_for, relation,
    MEP_DEPARTMENTS, XD_DEPARTMENTS, ALL_DEPARTMENTS,
    MAX_MONITOR_EVENTS,
)


NOW = datetime(2026, 11, 17, 2, 0, tzinfo=timezone.utc)
MEP_ID = "project-folder-012345678"
OTHER_ID = "project-folder-876543210"


def event(eid, action, project=MEP_ID, minutes=20, data=None, actor="staff@example.com"):
    return {
        "id": eid, "at": (NOW-timedelta(minutes=minutes)).isoformat(),
        "actor": actor, "project_id": project,
        "action": action, "data": data or {},
    }


def state():
    return {
        "projects": [{"id": MEP_ID, "code": "S234", "name": "Sunshine"}],
        "tasks": [
            {"id": "a"*32, "projectId": MEP_ID,
             "dept": "electrical", "status": "review",
             "reviewHistory": [{"at": NOW.isoformat(), "decision": "submitted"}],
             "createdAt": NOW.isoformat(), "dueDate": "2026-11-16",
             "code": "CV-001", "priority": "high"},
            {"id": "b"*32, "projectId": MEP_ID,
             "dept": "structure", "status": "working",
             "createdAt": NOW.isoformat(), "dueDate": "2026-11-18",
             "code": "CV-002", "priority": "normal"},
        ],
        "handoffs": [
            {"id": "h"*32, "projectId": MEP_ID, "taskId": "a"*32,
             "sourceDept": "electrical", "targetDept": "structure",
             "createdAt": (NOW-timedelta(hours=5)).isoformat(),
             "status": "open", "title": "MEP sang XD"},
            {"id": "i"*32, "projectId": MEP_ID, "taskId": "b"*32,
             "sourceDept": "structure", "targetDept": "bim",
             "createdAt": (NOW-timedelta(minutes=90)).isoformat(),
             "resolvedAt": NOW.isoformat(), "status": "resolved",
             "title": "XD sang MEP"},
        ],
        "agentRuns": [],
    }


class MonitoringBackendTests(unittest.TestCase):
    def test_dual_system_classification_and_cross_links(self):
        self.assertEqual(system_for("electrical"), "mep")
        self.assertEqual(system_for("bim"), "mep")
        self.assertEqual(system_for("structure"), "xd")
        self.assertEqual(system_for("xd_bim"), "xd")
        self.assertEqual(system_for("director"), "shared")
        self.assertEqual(relation("electrical", "structure"), "mep_to_xd")
        self.assertEqual(relation("structure", "bim"), "xd_to_mep")
        self.assertEqual(relation("hvac", "bim"), "mep_to_mep")
        self.assertEqual(relation("xd_site", "structure"), "xd_to_xd")
        self.assertEqual(relation("director", "electrical"), "shared")
        self.assertTrue(MEP_DEPARTMENTS.isdisjoint(XD_DEPARTMENTS))
        self.assertEqual(len(ALL_DEPARTMENTS), 16)

    def test_project_acl_filters_every_event_before_projection(self):
        ledger = [
            event("a"*32,"agent.completed",data={"agent_id":"ELE","task_id":"a"*32}),
            event("b"*32,"handoff.requested",
                  data={"source_dept":"electrical","target_dept":"structure",
                        "task_id":"a"*32}),
            event("c"*32,"agent.completed",OTHER_ID,5,
                  {"agent_id":"ELE","task_id":"c"*32,
                   "api_key":"DO_NOT_SEND_TO_BROWSER"}),
            event("d"*32,"document.registered",
                  data={"code":"PCCC","description":"INTERNAL PRIVATE BODY"}),
        ]
        packet = build_monitor_packet(
            {"email":"viewer@example.com","role":"read"}, state(), ledger, now=NOW,
        )
        self.assertEqual(packet["authorizedProjects"], 1)
        self.assertEqual(len(packet["events"]), 3)
        self.assertFalse(any(x["projectId"]==OTHER_ID for x in packet["events"]))
        self.assertEqual(packet["events"][0]["action"], "document.registered")
        self.assertEqual(packet["events"][1]["relation"], "mep_to_xd")
        self.assertEqual(packet["events"][2]["agentId"], "ELE")
        self.assertEqual(packet["handoffs"][0]["relation"], "mep_to_xd")
        self.assertEqual(packet["handoffs"][1]["relation"], "xd_to_mep")
        self.assertNotIn("INTERNAL PRIVATE BODY", str(packet))
        self.assertNotIn("DO_NOT_SEND_TO_BROWSER", str(packet))
        self.assertEqual(packet["capabilities"]["websocket"], False)
        self.assertEqual(packet["capabilities"]["agentRunningHeartbeat"], False)

    def test_current_window_and_old_events(self):
        packet=build_monitor_packet(
            {"email":"viewer@example.com","role":"read"}, state(),
            [event("a"*32,"agent.completed",minutes=20),
             event("b"*32,"agent.completed",minutes=8*24*60),
             event("c"*32,"agent.completed",minutes=-40)],
            now=NOW,
        )
        self.assertEqual(len(packet["events"]),1)
        self.assertEqual(packet["events"][0]["id"], "a"*32)

    def test_invalid_identity_and_unsigned_scope_errors(self):
        with self.assertRaises(PermissionError):
            build_monitor_packet({"role":"guest"},state(),[],now=NOW)
        foreign=state()
        foreign["tasks"].append({"id":"d"*32,"projectId":OTHER_ID})
        with self.assertRaises(PermissionError):
            build_monitor_packet({"role":"admin"},foreign,[],now=NOW)
        with self.assertRaises(ValueError):
            build_monitor_packet({"role":"admin"},state(),
                                 [event("e"*32,"agent.completed") | {"at":"BAD"}],now=NOW)

    def test_900_event_cap_is_reported_not_hidden(self):
        signed=[event(f"{i:032x}","agent.completed",minutes=(i%60))
                for i in range(MAX_MONITOR_EVENTS+5)]
        packet=build_monitor_packet({"role":"admin"},state(),signed,now=NOW)
        self.assertTrue(packet["eventsTruncated"])
        self.assertEqual(packet["eventsAvailable"],MAX_MONITOR_EVENTS+5)
        self.assertEqual(len(packet["events"]),MAX_MONITOR_EVENTS)


if __name__=="__main__":
    unittest.main()
