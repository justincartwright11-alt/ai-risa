"""
test_remediation_outcome_pack.py

Tests for remediation_outcome_pack workflow.
"""
import unittest
from workflows.remediation_outcome_pack import remediation_outcome_pack

class TestRemediationOutcomePack(unittest.TestCase):
    def test_all_completed(self):
        exec_result = {
            "event_name": "eventA",
            "ready_remediation_actions": [
                {
                    "bout_index": 1,
                    "remediation_action": "none",
                    "remediation_reason": "No remediation needed",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "execution_steps": ["verify", "apply_fix", "validate"],
                    "remediation_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "remediation_action": "none",
                    "remediation_reason": "No remediation needed",
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                    "execution_steps": ["verify", "apply_fix", "validate"],
                    "remediation_snapshot": {"snap": 2},
                },
            ],
            "blocked_remediation_actions": []
        }
        result = remediation_outcome_pack(exec_result)
        self.assertEqual(result["remediation_outcome_status"], "ready")
        self.assertEqual(len(result["completed_remediations"]), 2)
        self.assertEqual(result["blocked_remediation_outcomes"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["remediation_outcome_summary"], {"completed_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        exec_result = {
            "event_name": "eventB",
            "ready_remediation_actions": [
                {
                    "bout_index": 1,
                    "remediation_action": "none",
                    "remediation_reason": "No remediation needed",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "execution_steps": ["verify", "apply_fix", "validate"],
                    "remediation_snapshot": {"snap": 1},
                }
            ],
            "blocked_remediation_actions": [
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "remediation_snapshot": {"snap": 2},
                }
            ]
        }
        result = remediation_outcome_pack(exec_result)
        self.assertEqual(result["remediation_outcome_status"], "partial")
        self.assertEqual(len(result["completed_remediations"]), 1)
        self.assertEqual(len(result["blocked_remediation_outcomes"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["remediation_outcome_summary"], {"completed_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        exec_result = {
            "event_name": "eventC",
            "ready_remediation_actions": [],
            "blocked_remediation_actions": [
                {
                    "bout_index": 1,
                    "blocker_reason": "missing data",
                    "remediation_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                    "remediation_snapshot": {"snap": 2},
                },
            ]
        }
        result = remediation_outcome_pack(exec_result)
        self.assertEqual(result["remediation_outcome_status"], "blocked")
        self.assertEqual(len(result["completed_remediations"]), 0)
        self.assertEqual(len(result["blocked_remediation_outcomes"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["remediation_outcome_summary"], {"completed_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
