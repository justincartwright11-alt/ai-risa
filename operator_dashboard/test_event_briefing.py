"""
Deterministic contract tests for operator briefing endpoints (Build 16).
"""
import unittest
from operator_dashboard.briefing_utils import aggregate_briefing, aggregate_event_briefing

class TestOperatorBriefing(unittest.TestCase):
    def test_briefing_contract(self):
        result = aggregate_briefing()
        self.assertIsInstance(result, dict)
        self.assertTrue('ok' in result)
        self.assertTrue('briefings' in result)
        self.assertTrue('briefing_count' in result)
        self.assertTrue(isinstance(result['briefings'], list))
        for b in result['briefings']:
            self.assertIn('event_id', b)
            self.assertIn('briefing_priority', b)
            self.assertIn('handoff_summary', b)
            self.assertIn('top_reasons', b)
            self.assertIn('escalation_level', b)
            self.assertIn('watch_score', b)
            self.assertIn('digest_pressure', b)
            self.assertIn('anomaly_count', b)
            self.assertIn('queue_status', b)
            self.assertIn('operator_recommendation', b)
            self.assertIn('next_review_note', b)
    def test_event_briefing_contract_found(self):
        # Use a real event_id from the review queue if available
        all_briefings = aggregate_briefing()
        if all_briefings['briefings']:
            event_id = all_briefings['briefings'][0]['event_id']
            result = aggregate_event_briefing(event_id)
            self.assertTrue(result['ok'])
            self.assertTrue(result['event_found'])
            self.assertEqual(result['event_id'], event_id)
            self.assertIn('briefing_priority', result)
            self.assertIn('handoff_summary', result)
            self.assertIn('top_reasons', result)
            self.assertIn('escalation_level', result)
            self.assertIn('watch_score', result)
            self.assertIn('digest_pressure', result)
            self.assertIn('anomaly_count', result)
            self.assertIn('queue_status', result)
            self.assertIn('operator_recommendation', result)
            self.assertIn('next_review_note', result)
    def test_event_briefing_contract_not_found(self):
        result = aggregate_event_briefing('___notarealeventid___')
        self.assertTrue(result['ok'])
        self.assertFalse(result['event_found'])
        self.assertEqual(result['event_id'], '___notarealeventid___')
        self.assertIn('briefing_priority', result)
        self.assertIn('handoff_summary', result)
        self.assertIn('top_reasons', result)
        self.assertIn('escalation_level', result)
        self.assertIn('watch_score', result)
        self.assertIn('digest_pressure', result)
        self.assertIn('anomaly_count', result)
        self.assertIn('queue_status', result)
        self.assertIn('operator_recommendation', result)
        self.assertIn('next_review_note', result)

if __name__ == '__main__':
    unittest.main()
