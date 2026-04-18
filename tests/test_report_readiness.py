import unittest
from workflows.coverage_readiness import coverage_readiness
from workflows.report_readiness import report_readiness

def make_bout(a, b):
    return {"fighter_a": a, "fighter_b": b}

def make_event(event_name, bouts):
    return {
        "event_name": event_name,
        "discovered_bout_slots": bouts
    }

class TestReportReadiness(unittest.TestCase):
    def test_fully_ready_event(self):
        event = make_event("E1", [make_bout("A", "B"), make_bout("C", "D")])
        coverage = coverage_readiness(event)
        result = report_readiness(coverage)
        self.assertEqual(result["reportability_status"], "ready")
        self.assertEqual(result["report_ready_bouts"], 2)
        self.assertEqual(result["report_blocked_bouts"], 0)
        self.assertEqual(result["report_ready_indices"], [0, 1])
        self.assertEqual(result["report_blocked_indices"], [])
        self.assertEqual(result["fighter_gap_candidate_count"], 0)
        self.assertEqual(result["report_readiness_summary"]["has_blocked_bouts"], False)
        self.assertEqual(result["report_readiness_summary"]["has_ready_bouts"], True)

    def test_mixed_readiness(self):
        event = make_event("E2", [make_bout("A", "B"), make_bout("", "D"), make_bout(None, "E")])
        coverage = coverage_readiness(event)
        result = report_readiness(coverage)
        self.assertEqual(result["reportability_status"], "partial")
        self.assertEqual(result["report_ready_bouts"], 1)
        self.assertEqual(result["report_blocked_bouts"], 2)
        self.assertEqual(result["report_ready_indices"], [0])
        self.assertEqual(result["report_blocked_indices"], [1, 2])
        self.assertEqual(result["fighter_gap_candidate_count"], 2)
        self.assertEqual(result["report_readiness_summary"]["has_blocked_bouts"], True)
        self.assertEqual(result["report_readiness_summary"]["has_ready_bouts"], True)

    def test_fully_blocked_event(self):
        event = make_event("E3", [make_bout("", None), make_bout(None, "")])
        coverage = coverage_readiness(event)
        result = report_readiness(coverage)
        self.assertEqual(result["reportability_status"], "blocked")
        self.assertEqual(result["report_ready_bouts"], 0)
        self.assertEqual(result["report_blocked_bouts"], 2)
        self.assertEqual(result["report_ready_indices"], [])
        self.assertEqual(result["report_blocked_indices"], [0, 1])
        self.assertEqual(result["fighter_gap_candidate_count"], 2)
        self.assertEqual(result["report_readiness_summary"]["has_blocked_bouts"], True)
        self.assertEqual(result["report_readiness_summary"]["has_ready_bouts"], False)

    def test_stable_output(self):
        event = make_event("E4", [make_bout("A", "B"), make_bout("", "D")])
        coverage = coverage_readiness(event)
        result1 = report_readiness(coverage)
        result2 = report_readiness(coverage)
        self.assertEqual(result1, result2)

if __name__ == "__main__":
    unittest.main()
