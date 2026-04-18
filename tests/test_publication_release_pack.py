import unittest
from workflows.operator_review_pack import operator_review_pack
from workflows.publication_release_pack import publication_release_pack

def make_operator_review(event_name, reviewable, blocked, review_flags=None, blocker_summary=None):
    return {
        "event_name": event_name,
        "operator_review_status": (
            "ready" if blocked == [] else ("blocked" if reviewable == [] else "partial")
        ),
        "reviewable_exports": reviewable,
        "blocked_exports": blocked,
        "review_flags": review_flags if review_flags is not None else {r["bout_index"]: [] for r in reviewable} | {b["bout_index"]: [b.get("blocker_reason")] for b in blocked},
        "blocker_summary": blocker_summary if blocker_summary is not None else {b["bout_index"]: b.get("blocker_reason", "") for b in blocked},
        "operator_review_summary": {}
    }

def make_reviewable(event_name, bout_index, order, label, key, a, b, extra=None):
    d = {
        "event_name": event_name,
        "bout_index": bout_index,
        "review_status": "reviewable",
        "delivery_key": key,
        "publication_label": label,
        "publication_order": order,
        "fighter_a": a,
        "fighter_b": b,
        "review_notes": [],
        "export_snapshot": {}
    }
    if extra:
        d.update(extra)
    return d

def make_blocked(event_name, bout_index, reason):
    return {
        "event_name": event_name,
        "bout_index": bout_index,
        "review_status": "blocked",
        "blocker_reason": reason,
        "export_snapshot": {}
    }

class TestPublicationReleasePack(unittest.TestCase):
    def test_fully_release_ready(self):
        reviewable = [
            make_reviewable("E1", 0, 0, "Bout 1", "E1_delivery_0", "A", "B"),
            make_reviewable("E1", 1, 1, "Bout 2", "E1_delivery_1", "C", "D")
        ]
        blocked = []
        review_flags = {0: [], 1: []}
        bundle = make_operator_review("E1", reviewable, blocked, review_flags)
        release = publication_release_pack(bundle)
        self.assertEqual(release["publication_release_status"], "ready")
        self.assertEqual(len(release["release_ready_exports"]), 2)
        self.assertEqual(len(release["blocked_releases"]), 0)
        for i, d in enumerate(release["release_ready_exports"]):
            self.assertEqual(d["release_status"], "release_ready")
            self.assertEqual(d["bout_index"], i)
            self.assertEqual(d["delivery_key"], reviewable[i]["delivery_key"])
            self.assertEqual(d["operator_review_snapshot"]["delivery_key"], reviewable[i]["delivery_key"])
            self.assertEqual(d["release_notes"], [])
        self.assertEqual(release["release_ready_bout_indices"], [0, 1])
        self.assertEqual(release["blocked_bout_indices"], [])
        self.assertEqual(release["review_flags"], {0: [], 1: []})

    def test_mixed(self):
        reviewable = [make_reviewable("E2", 0, 0, "Bout 1", "E2_delivery_0", "A", "B")]
        blocked = [make_blocked("E2", 1, "fighters_invalid")]
        review_flags = {0: [], 1: ["fighters_invalid"]}
        bundle = make_operator_review("E2", reviewable, blocked, review_flags)
        release = publication_release_pack(bundle)
        self.assertEqual(release["publication_release_status"], "partial")
        self.assertEqual(len(release["release_ready_exports"]), 1)
        self.assertEqual(len(release["blocked_releases"]), 1)
        self.assertEqual(release["blocked_releases"][0]["blocker_reason"], "fighters_invalid")
        self.assertEqual(release["release_ready_bout_indices"], [0])
        self.assertEqual(release["blocked_bout_indices"], [1])
        self.assertEqual(release["review_flags"], {0: [], 1: ["fighters_invalid"]})

    def test_fully_blocked(self):
        reviewable = []
        blocked = [make_blocked("E3", 0, "fighters_invalid"), make_blocked("E3", 1, "fighters_invalid")]
        review_flags = {0: ["fighters_invalid"], 1: ["fighters_invalid"]}
        bundle = make_operator_review("E3", reviewable, blocked, review_flags)
        release = publication_release_pack(bundle)
        self.assertEqual(release["publication_release_status"], "blocked")
        self.assertEqual(len(release["release_ready_exports"]), 0)
        self.assertEqual(len(release["blocked_releases"]), 2)
        for b in release["blocked_releases"]:
            self.assertEqual(b["release_status"], "blocked")
            self.assertIn("blocker_reason", b)
        self.assertEqual(release["release_ready_bout_indices"], [])
        self.assertEqual(release["blocked_bout_indices"], [0, 1])
        self.assertEqual(release["review_flags"], {0: ["fighters_invalid"], 1: ["fighters_invalid"]})

    def test_stable_ordering(self):
        reviewable = [
            make_reviewable("E4", 1, 1, "Bout 2", "E4_delivery_1", "C", "D"),
            make_reviewable("E4", 0, 0, "Bout 1", "E4_delivery_0", "A", "B")
        ]
        blocked = [make_blocked("E4", 2, "fighters_invalid")]
        review_flags = {0: [], 1: [], 2: ["fighters_invalid"]}
        bundle = make_operator_review("E4", reviewable, blocked, review_flags)
        release = publication_release_pack(bundle)
        # Should be sorted by publication_order then bout_index
        self.assertEqual([d["bout_index"] for d in release["release_ready_exports"]], [0, 1])
        self.assertEqual([b["bout_index"] for b in release["blocked_releases"]], [2])

    def test_stable_blocker_carry_through(self):
        reviewable = [make_reviewable("E5", 0, 0, "Bout 1", "E5_delivery_0", "A", "B")]
        blocked = [make_blocked("E5", 1, "fighters_invalid")]
        review_flags = {0: [], 1: ["fighters_invalid"]}
        bundle = make_operator_review("E5", reviewable, blocked, review_flags, blocker_summary={1: "fighters_invalid"})
        release = publication_release_pack(bundle)
        self.assertEqual(release["blocker_summary"], {1: "fighters_invalid"})
