"""
test_execution_outcome_pack.py

Tests for execution_outcome_pack workflow.
"""
import unittest
from workflows.execution_outcome_pack import execution_outcome_pack

class TestExecutionOutcomePack(unittest.TestCase):
    def test_all_completed(self):
        session_result = {
            "event_name": "eventA",
            "ready_session_actions": [
                {
                    "bout_index": 1,
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1", "step2"],
                    "preflight_checks": ["ok"],
                    "runbook_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                    "action_sequence": ["stepA"],
                    "preflight_checks": ["ok"],
                    "runbook_snapshot": {"snap": 2},
                },
            ],
            "blocked_session_actions": []
        }
        result = execution_outcome_pack(session_result)
        self.assertEqual(result["execution_outcome_status"], "ready")
        self.assertEqual(len(result["completed_actions"]), 2)
        self.assertEqual(result["blocked_actions"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["execution_outcome_summary"], {"completed_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        session_result = {
            "event_name": "eventB",
            "ready_session_actions": [
                {
                    "bout_index": 1,
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1"],
                    "preflight_checks": ["ok"],
                    "runbook_snapshot": {"snap": 1},
                }
            ],
            "blocked_session_actions": [
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "runbook_snapshot": {"snap": 2},
                }
            ]
        }
        result = execution_outcome_pack(session_result)
        self.assertEqual(result["execution_outcome_status"], "partial")
        self.assertEqual(len(result["completed_actions"]), 1)
        self.assertEqual(len(result["blocked_actions"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["execution_outcome_summary"], {"completed_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        session_result = {
            "event_name": "eventC",
            "ready_session_actions": [],
            "blocked_session_actions": [
                {
                    "bout_index": 1,
                    "blocker_reason": "missing data",
                    "runbook_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "runbook_snapshot": {"snap": 2},
                },
            ]
        }
        result = execution_outcome_pack(session_result)
        self.assertEqual(result["execution_outcome_status"], "blocked")
        self.assertEqual(len(result["completed_actions"]), 0)
        self.assertEqual(len(result["blocked_actions"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["execution_outcome_summary"], {"completed_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
