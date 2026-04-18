import unittest
from workflows.coverage_readiness import coverage_readiness
from workflows.report_readiness import report_readiness
from workflows.report_candidate_pack import report_candidate_pack
from workflows.scouting_input_pack import scouting_input_pack
from workflows.bout_dossier_pack import bout_dossier_pack
from workflows.report_brief_pack import report_brief_pack
from workflows.narrative_input_pack import narrative_input_pack
from workflows.report_skeleton_pack import report_skeleton_pack
from workflows.draft_report_pack import draft_report_pack
from workflows.final_report_pack import final_report_pack
from workflows.report_release_pack import report_release_pack
from workflows.publication_manifest_pack import publication_manifest_pack
from workflows.delivery_bundle_pack import delivery_bundle_pack

def make_bout(a, b, notes=None, weight_class=None, scheduled_rounds=None, is_title_fight=None):
    bout = {"fighter_a": a, "fighter_b": b}
    if notes is not None:
        bout["normalization_notes"] = notes
    if weight_class is not None:
        bout["weight_class"] = weight_class
    if scheduled_rounds is not None:
        bout["scheduled_rounds"] = scheduled_rounds
    if is_title_fight is not None:
        bout["is_title_fight"] = is_title_fight
    return bout

def make_event(event_name, bouts):
    return {
        "event_name": event_name,
        "discovered_bout_slots": bouts
    }

class TestDeliveryBundlePack(unittest.TestCase):
    def test_fully_deliverable(self):
        event = make_event("E1", [make_bout("A", "B"), make_bout("C", "D")])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        final = final_report_pack(draft)
        release = report_release_pack(final)
        manifest = publication_manifest_pack(release)
        bundle = delivery_bundle_pack(manifest)
        self.assertEqual(bundle["delivery_bundle_status"], "ready")
        self.assertEqual(bundle["total_bouts"], 2)
        self.assertEqual(len(bundle["deliverable_reports"]), 2)
        self.assertEqual(len(bundle["blocked_deliverables"]), 0)
        for d in bundle["deliverable_reports"]:
            self.assertEqual(d["delivery_status"], "deliverable")
            self.assertIn("fighter_a", d)
            self.assertIn("fighter_b", d)
            self.assertIn("release_snapshot", d)
            self.assertIn("manifest_snapshot", d)
            self.assertIn("delivery_key", d)
            self.assertIn("publication_label", d)
            self.assertIn("publication_order", d)
            self.assertEqual(d["event_name"], "E1")

    def test_mixed_deliverable_blocked(self):
        event = make_event("E2", [
            make_bout("A", "B"),
            make_bout("", "D", notes=["fighters_invalid"]),
            make_bout(None, "E", notes=["fighters_invalid"])
        ])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        final = final_report_pack(draft)
        release = report_release_pack(final)
        manifest = publication_manifest_pack(release)
        bundle = delivery_bundle_pack(manifest)
        self.assertEqual(bundle["delivery_bundle_status"], "partial")
        self.assertEqual(bundle["total_bouts"], 3)
        self.assertEqual(len(bundle["deliverable_reports"]), 1)
        self.assertEqual(len(bundle["blocked_deliverables"]), 2)
        # Deliverable
        deliverable = bundle["deliverable_reports"][0]
        self.assertEqual(deliverable["delivery_status"], "deliverable")
        self.assertEqual(deliverable["bout_index"], 0)
        # Blocked
        for d in bundle["blocked_deliverables"]:
            self.assertEqual(d["delivery_status"], "blocked")
            self.assertIn(d["bout_index"], [1, 2])
            self.assertIn("blocker_reason", d)
            self.assertIn("release_snapshot", d)
            self.assertIn("manifest_snapshot", d)

    def test_fully_blocked(self):
        event = make_event("E3", [
            make_bout("", None, notes=["fighters_invalid"]),
            make_bout(None, "", notes=["fighters_invalid"])
        ])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        final = final_report_pack(draft)
        release = report_release_pack(final)
        manifest = publication_manifest_pack(release)
        bundle = delivery_bundle_pack(manifest)
        self.assertEqual(bundle["delivery_bundle_status"], "blocked")
        self.assertEqual(bundle["total_bouts"], 2)
        self.assertEqual(len(bundle["deliverable_reports"]), 0)
        self.assertEqual(len(bundle["blocked_deliverables"]), 2)
        for d in bundle["blocked_deliverables"]:
            self.assertEqual(d["delivery_status"], "blocked")
            self.assertIn("blocker_reason", d)
            self.assertIn("release_snapshot", d)
            self.assertIn("manifest_snapshot", d)

    def test_stable_publication_order_and_delivery_key(self):
        event = make_event("E4", [make_bout("A", "B"), make_bout("C", "D")])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        final = final_report_pack(draft)
        release = report_release_pack(final)
        manifest = publication_manifest_pack(release)
        bundle = delivery_bundle_pack(manifest)
        keys = [d["delivery_key"] for d in bundle["deliverable_reports"]]
        orders = [d["publication_order"] for d in bundle["deliverable_reports"]]
        self.assertEqual(keys, ["E4_delivery_0", "E4_delivery_1"])
        self.assertEqual(orders, [0, 1])

    def test_stable_blocker_carry_through(self):
        event = make_event("E5", [make_bout("A", "B"), make_bout("", "D", notes=["fighters_invalid"])] )
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        final = final_report_pack(draft)
        release = report_release_pack(final)
        manifest = publication_manifest_pack(release)
        bundle = delivery_bundle_pack(manifest)
        blocked = bundle["blocked_deliverables"][0]
        self.assertEqual(blocked["blocker_reason"], "fighters_invalid")
