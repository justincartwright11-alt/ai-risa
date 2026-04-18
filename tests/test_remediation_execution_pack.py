"""
test_remediation_execution_pack.py

Tests for remediation_execution_pack workflow.
"""
import unittest
from workflows.remediation_execution_pack import remediation_execution_pack

class TestRemediationExecutionPack(unittest.TestCase):
    def test_all_ready(self):
        plan_result = {
            "event_name": "eventA",
            "remediation_actions": [
                {
                    "bout_index": 1,
                    "remediation_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "remediation_action": "none",
                    "remediation_reason": "No remediation needed",
                },
                {
                    "bout_index": 2,
                    "remediation_status": "ready",
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                    "remediation_action": "none",
                    "remediation_reason": "No remediation needed",
                },
            ],
            "blocked_remediations": []
        }
        result = remediation_execution_pack(plan_result)
        self.assertEqual(result["remediation_execution_status"], "ready")
        self.assertEqual(len(result["ready_remediation_actions"]), 2)
        self.assertEqual(result["blocked_remediation_actions"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["remediation_execution_summary"], {"ready_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        plan_result = {
            "event_name": "eventB",
            "remediation_actions": [
                {
                    "bout_index": 1,
                    "remediation_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "remediation_action": "none",
                    "remediation_reason": "No remediation needed",
                }
            ],
            "blocked_remediations": [
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                }
            ]
        }
        result = remediation_execution_pack(plan_result)
        self.assertEqual(result["remediation_execution_status"], "partial")
        self.assertEqual(len(result["ready_remediation_actions"]), 1)
        self.assertEqual(len(result["blocked_remediation_actions"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["remediation_execution_summary"], {"ready_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        plan_result = {
            "event_name": "eventC",
            "remediation_actions": [],
            "blocked_remediations": [
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
        result = remediation_execution_pack(plan_result)
        self.assertEqual(result["remediation_execution_status"], "blocked")
        self.assertEqual(len(result["ready_remediation_actions"]), 0)
        self.assertEqual(len(result["blocked_remediation_actions"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["remediation_execution_summary"], {"ready_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
