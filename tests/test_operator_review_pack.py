import unittest
from workflows.export_bundle_pack import export_bundle_pack
from workflows.operator_review_pack import operator_review_pack

def make_export_bundle(event_name, deliverable, blocked, blocker_summary=None):
    return {
        "event_name": event_name,
        "export_bundle_status": (
            "ready" if blocked == [] else ("blocked" if deliverable == [] else "partial")
        ),
        "deliverable_exports": deliverable,
        "blocked_exports": blocked,
        "deliverable_bout_indices": [d["bout_index"] for d in deliverable],
        "blocked_bout_indices": [b["bout_index"] for b in blocked],
        "blocker_summary": blocker_summary if blocker_summary is not None else {b["bout_index"]: b.get("blocker_reason", "") for b in blocked},
        "export_manifest": {},
        "export_bundle_summary": {}
    }

def make_deliverable(event_name, bout_index, order, label, key, a, b, extra=None):
    d = {
        "event_name": event_name,
        "bout_index": bout_index,
        "export_status": "deliverable",
        "delivery_key": key,
        "publication_label": label,
        "publication_order": order,
        "fighter_a": a,
        "fighter_b": b,
        "weight_class": "LW",
        "scheduled_rounds": 3,
        "is_title_fight": False,
        "export_payload": {},
        "delivery_snapshot": {}
    }
    if extra:
        d.update(extra)
    return d

def make_blocked(event_name, bout_index, reason):
    return {
        "event_name": event_name,
        "bout_index": bout_index,
        "export_status": "blocked",
        "blocker_reason": reason,
        "export_snapshot": {}
    }

class TestOperatorReviewPack(unittest.TestCase):
    def test_fully_reviewable(self):
        deliverable = [
            make_deliverable("E1", 0, 0, "Bout 1", "E1_delivery_0", "A", "B"),
            make_deliverable("E1", 1, 1, "Bout 2", "E1_delivery_1", "C", "D")
        ]
        blocked = []
        bundle = make_export_bundle("E1", deliverable, blocked)
        review = operator_review_pack(bundle)
        self.assertEqual(review["operator_review_status"], "ready")
        self.assertEqual(len(review["reviewable_exports"]), 2)
        self.assertEqual(len(review["blocked_exports"]), 0)
        for i, d in enumerate(review["reviewable_exports"]):
            self.assertEqual(d["review_status"], "reviewable")
            self.assertEqual(d["bout_index"], i)
            self.assertEqual(d["delivery_key"], deliverable[i]["delivery_key"])
            self.assertEqual(d["export_snapshot"]["delivery_key"], deliverable[i]["delivery_key"])
            self.assertEqual(d["review_notes"], [])
        self.assertEqual(review["review_flags"], {0: [], 1: []})

    def test_mixed(self):
        deliverable = [make_deliverable("E2", 0, 0, "Bout 1", "E2_delivery_0", "A", "B")]
        blocked = [make_blocked("E2", 1, "fighters_invalid")]
        bundle = make_export_bundle("E2", deliverable, blocked)
        review = operator_review_pack(bundle)
        self.assertEqual(review["operator_review_status"], "partial")
        self.assertEqual(len(review["reviewable_exports"]), 1)
        self.assertEqual(len(review["blocked_exports"]), 1)
        self.assertEqual(review["blocked_exports"][0]["blocker_reason"], "fighters_invalid")
        self.assertEqual(review["review_flags"], {0: [], 1: ["fighters_invalid"]})

    def test_fully_blocked(self):
        deliverable = []
        blocked = [make_blocked("E3", 0, "fighters_invalid"), make_blocked("E3", 1, "fighters_invalid")]
        bundle = make_export_bundle("E3", deliverable, blocked)
        review = operator_review_pack(bundle)
        self.assertEqual(review["operator_review_status"], "blocked")
        self.assertEqual(len(review["reviewable_exports"]), 0)
        self.assertEqual(len(review["blocked_exports"]), 2)
        for b in review["blocked_exports"]:
            self.assertEqual(b["review_status"], "blocked")
            self.assertIn("blocker_reason", b)
        self.assertEqual(review["review_flags"], {0: ["fighters_invalid"], 1: ["fighters_invalid"]})

    def test_stable_ordering(self):
        deliverable = [
            make_deliverable("E4", 1, 1, "Bout 2", "E4_delivery_1", "C", "D"),
            make_deliverable("E4", 0, 0, "Bout 1", "E4_delivery_0", "A", "B")
        ]
        blocked = [make_blocked("E4", 2, "fighters_invalid")]
        bundle = make_export_bundle("E4", deliverable, blocked)
        review = operator_review_pack(bundle)
        # Should be sorted by publication_order then bout_index
        self.assertEqual([d["bout_index"] for d in review["reviewable_exports"]], [0, 1])
        self.assertEqual([b["bout_index"] for b in review["blocked_exports"]], [2])

    def test_stable_blocker_carry_through(self):
        deliverable = [make_deliverable("E5", 0, 0, "Bout 1", "E5_delivery_0", "A", "B")]
        blocked = [make_blocked("E5", 1, "fighters_invalid")]
        bundle = make_export_bundle("E5", deliverable, blocked, blocker_summary={1: "fighters_invalid"})
        review = operator_review_pack(bundle)
        self.assertEqual(review["blocker_summary"], {1: "fighters_invalid"})
