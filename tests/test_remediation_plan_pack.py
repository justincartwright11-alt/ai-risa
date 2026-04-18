"""
test_remediation_plan_pack.py

Tests for remediation_plan_pack workflow.
"""
import unittest
from workflows.remediation_plan_pack import remediation_plan_pack

class TestRemediationPlanPack(unittest.TestCase):
    def test_all_ready(self):
        followup_result = {
            "event_name": "eventA",
            "followup_actions": [
                {
                    "bout_index": 1,
                    "followup_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                },
                {
                    "bout_index": 2,
                    "followup_status": "ready",
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                },
            ],
            "blocked_followups": []
        }
        result = remediation_plan_pack(followup_result)
        self.assertEqual(result["remediation_plan_status"], "ready")
        self.assertEqual(len(result["remediation_actions"]), 2)
        self.assertEqual(result["blocked_remediations"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["remediation_plan_summary"], {"remediation_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        followup_result = {
            "event_name": "eventB",
            "followup_actions": [
                {
                    "bout_index": 1,
                    "followup_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                }
            ],
            "blocked_followups": [
                {
                    "bout_index": 2,
                    "blocker_reason": "not approved",
                }
            ]
        }
        result = remediation_plan_pack(followup_result)
        self.assertEqual(result["remediation_plan_status"], "partial")
        self.assertEqual(len(result["remediation_actions"]), 1)
        self.assertEqual(len(result["blocked_remediations"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["remediation_plan_summary"], {"remediation_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        followup_result = {
            "event_name": "eventC",
            "followup_actions": [],
            "blocked_followups": [
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
        result = remediation_plan_pack(followup_result)
        self.assertEqual(result["remediation_plan_status"], "blocked")
        self.assertEqual(len(result["remediation_actions"]), 0)
        self.assertEqual(len(result["blocked_remediations"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["remediation_plan_summary"], {"remediation_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
