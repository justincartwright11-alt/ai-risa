import unittest
from workflows.release_audit_pack import release_audit_pack
from workflows.publication_control_pack import publication_control_pack

def make_release_audit(event_name, auditable, blocked, blocker_summary=None):
    return {
        "event_name": event_name,
        "release_audit_status": (
            "ready" if blocked == [] else ("blocked" if auditable == [] else "partial")
        ),
        "auditable_releases": auditable,
        "blocked_audits": blocked,
        "ready_bout_indices": [d.get("bout_index") for d in auditable],
        "blocked_bout_indices": [b.get("bout_index") for b in blocked],
        "blocker_summary": blocker_summary if blocker_summary is not None else {b.get("bout_index"): b.get("blocker_reason", "") for b in blocked},
        "release_audit_summary": {}
    }

def make_auditable(bout_index, order, label, key, a, b, extra=None):
    d = {
        "bout_index": bout_index,
        "delivery_key": key,
        "publication_label": label,
        "publication_order": order,
        "fighter_a": a,
        "fighter_b": b,
        "execution_action": "publish_ready",
        "audit_checks": {
            "delivery_key_present": True,
            "publication_label_present": True,
            "publication_order_present": True,
            "fighter_fields_present": True,
            "execution_action_valid": True
        },
        "execution_snapshot": {}
    }
    if extra:
        d.update(extra)
    return d

def make_blocked(bout_index, reason):
    return {
        "bout_index": bout_index,
        "blocker_reason": reason,
        "execution_snapshot": {}
    }

class TestPublicationControlPack(unittest.TestCase):
    def test_fully_approved(self):
        auditable = [
            make_auditable(0, 0, "Bout 1", "E1_delivery_0", "A", "B"),
            make_auditable(1, 1, "Bout 2", "E1_delivery_1", "C", "D")
        ]
        blocked = []
        bundle = make_release_audit("E1", auditable, blocked)
        control = publication_control_pack(bundle)
        self.assertEqual(control["publication_control_status"], "ready")
        self.assertEqual(len(control["approved_publications"]), 2)
        self.assertEqual(len(control["blocked_publications"]), 0)
        for i, d in enumerate(control["approved_publications"]):
            self.assertEqual(d["bout_index"], i)
            self.assertEqual(d["delivery_key"], auditable[i]["delivery_key"])
            self.assertEqual(d["publication_label"], auditable[i]["publication_label"])
            self.assertEqual(d["publication_order"], auditable[i]["publication_order"])
            self.assertEqual(d["fighter_a"], auditable[i]["fighter_a"])
            self.assertEqual(d["fighter_b"], auditable[i]["fighter_b"])
            self.assertEqual(d["execution_action"], "publish_ready")
            self.assertIn("audit_checks", d)
            self.assertTrue(d["audit_checks"]["delivery_key_present"])
            self.assertTrue(d["audit_checks"]["publication_label_present"])
            self.assertTrue(d["audit_checks"]["publication_order_present"])
            self.assertTrue(d["audit_checks"]["fighter_fields_present"])
            self.assertTrue(d["audit_checks"]["execution_action_valid"])
        self.assertEqual(control["ready_bout_indices"], [0, 1])
        self.assertEqual(control["blocked_bout_indices"], [])

    def test_mixed(self):
        auditable = [make_auditable(0, 0, "Bout 1", "E2_delivery_0", "A", "B")]
        blocked = [make_blocked(1, "fighters_invalid")]
        bundle = make_release_audit("E2", auditable, blocked)
        control = publication_control_pack(bundle)
        self.assertEqual(control["publication_control_status"], "partial")
        self.assertEqual(len(control["approved_publications"]), 1)
        self.assertEqual(len(control["blocked_publications"]), 1)
        self.assertEqual(control["blocked_publications"][0]["blocker_reason"], "fighters_invalid")
        self.assertEqual(control["ready_bout_indices"], [0])
        self.assertEqual(control["blocked_bout_indices"], [1])

    def test_fully_blocked(self):
        auditable = []
        blocked = [make_blocked(0, "fighters_invalid"), make_blocked(1, "fighters_invalid")]
        bundle = make_release_audit("E3", auditable, blocked)
        control = publication_control_pack(bundle)
        self.assertEqual(control["publication_control_status"], "blocked")
        self.assertEqual(len(control["approved_publications"]), 0)
        self.assertEqual(len(control["blocked_publications"]), 2)
        for b in control["blocked_publications"]:
            self.assertIn("blocker_reason", b)
        self.assertEqual(control["ready_bout_indices"], [])
        self.assertEqual(control["blocked_bout_indices"], [0, 1])

    def test_stable_ordering(self):
        auditable = [
            make_auditable(1, 1, "Bout 2", "E4_delivery_1", "C", "D"),
            make_auditable(0, 0, "Bout 1", "E4_delivery_0", "A", "B")
        ]
        blocked = [make_blocked(2, "fighters_invalid")]
        bundle = make_release_audit("E4", auditable, blocked)
        control = publication_control_pack(bundle)
        # Should be sorted by publication_order then bout_index
        self.assertEqual([d["publication_order"] for d in control["approved_publications"]], [0, 1])
        self.assertEqual([d["bout_index"] for d in control["approved_publications"]], [0, 1])
        self.assertEqual([b["bout_index"] for b in control["blocked_publications"]], [2])

    def test_stable_blocker_carry_through(self):
        auditable = [make_auditable(0, 0, "Bout 1", "E5_delivery_0", "A", "B")]
        blocked = [make_blocked(1, "fighters_invalid")]
        bundle = make_release_audit("E5", auditable, blocked, blocker_summary={1: "fighters_invalid"})
        control = publication_control_pack(bundle)
        self.assertEqual(control["blocker_summary"], {1: "fighters_invalid"})
