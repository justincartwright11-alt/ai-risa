import unittest
from workflows.coverage_readiness import coverage_readiness
from workflows.report_readiness import report_readiness
from workflows.report_candidate_pack import report_candidate_pack

# Helpers

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

class TestReportCandidatePack(unittest.TestCase):
    def test_fully_ready_event(self):
        event = make_event("E1", [make_bout("A", "B"), make_bout("C", "D")])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        self.assertEqual(pack_summary["reportability_status"], "ready")
        self.assertEqual(pack_summary["ready_report_candidates"], 2)
        self.assertEqual(pack_summary["blocked_report_candidates"], 0)
        self.assertEqual(len(ready), 2)
        self.assertEqual(len(blocked), 0)
        self.assertEqual(pack_summary["ready_bout_indices"], [0, 1])
        self.assertEqual(pack_summary["blocked_bout_indices"], [])
        self.assertEqual(pack_summary["blocker_summary"], [])

    def test_mixed_readiness(self):
        event = make_event("E2", [make_bout("A", "B"), make_bout("", "D", notes=["fighters_invalid"]), make_bout(None, "E", notes=["fighters_invalid"])] )
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        self.assertEqual(pack_summary["reportability_status"], "partial")
        self.assertEqual(pack_summary["ready_report_candidates"], 1)
        self.assertEqual(pack_summary["blocked_report_candidates"], 2)
        self.assertEqual(len(ready), 1)
        self.assertEqual(len(blocked), 2)
        self.assertEqual(pack_summary["ready_bout_indices"], [0])
        self.assertEqual(pack_summary["blocked_bout_indices"], [1, 2])
        self.assertEqual(len(pack_summary["blocker_summary"]), 2)
        self.assertEqual(pack_summary["blocker_summary"][0]["bout_index"], 1)
        self.assertIn("fighters_invalid", pack_summary["blocker_summary"][0]["blocker_reasons"])

    def test_fully_blocked_event(self):
        event = make_event("E3", [make_bout("", None, notes=["fighters_invalid"]), make_bout(None, "", notes=["fighters_invalid"])] )
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        self.assertEqual(pack_summary["reportability_status"], "blocked")
        self.assertEqual(pack_summary["ready_report_candidates"], 0)
        self.assertEqual(pack_summary["blocked_report_candidates"], 2)
        self.assertEqual(len(ready), 0)
        self.assertEqual(len(blocked), 2)
        self.assertEqual(pack_summary["ready_bout_indices"], [])
        self.assertEqual(pack_summary["blocked_bout_indices"], [0, 1])
        self.assertEqual(len(pack_summary["blocker_summary"]), 2)
        self.assertIn("fighters_invalid", pack_summary["blocker_summary"][0]["blocker_reasons"])

    def test_stable_output(self):
        event = make_event("E4", [make_bout("A", "B"), make_bout("", "D", notes=["fighters_invalid"])] )
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack1 = report_candidate_pack(event, readiness)
        pack2 = report_candidate_pack(event, readiness)
        self.assertEqual(pack1, pack2)

if __name__ == "__main__":
    unittest.main()
