import unittest
from workflows.coverage_readiness import coverage_readiness

def make_bout(a, b):
    return {"fighter_a": a, "fighter_b": b}

def make_event(event_name, bouts):
    return {
        "event_name": event_name,
        "discovered_bout_slots": bouts
    }

class TestCoverageReadiness(unittest.TestCase):
    def test_fully_complete_event(self):
        event = make_event("E1", [make_bout("A", "B"), make_bout("C", "D")])
        result = coverage_readiness(event)
        self.assertEqual(result["readiness_status"], "ready")
        self.assertEqual(result["total_bouts"], 2)
        self.assertEqual(result["complete_bouts"], 2)
        self.assertEqual(result["incomplete_bouts"], 0)
        self.assertEqual(result["fighter_gap_candidate_count"], 0)
        self.assertEqual(result["complete_bout_indices"], [0, 1])
        self.assertEqual(result["incomplete_bout_indices"], [])

    def test_mixed_completeness(self):
        event = make_event("E2", [make_bout("A", "B"), make_bout("", "D"), make_bout(None, "E")])
        result = coverage_readiness(event)
        self.assertEqual(result["readiness_status"], "partial")
        self.assertEqual(result["total_bouts"], 3)
        self.assertEqual(result["complete_bouts"], 1)
        self.assertEqual(result["incomplete_bouts"], 2)
        self.assertEqual(result["fighter_gap_candidate_count"], 2)
        self.assertEqual(result["complete_bout_indices"], [0])
        self.assertEqual(result["incomplete_bout_indices"], [1, 2])
        # Check gap candidates
        gaps = result["fighter_gap_candidates"]
        self.assertEqual(len(gaps), 2)
        self.assertEqual(gaps[0]["missing_side"], "a")
        self.assertEqual(gaps[0]["source_bout_index"], 1)
        self.assertEqual(gaps[1]["missing_side"], "a")
        self.assertEqual(gaps[1]["source_bout_index"], 2)

    def test_all_incomplete(self):
        event = make_event("E3", [make_bout("", None), make_bout(None, "")])
        result = coverage_readiness(event)
        self.assertEqual(result["readiness_status"], "blocked")
        self.assertEqual(result["total_bouts"], 2)
        self.assertEqual(result["complete_bouts"], 0)
        self.assertEqual(result["incomplete_bouts"], 2)
        self.assertEqual(result["fighter_gap_candidate_count"], 2)
        self.assertEqual(result["complete_bout_indices"], [])
        self.assertEqual(result["incomplete_bout_indices"], [0, 1])
        # Both bouts missing 'a'
        for idx, gap in enumerate(result["fighter_gap_candidates"]):
            self.assertEqual(gap["missing_side"], "a")
            self.assertEqual(gap["source_bout_index"], idx)

    def test_stable_output(self):
        event = make_event("E4", [make_bout("A", "B"), make_bout("", "D")])
        result1 = coverage_readiness(event)
        result2 = coverage_readiness(event)
        self.assertEqual(result1, result2)

if __name__ == "__main__":
    unittest.main()
