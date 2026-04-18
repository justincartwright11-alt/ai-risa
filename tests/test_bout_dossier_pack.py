import unittest
from workflows.coverage_readiness import coverage_readiness
from workflows.report_readiness import report_readiness
from workflows.report_candidate_pack import report_candidate_pack
from workflows.scouting_input_pack import scouting_input_pack
from workflows.bout_dossier_pack import bout_dossier_pack

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

class TestBoutDossierPack(unittest.TestCase):
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
        self.assertEqual(dossier["dossier_pack_status"], "ready")
        self.assertEqual(dossier["total_bouts"], 2)
        self.assertEqual(len(dossier["ready_bout_dossiers"]), 2)
        self.assertEqual(len(dossier["blocked_bout_dossiers"]), 0)
        for d in dossier["ready_bout_dossiers"]:
            self.assertEqual(d["dossier_status"], "ready")
            self.assertIn("fighter_a", d)
            self.assertIn("fighter_b", d)
            self.assertIn("scouting_bundle_snapshot", d)
            self.assertEqual(d["event_name"], "E1")
            self.assertEqual(d["source_summary"]["event_name"], "E1")

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
        self.assertEqual(dossier["dossier_pack_status"], "partial")
        self.assertEqual(dossier["total_bouts"], 3)
        self.assertEqual(len(dossier["ready_bout_dossiers"]), 1)
        self.assertEqual(len(dossier["blocked_bout_dossiers"]), 2)
        # Check ready dossier
        ready_dossier = dossier["ready_bout_dossiers"][0]
        self.assertEqual(ready_dossier["dossier_status"], "ready")
        self.assertEqual(ready_dossier["bout_index"], 0)
        # Check blocked dossiers
        for d in dossier["blocked_bout_dossiers"]:
            self.assertEqual(d["dossier_status"], "blocked")
            self.assertIn(d["bout_index"], [1, 2])
            self.assertIn("blocker_reason", d)
            self.assertIn("scouting_bundle_snapshot", d)

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
        self.assertEqual(dossier["dossier_pack_status"], "blocked")
        self.assertEqual(dossier["total_bouts"], 2)
        self.assertEqual(len(dossier["ready_bout_dossiers"]), 0)
        self.assertEqual(len(dossier["blocked_bout_dossiers"]), 2)
        for d in dossier["blocked_bout_dossiers"]:
            self.assertEqual(d["dossier_status"], "blocked")
            self.assertIn("blocker_reason", d)
            self.assertIn("scouting_bundle_snapshot", d)

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
        dossier1 = bout_dossier_pack(scouting)
        dossier2 = bout_dossier_pack(scouting)
        self.assertEqual(dossier1, dossier2)

if __name__ == "__main__":
    unittest.main()
