import unittest
from workflows.delivery_bundle_pack import delivery_bundle_pack
from workflows.export_bundle_pack import export_bundle_pack

def make_delivery_bundle(event_name, deliverable, blocked):
    # Minimal deterministic delivery_bundle_pack_result
    return {
        "event_name": event_name,
        "delivery_bundle_status": (
            "ready" if blocked == [] else ("blocked" if deliverable == [] else "partial")
        ),
        "deliverable_reports": deliverable,
        "blocked_deliverables": blocked,
        "deliverable_bout_indices": [d["bout_index"] for d in deliverable],
        "blocked_bout_indices": [b["bout_index"] for b in blocked],
        "blocker_summary": {b["bout_index"]: b.get("blocker_reason", "") for b in blocked},
        "delivery_bundle_summary": {
            "event_name": event_name,
            "delivery_bundle_status": (
                "ready" if blocked == [] else ("blocked" if deliverable == [] else "partial")
            ),
            "deliverable_count": len(deliverable),
            "blocked_count": len(blocked)
        }
    }

def make_deliverable(event_name, bout_index, order, label, key, a, b, extra=None):
    d = {
        "event_name": event_name,
        "bout_index": bout_index,
        "delivery_status": "deliverable",
        "delivery_key": key,
        "publication_label": label,
        "publication_order": order,
        "fighter_a": a,
        "fighter_b": b,
        "weight_class": "LW",
        "scheduled_rounds": 3,
        "is_title_fight": False,
        "release_snapshot": {"sections": {"main": "report"}},
        "manifest_snapshot": {"audit_summary": {"score": 99}}
    }
    if extra:
        d.update(extra)
    return d

def make_blocked(event_name, bout_index, reason):
    return {
        "event_name": event_name,
        "bout_index": bout_index,
        "delivery_status": "blocked",
        "blocker_reason": reason,
        "release_snapshot": {"sections": {"main": "blocked"}}
    }

class TestExportBundlePack(unittest.TestCase):
    def test_fully_deliverable(self):
        deliverable = [
            make_deliverable("E1", 0, 0, "Bout 1", "E1_delivery_0", "A", "B"),
            make_deliverable("E1", 1, 1, "Bout 2", "E1_delivery_1", "C", "D")
        ]
        blocked = []
        bundle = make_delivery_bundle("E1", deliverable, blocked)
        export = export_bundle_pack(bundle)
        self.assertEqual(export["export_bundle_status"], "ready")
        self.assertEqual(export["total_bouts"], 2)
        self.assertEqual(len(export["deliverable_exports"]), 2)
        self.assertEqual(len(export["blocked_exports"]), 0)
        for i, d in enumerate(export["deliverable_exports"]):
            self.assertEqual(d["export_status"], "deliverable")
            self.assertEqual(d["bout_index"], i)
            self.assertIn("export_payload", d)
            self.assertEqual(d["export_payload"]["metadata"]["delivery_key"], d["delivery_key"])
            self.assertIn("release_sections", d["export_payload"])
            self.assertIn("audit_summary", d["export_payload"])
            self.assertEqual(d["delivery_snapshot"], deliverable[i]["release_snapshot"])
        manifest = export["export_manifest"]
        self.assertEqual(manifest["deliverable_count"], 2)
        self.assertEqual(manifest["blocked_count"], 0)
        self.assertEqual(manifest["deliverable_bout_indices"], [0, 1])
        self.assertEqual(manifest["blocked_bout_indices"], [])
        self.assertEqual(manifest["publication_labels"], ["Bout 1", "Bout 2"])
        self.assertEqual(manifest["delivery_keys"], ["E1_delivery_0", "E1_delivery_1"])

    def test_mixed(self):
        deliverable = [make_deliverable("E2", 0, 0, "Bout 1", "E2_delivery_0", "A", "B")]
        blocked = [make_blocked("E2", 1, "fighters_invalid")]
        bundle = make_delivery_bundle("E2", deliverable, blocked)
        export = export_bundle_pack(bundle)
        self.assertEqual(export["export_bundle_status"], "partial")
        self.assertEqual(export["total_bouts"], 2)
        self.assertEqual(len(export["deliverable_exports"]), 1)
        self.assertEqual(len(export["blocked_exports"]), 1)
        self.assertEqual(export["blocked_exports"][0]["blocker_reason"], "fighters_invalid")
        self.assertEqual(export["blocked_exports"][0]["delivery_snapshot"], {"sections": {"main": "blocked"}})
        manifest = export["export_manifest"]
        self.assertEqual(manifest["deliverable_count"], 1)
        self.assertEqual(manifest["blocked_count"], 1)
        self.assertEqual(manifest["deliverable_bout_indices"], [0])
        self.assertEqual(manifest["blocked_bout_indices"], [1])
        self.assertEqual(manifest["publication_labels"], ["Bout 1"])
        self.assertEqual(manifest["delivery_keys"], ["E2_delivery_0"])

    def test_fully_blocked(self):
        deliverable = []
        blocked = [make_blocked("E3", 0, "fighters_invalid"), make_blocked("E3", 1, "fighters_invalid")]
        bundle = make_delivery_bundle("E3", deliverable, blocked)
        export = export_bundle_pack(bundle)
        self.assertEqual(export["export_bundle_status"], "blocked")
        self.assertEqual(export["total_bouts"], 2)
        self.assertEqual(len(export["deliverable_exports"]), 0)
        self.assertEqual(len(export["blocked_exports"]), 2)
        for b in export["blocked_exports"]:
            self.assertEqual(b["export_status"], "blocked")
            self.assertIn("blocker_reason", b)
            self.assertIn("delivery_snapshot", b)
        manifest = export["export_manifest"]
        self.assertEqual(manifest["deliverable_count"], 0)
        self.assertEqual(manifest["blocked_count"], 2)
        self.assertEqual(manifest["deliverable_bout_indices"], [])
        self.assertEqual(manifest["blocked_bout_indices"], [0, 1])
        self.assertEqual(manifest["publication_labels"], [])
        self.assertEqual(manifest["delivery_keys"], [])

    def test_stable_ordering(self):
        deliverable = [
            make_deliverable("E4", 1, 1, "Bout 2", "E4_delivery_1", "C", "D"),
            make_deliverable("E4", 0, 0, "Bout 1", "E4_delivery_0", "A", "B")
        ]
        blocked = [make_blocked("E4", 2, "fighters_invalid")]
        bundle = make_delivery_bundle("E4", deliverable, blocked)
        export = export_bundle_pack(bundle)
        # Should be sorted by publication_order then bout_index
        self.assertEqual([d["bout_index"] for d in export["deliverable_exports"]], [0, 1])
        self.assertEqual([d["publication_order"] for d in export["deliverable_exports"]], [0, 1])
        self.assertEqual([b["bout_index"] for b in export["blocked_exports"]], [2])

    def test_stable_blocker_carry_through(self):
        deliverable = [make_deliverable("E5", 0, 0, "Bout 1", "E5_delivery_0", "A", "B")]
        blocked = [make_blocked("E5", 1, "fighters_invalid")]
        bundle = make_delivery_bundle("E5", deliverable, blocked)
        export = export_bundle_pack(bundle)
        self.assertEqual(export["blocker_summary"], {1: "fighters_invalid"})
