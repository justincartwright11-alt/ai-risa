"""
test_release_runbook_pack.py

Tests for release_runbook_pack workflow.
"""
import unittest
from workflows.release_runbook_pack import release_runbook_pack

class TestReleaseRunbookPack(unittest.TestCase):
    def test_all_ready(self):
        pub_result = {
            "event_name": "eventA",
            "release_actions": [
                {
                    "bout_index": 1,
                    "release_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1", "step2"],
                    "preflight_checks": ["ok"],
                    "release_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "release_status": "ready",
                    "delivery_key": "dk2",
                    "publication_label": "label2",
                    "publication_order": 2,
                    "action_sequence": ["stepA"],
                    "preflight_checks": ["ok"],
                    "release_snapshot": {"snap": 2},
                },
            ]
        }
        result = release_runbook_pack(pub_result)
        self.assertEqual(result["release_runbook_status"], "ready")
        self.assertEqual(len(result["ready_release_actions"]), 2)
        self.assertEqual(result["blocked_release_actions"], [])
        self.assertEqual(result["ready_bout_indices"], [1, 2])
        self.assertEqual(result["blocked_bout_indices"], [])
        self.assertEqual(result["release_runbook_summary"], {"ready_count": 2, "blocked_count": 0, "total": 2})

    def test_partial(self):
        pub_result = {
            "event_name": "eventB",
            "release_actions": [
                {
                    "bout_index": 1,
                    "release_status": "ready",
                    "delivery_key": "dk1",
                    "publication_label": "label1",
                    "publication_order": 1,
                    "action_sequence": ["step1"],
                    "preflight_checks": ["ok"],
                    "release_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "release_status": "blocked",
                    "blocker_reason": "not approved",
                    "release_snapshot": {"snap": 2},
                },
            ]
        }
        result = release_runbook_pack(pub_result)
        self.assertEqual(result["release_runbook_status"], "partial")
        self.assertEqual(len(result["ready_release_actions"]), 1)
        self.assertEqual(len(result["blocked_release_actions"]), 1)
        self.assertEqual(result["ready_bout_indices"], [1])
        self.assertEqual(result["blocked_bout_indices"], [2])
        self.assertEqual(result["blocker_summary"], [{"bout_index": 2, "reason": "not approved"}])
        self.assertEqual(result["release_runbook_summary"], {"ready_count": 1, "blocked_count": 1, "total": 2})

    def test_all_blocked(self):
        pub_result = {
            "event_name": "eventC",
            "release_actions": [
                {
                    "bout_index": 1,
                    "release_status": "blocked",
                    "blocker_reason": "missing data",
                    "release_snapshot": {"snap": 1},
                },
                {
                    "bout_index": 2,
                    "release_status": "blocked",
                    "blocker_reason": "not approved",
                    "release_snapshot": {"snap": 2},
                },
            ]
        }
        result = release_runbook_pack(pub_result)
        self.assertEqual(result["release_runbook_status"], "blocked")
        self.assertEqual(len(result["ready_release_actions"]), 0)
        self.assertEqual(len(result["blocked_release_actions"]), 2)
        self.assertEqual(result["ready_bout_indices"], [])
        self.assertEqual(result["blocked_bout_indices"], [1, 2])
        self.assertEqual(result["blocker_summary"], [
            {"bout_index": 1, "reason": "missing data"},
            {"bout_index": 2, "reason": "not approved"},
        ])
        self.assertEqual(result["release_runbook_summary"], {"ready_count": 0, "blocked_count": 2, "total": 2})

if __name__ == "__main__":
    unittest.main()
