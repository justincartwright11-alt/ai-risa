"""
test_operator_followup_pack.py

Tests for operator_followup_pack workflow.
"""
import unittest
from workflows.operator_followup_pack import operator_followup_pack

class TestOperatorFollowupPack(unittest.TestCase):
    def test_all_ready(self):
        recon_result = {
            "event_name": "eventA",
            "reconciled_entries": [
                {
                    "bout_index": 1,
                    "reconciliation_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                },
                {
                    "bout_index": 2,
                    "reconciliation_status": "ready",
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                },
            ],
            "blocked_reconciliations": []
        }
        result = operator_followup_pack(recon_result)
        self.assertEqual(result["operator_followup_status"], "ready")
        self.assertEqual(len(result["followup_actions"]), 2)
        self.assertEqual(result["blocked_followups"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["operator_followup_summary"], {"followup_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        recon_result = {
            "event_name": "eventB",
            "reconciled_entries": [
                {
                    "bout_index": 1,
                    "reconciliation_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                }
            ],
            "blocked_reconciliations": [
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                }
            ]
        }
        result = operator_followup_pack(recon_result)
        self.assertEqual(result["operator_followup_status"], "partial")
        self.assertEqual(len(result["followup_actions"]), 1)
        self.assertEqual(len(result["blocked_followups"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["operator_followup_summary"], {"followup_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        recon_result = {
            "event_name": "eventC",
            "reconciled_entries": [],
            "blocked_reconciliations": [
                {
                    "bout_index": 1,
                    "blocker_reason": "missing data",
                },
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                },
            ]
        }
        result = operator_followup_pack(recon_result)
        self.assertEqual(result["operator_followup_status"], "blocked")
        self.assertEqual(len(result["followup_actions"]), 0)
        self.assertEqual(len(result["blocked_followups"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["operator_followup_summary"], {"followup_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
