"""
test_operator_execution_session_pack.py

Tests for operator_execution_session_pack workflow.
"""
import unittest
from workflows.operator_execution_session_pack import operator_execution_session_pack

class TestOperatorExecutionSessionPack(unittest.TestCase):
    def test_all_ready(self):
        runbook_result = {
            "event_name": "eventA",
            "ready_release_actions": [
                {
                    "bout_index": 1,
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1", "step2"],
                    "preflight_checks": ["ok"],
                    "release_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                    "action_sequence": ["stepA"],
                    "preflight_checks": ["ok"],
                    "release_snapshot": {"snap": 2},
                },
            ],
            "blocked_release_actions": []
        }
        result = operator_execution_session_pack(runbook_result)
        self.assertEqual(result["execution_session_status"], "ready")
        self.assertEqual(len(result["ready_session_actions"]), 2)
        self.assertEqual(result["blocked_session_actions"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["execution_session_summary"], {"ready_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        runbook_result = {
            "event_name": "eventB",
            "ready_release_actions": [
                {
                    "bout_index": 1,
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1"],
                    "preflight_checks": ["ok"],
                    "release_snapshot": {"snap": 1},
                }
            ],
            "blocked_release_actions": [
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "release_snapshot": {"snap": 2},
                }
            ]
        }
        result = operator_execution_session_pack(runbook_result)
        self.assertEqual(result["execution_session_status"], "partial")
        self.assertEqual(len(result["ready_session_actions"]), 1)
        self.assertEqual(len(result["blocked_session_actions"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["execution_session_summary"], {"ready_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        runbook_result = {
            "event_name": "eventC",
            "ready_release_actions": [],
            "blocked_release_actions": [
                {
                    "bout_index": 1,
                    "blocker_reason": "missing data",
                    "release_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "release_snapshot": {"snap": 2},
                },
            ]
        }
        result = operator_execution_session_pack(runbook_result)
        self.assertEqual(result["execution_session_status"], "blocked")
        self.assertEqual(len(result["ready_session_actions"]), 0)
        self.assertEqual(len(result["blocked_session_actions"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["execution_session_summary"], {"ready_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
