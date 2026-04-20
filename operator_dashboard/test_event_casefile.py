"""
Deterministic contract tests for operator casefile endpoint (Build 17).
"""
import unittest
from operator_dashboard.casefile_utils import aggregate_event_casefile

class TestOperatorCasefile(unittest.TestCase):
    def test_casefile_contract_hit(self):
        # Use a real event_id from the queue if available
        from operator_dashboard.queue_utils import safe_read_queue
        queue = safe_read_queue()
        rows = queue.get('rows', [])
        if not rows:
            self.skipTest('No events in queue')
        event_id = rows[0].get('event_id') or rows[0].get('event_name')
        result = aggregate_event_casefile(event_id)
        self.assertIsInstance(result, dict)
        self.assertTrue(result['ok'])
        self.assertTrue(result['event_found'])
        self.assertEqual(result['event_id'], event_id)
        for key in [
            'queue_snapshot', 'evidence_snapshot', 'comparison_snapshot', 'timeline_snapshot',
            'anomaly_snapshot', 'watchlist_snapshot', 'digest_snapshot', 'escalation_snapshot',
            'review_queue_snapshot', 'briefing_snapshot', 'casefile_summary',
            'operator_recommendation', 'next_review_note', 'errors']:
            self.assertIn(key, result)
    def test_casefile_contract_miss(self):
        result = aggregate_event_casefile('___notarealeventid___')
        self.assertIsInstance(result, dict)
        self.assertTrue(result['ok'])
        self.assertFalse(result['event_found'])
        self.assertEqual(result['event_id'], '___notarealeventid___')
        self.assertIn('casefile_summary', result)
        self.assertIn('errors', result)
    def test_casefile_low_pressure(self):
        # Use a real event_id from the queue if available
        from operator_dashboard.queue_utils import safe_read_queue
        queue = safe_read_queue()
        rows = queue.get('rows', [])
        if not rows:
            self.skipTest('No events in queue')
        event_id = rows[0].get('event_id') or rows[0].get('event_name')
        result = aggregate_event_casefile(event_id)
        self.assertTrue(result['event_found'])
        # Should still return a valid casefile even if low pressure
        self.assertIn('casefile_summary', result)
        self.assertIn('operator_recommendation', result)
        self.assertIn('next_review_note', result)

if __name__ == '__main__':
    unittest.main()
