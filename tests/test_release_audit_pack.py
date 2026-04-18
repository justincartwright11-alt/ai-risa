import unittest
from workflows.publication_release_pack import publication_release_pack
from workflows.release_audit_pack import release_audit_pack

def make_publication_release(event_name, release_ready, blocked, review_flags=None, blocker_summary=None):
    return {
        "event_name": event_name,
        "publication_release_status": (
            "ready" if blocked == [] else ("blocked" if release_ready == [] else "partial")
        ),
        "release_ready_exports": release_ready,
        "blocked_releases": blocked,
        "release_ready_bout_indices": [d["bout_index"] for d in release_ready],
        "blocked_bout_indices": [b["bout_index"] for b in blocked],
        "review_flags": review_flags if review_flags is not None else {r["bout_index"]: [] for r in release_ready} | {b["bout_index"]: [b.get("blocker_reason")] for b in blocked},
        "blocker_summary": blocker_summary if blocker_summary is not None else {b["bout_index"]: b.get("blocker_reason", "") for b in blocked},
        "publication_release_summary": {}
    }

def make_release_ready(event_name, bout_index, order, label, key, a, b, extra=None):
    d = {
        "event_name": event_name,
        "bout_index": bout_index,
        "release_status": "release_ready",
        "delivery_key": key,
        "publication_label": label,
        "publication_order": order,
        "fighter_a": a,
        "fighter_b": b,
        "release_notes": [],
        "operator_review_snapshot": {}
    }
    if extra:
        d.update(extra)
    return d

def make_blocked(event_name, bout_index, reason):
    return {
        "event_name": event_name,
        "bout_index": bout_index,
        "release_status": "blocked",
        "blocker_reason": reason,
        "operator_review_snapshot": {}
    }

class TestReleaseAuditPack(unittest.TestCase):
    def test_fully_auditable(self):
        release_ready = [
            make_release_ready("E1", 0, 0, "Bout 1", "E1_delivery_0", "A", "B"),
            make_release_ready("E1", 1, 1, "Bout 2", "E1_delivery_1", "C", "D")
        ]
        blocked = []
        review_flags = {0: [], 1: []}
        bundle = make_publication_release("E1", release_ready, blocked, review_flags)
        audit = release_audit_pack(bundle)
        self.assertEqual(audit["release_audit_status"], "ready")
        self.assertEqual(len(audit["auditable_releases"]), 2)
        self.assertEqual(len(audit["blocked_audits"]), 0)
        for i, d in enumerate(audit["auditable_releases"]):
            self.assertEqual(d["audit_status"], "auditable")
            self.assertEqual(d["bout_index"], i)
            self.assertEqual(d["delivery_key"], release_ready[i]["delivery_key"])
            self.assertEqual(d["release_snapshot"]["delivery_key"], release_ready[i]["delivery_key"])
            self.assertIn("audit_checks", d)
            self.assertTrue(d["audit_checks"]["delivery_key_present"])
            self.assertTrue(d["audit_checks"]["publication_label_present"])
            self.assertTrue(d["audit_checks"]["publication_order_present"])
            self.assertTrue(d["audit_checks"]["fighter_fields_present"])
            self.assertTrue(d["audit_checks"]["release_status_valid"])
        self.assertEqual(audit["release_ready_bout_indices"], [0, 1])
        self.assertEqual(audit["blocked_bout_indices"], [])
        self.assertEqual(audit["review_flags"], {0: [], 1: []})

    def test_mixed(self):
        release_ready = [make_release_ready("E2", 0, 0, "Bout 1", "E2_delivery_0", "A", "B")]
        blocked = [make_blocked("E2", 1, "fighters_invalid")]
        review_flags = {0: [], 1: ["fighters_invalid"]}
        bundle = make_publication_release("E2", release_ready, blocked, review_flags)
        audit = release_audit_pack(bundle)
        self.assertEqual(audit["release_audit_status"], "partial")
        self.assertEqual(len(audit["auditable_releases"]), 1)
        self.assertEqual(len(audit["blocked_audits"]), 1)
        self.assertEqual(audit["blocked_audits"][0]["blocker_reason"], "fighters_invalid")
        self.assertEqual(audit["release_ready_bout_indices"], [0])
        self.assertEqual(audit["blocked_bout_indices"], [1])
        self.assertEqual(audit["review_flags"], {0: [], 1: ["fighters_invalid"]})

    def test_fully_blocked(self):
        release_ready = []
        blocked = [make_blocked("E3", 0, "fighters_invalid"), make_blocked("E3", 1, "fighters_invalid")]
        review_flags = {0: ["fighters_invalid"], 1: ["fighters_invalid"]}
        bundle = make_publication_release("E3", release_ready, blocked, review_flags)
        audit = release_audit_pack(bundle)
        self.assertEqual(audit["release_audit_status"], "blocked")
        self.assertEqual(len(audit["auditable_releases"]), 0)
        self.assertEqual(len(audit["blocked_audits"]), 2)
        for b in audit["blocked_audits"]:
            self.assertEqual(b["audit_status"], "blocked")
            self.assertIn("blocker_reason", b)
        self.assertEqual(audit["release_ready_bout_indices"], [])
        self.assertEqual(audit["blocked_bout_indices"], [0, 1])
        self.assertEqual(audit["review_flags"], {0: ["fighters_invalid"], 1: ["fighters_invalid"]})

    def test_stable_ordering(self):
        release_ready = [
            make_release_ready("E4", 1, 1, "Bout 2", "E4_delivery_1", "C", "D"),
            make_release_ready("E4", 0, 0, "Bout 1", "E4_delivery_0", "A", "B")
        ]
        blocked = [make_blocked("E4", 2, "fighters_invalid")]
        review_flags = {0: [], 1: [], 2: ["fighters_invalid"]}
        bundle = make_publication_release("E4", release_ready, blocked, review_flags)
        audit = release_audit_pack(bundle)
        # Should be sorted by publication_order then bout_index
        self.assertEqual([d["bout_index"] for d in audit["auditable_releases"]], [0, 1])
        self.assertEqual([b["bout_index"] for b in audit["blocked_audits"]], [2])

    def test_stable_blocker_carry_through(self):
        release_ready = [make_release_ready("E5", 0, 0, "Bout 1", "E5_delivery_0", "A", "B")]
        blocked = [make_blocked("E5", 1, "fighters_invalid")]
        review_flags = {0: [], 1: ["fighters_invalid"]}
        bundle = make_publication_release("E5", release_ready, blocked, review_flags, blocker_summary={1: "fighters_invalid"})
        audit = release_audit_pack(bundle)
        self.assertEqual(audit["blocker_summary"], {1: "fighters_invalid"})
