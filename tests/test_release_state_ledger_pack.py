"""
test_release_state_ledger_pack.py

Tests for release_state_ledger_pack workflow.
"""
import unittest
from workflows.release_state_ledger_pack import release_state_ledger_pack

class TestReleaseStateLedgerPack(unittest.TestCase):
    def test_all_ready(self):
        outcome_result = {
            "event_name": "eventA",
            "completed_actions": [
                {
                    "bout_index": 1,
                    "outcome_status": "completed",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1", "step2"],
                    "session_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "outcome_status": "completed",
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                    "action_sequence": ["stepA"],
                    "session_snapshot": {"snap": 2},
                },
            ],
            "blocked_actions": []
        }
        result = release_state_ledger_pack(outcome_result)
        self.assertEqual(result["release_state_ledger_status"], "ready")
        self.assertEqual(len(result["ledger_entries"]), 2)
        self.assertEqual(result["blocked_ledger_entries"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["release_state_ledger_summary"], {"ledger_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        outcome_result = {
            "event_name": "eventB",
            "completed_actions": [
                {
                    "bout_index": 1,
                    "outcome_status": "completed",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1"],
                    "session_snapshot": {"snap": 1},
                }
            ],
            "blocked_actions": [
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "session_snapshot": {"snap": 2},
                }
            ]
        }
        result = release_state_ledger_pack(outcome_result)
        self.assertEqual(result["release_state_ledger_status"], "partial")
        self.assertEqual(len(result["ledger_entries"]), 1)
        self.assertEqual(len(result["blocked_ledger_entries"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["release_state_ledger_summary"], {"ledger_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        outcome_result = {
            "event_name": "eventC",
            "completed_actions": [],
            "blocked_actions": [
                {
                    "bout_index": 1,
                    "blocker_reason": "missing data",
                    "session_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "session_snapshot": {"snap": 2},
                },
            ]
        }
        result = release_state_ledger_pack(outcome_result)
        self.assertEqual(result["release_state_ledger_status"], "blocked")
        self.assertEqual(len(result["ledger_entries"]), 0)
        self.assertEqual(len(result["blocked_ledger_entries"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["release_state_ledger_summary"], {"ledger_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
