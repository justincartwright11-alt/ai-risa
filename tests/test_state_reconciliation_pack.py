"""
test_state_reconciliation_pack.py

Tests for state_reconciliation_pack workflow.
"""
import unittest
from workflows.state_reconciliation_pack import state_reconciliation_pack

class TestStateReconciliationPack(unittest.TestCase):
    def test_all_ready(self):
        ledger_result = {
            "event_name": "eventA",
            "ledger_entries": [
                {
                    "bout_index": 1,
                    "ledger_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "outcome_status": "completed",
                    "action_sequence": ["step1", "step2"],
                },
                {
                    "bout_index": 2,
                    "ledger_status": "ready",
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                    "outcome_status": "completed",
                    "action_sequence": ["stepA"],
                },
            ],
            "blocked_ledger_entries": []
        }
        result = state_reconciliation_pack(ledger_result)
        self.assertEqual(result["state_reconciliation_status"], "ready")
        self.assertEqual(len(result["reconciled_entries"]), 2)
        self.assertEqual(result["blocked_reconciliations"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["state_reconciliation_summary"], {"reconciled_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        ledger_result = {
            "event_name": "eventB",
            "ledger_entries": [
                {
                    "bout_index": 1,
                    "ledger_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "outcome_status": "completed",
                    "action_sequence": ["step1"],
                }
            ],
            "blocked_ledger_entries": [
                {
                    "bout_index": 2,
                    "ledger_status": "blocked",
                    "blocker_reason": "not approved",
                }
            ]
        }
        result = state_reconciliation_pack(ledger_result)
        self.assertEqual(result["state_reconciliation_status"], "partial")
        self.assertEqual(len(result["reconciled_entries"]), 1)
        self.assertEqual(len(result["blocked_reconciliations"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["state_reconciliation_summary"], {"reconciled_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        ledger_result = {
            "event_name": "eventC",
            "ledger_entries": [],
            "blocked_ledger_entries": [
                {
                    "bout_index": 1,
                    "ledger_status": "blocked",
                    "blocker_reason": "missing data",
                },
                {
                    "bout_index": 2,
                    "ledger_status": "blocked",
                    "blocker_reason": "not approved",
                },
            ]
        }
        result = state_reconciliation_pack(ledger_result)
        self.assertEqual(result["state_reconciliation_status"], "blocked")
        self.assertEqual(len(result["reconciled_entries"]), 0)
        self.assertEqual(len(result["blocked_reconciliations"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["state_reconciliation_summary"], {"reconciled_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
