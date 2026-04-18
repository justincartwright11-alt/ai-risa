import unittest
from workflows.coverage_readiness import coverage_readiness
from workflows.report_readiness import report_readiness
from workflows.report_candidate_pack import report_candidate_pack
from workflows.scouting_input_pack import scouting_input_pack
from workflows.bout_dossier_pack import bout_dossier_pack
from workflows.report_brief_pack import report_brief_pack
from workflows.narrative_input_pack import narrative_input_pack

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

class TestNarrativeInputPack(unittest.TestCase):
    def test_fully_ready(self):
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
        self.assertEqual(narrative["narrative_pack_status"], "ready")
        self.assertEqual(narrative["total_bouts"], 2)
        self.assertEqual(len(narrative["ready_narrative_inputs"]), 2)
        self.assertEqual(len(narrative["blocked_narrative_inputs"]), 0)
        for bundle in narrative["ready_narrative_inputs"]:
            self.assertEqual(bundle["narrative_status"], "ready")
            self.assertIn("fighter_a", bundle)
            self.assertIn("fighter_b", bundle)
            self.assertIn("dossier_snapshot", bundle)
            self.assertIn("report_brief_snapshot", bundle)
            self.assertEqual(bundle["event_name"], "E1")
            self.assertEqual(bundle["brief_summary"]["event_name"], "E1")

    def test_mixed_ready_blocked(self):
        event = make_event("E2", [make_bout("A", "B"), make_bout("", "D", notes=["fighters_invalid"]), make_bout(None, "E", notes=["fighters_invalid"])])
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
        self.assertEqual(narrative["narrative_pack_status"], "partial")
        self.assertEqual(narrative["total_bouts"], 3)
        self.assertEqual(len(narrative["ready_narrative_inputs"]), 1)
        self.assertEqual(len(narrative["blocked_narrative_inputs"]), 2)
        # Check ready bundle
        ready_bundle = narrative["ready_narrative_inputs"][0]
        self.assertEqual(ready_bundle["narrative_status"], "ready")
        self.assertEqual(ready_bundle["bout_index"], 0)
        # Check blocked bundles
        for bundle in narrative["blocked_narrative_inputs"]:
            self.assertEqual(bundle["narrative_status"], "blocked")
            self.assertIn(bundle["bout_index"], [1, 2])
            self.assertIn("blocker_reason", bundle)
            self.assertIn("report_brief_snapshot", bundle)

    def test_fully_blocked(self):
        event = make_event("E3", [make_bout("", None, notes=["fighters_invalid"]), make_bout(None, "", notes=["fighters_invalid"])])
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
        self.assertEqual(narrative["narrative_pack_status"], "blocked")
        self.assertEqual(narrative["total_bouts"], 2)
        self.assertEqual(len(narrative["ready_narrative_inputs"]), 0)
        self.assertEqual(len(narrative["blocked_narrative_inputs"]), 2)
        for bundle in narrative["blocked_narrative_inputs"]:
            self.assertEqual(bundle["narrative_status"], "blocked")
            self.assertIn("blocker_reason", bundle)
            self.assertIn("report_brief_snapshot", bundle)

    def test_stable_output(self):
        event = make_event("E4", [make_bout("A", "B"), make_bout("", "D", notes=["fighters_invalid"])])
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
        narrative1 = narrative_input_pack(brief)
        narrative2 = narrative_input_pack(brief)
        self.assertEqual(narrative1, narrative2)

if __name__ == "__main__":
    unittest.main()
