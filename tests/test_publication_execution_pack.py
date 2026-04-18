import unittest
from workflows.release_audit_pack import release_audit_pack
from workflows.publication_execution_pack import publication_execution_pack

def make_release_audit(event_name, auditable, blocked, blocker_summary=None):
    return {
        "event_name": event_name,
        "release_audit_status": (
            "ready" if blocked == [] else ("blocked" if auditable == [] else "partial")
        ),
        "auditable_releases": auditable,
        "blocked_audits": blocked,
        "release_ready_bout_indices": [d["bout_index"] for d in auditable],
        "blocked_bout_indices": [b["bout_index"] for b in blocked],
        "review_flags": {},
        "blocker_summary": blocker_summary if blocker_summary is not None else {b["bout_index"]: b.get("blocker_reason", "") for b in blocked},
        "release_audit_summary": {}
    }

def make_auditable(event_name, bout_index, order, label, key, extra=None):
    d = {
        "event_name": event_name,
        "bout_index": bout_index,
        "audit_status": "auditable",
        "delivery_key": key,
        "publication_label": label,
        "publication_order": order,
        "audit_checks": {},
        "release_snapshot": {},
        "operator_review_snapshot": {}
    }
    if extra:
        d.update(extra)
    return d

def make_blocked(event_name, bout_index, reason):
    return {
        "event_name": event_name,
        "bout_index": bout_index,
        "audit_status": "blocked",
        "blocker_reason": reason,
        "release_snapshot": {}
    }

class TestPublicationExecutionPack(unittest.TestCase):
    def test_fully_executable(self):
        auditable = [
            make_auditable("E1", 0, 0, "Bout 1", "E1_delivery_0"),
            make_auditable("E1", 1, 1, "Bout 2", "E1_delivery_1")
        ]
        blocked = []
        bundle = make_release_audit("E1", auditable, blocked)
        execution = publication_execution_pack(bundle)
        self.assertEqual(execution["publication_execution_status"], "ready")
        self.assertEqual(len(execution["executable_publications"]), 2)
        self.assertEqual(len(execution["blocked_publications"]), 0)
        for i, d in enumerate(execution["executable_publications"]):
            self.assertEqual(d["execution_status"], "executable")
            self.assertEqual(d["bout_index"], i)
            self.assertEqual(d["delivery_key"], auditable[i]["delivery_key"])
            self.assertEqual(d["release_snapshot"], auditable[i]["release_snapshot"])
            self.assertEqual(d["execution_action"], "publish_ready")
        self.assertEqual(execution["ready_bout_indices"], [0, 1])
        self.assertEqual(execution["blocked_bout_indices"], [])

    def test_mixed(self):
        auditable = [make_auditable("E2", 0, 0, "Bout 1", "E2_delivery_0")]
        blocked = [make_blocked("E2", 1, "fighters_invalid")]
        bundle = make_release_audit("E2", auditable, blocked)
        execution = publication_execution_pack(bundle)
        self.assertEqual(execution["publication_execution_status"], "partial")
        self.assertEqual(len(execution["executable_publications"]), 1)
        self.assertEqual(len(execution["blocked_publications"]), 1)
        self.assertEqual(execution["blocked_publications"][0]["blocker_reason"], "fighters_invalid")
        self.assertEqual(execution["ready_bout_indices"], [0])
        self.assertEqual(execution["blocked_bout_indices"], [1])

    def test_fully_blocked(self):
        auditable = []
        blocked = [make_blocked("E3", 0, "fighters_invalid"), make_blocked("E3", 1, "fighters_invalid")]
        bundle = make_release_audit("E3", auditable, blocked)
        execution = publication_execution_pack(bundle)
        self.assertEqual(execution["publication_execution_status"], "blocked")
        self.assertEqual(len(execution["executable_publications"]), 0)
        self.assertEqual(len(execution["blocked_publications"]), 2)
        for b in execution["blocked_publications"]:
            self.assertEqual(b["execution_status"], "blocked")
            self.assertIn("blocker_reason", b)
        self.assertEqual(execution["ready_bout_indices"], [])
        self.assertEqual(execution["blocked_bout_indices"], [0, 1])

    def test_stable_ordering(self):
        auditable = [
            make_auditable("E4", 1, 1, "Bout 2", "E4_delivery_1"),
            make_auditable("E4", 0, 0, "Bout 1", "E4_delivery_0")
        ]
        blocked = [make_blocked("E4", 2, "fighters_invalid")]
        bundle = make_release_audit("E4", auditable, blocked)
        execution = publication_execution_pack(bundle)
        # Should be sorted by publication_order then bout_index
        self.assertEqual([d["bout_index"] for d in execution["executable_publications"]], [0, 1])
        self.assertEqual([b["bout_index"] for b in execution["blocked_publications"]], [2])

    def test_stable_blocker_carry_through(self):
        auditable = [make_auditable("E5", 0, 0, "Bout 1", "E5_delivery_0")]
        blocked = [make_blocked("E5", 1, "fighters_invalid")]
        bundle = make_release_audit("E5", auditable, blocked, blocker_summary={1: "fighters_invalid"})
        execution = publication_execution_pack(bundle)
        self.assertEqual(execution["blocker_summary"], {1: "fighters_invalid"})
