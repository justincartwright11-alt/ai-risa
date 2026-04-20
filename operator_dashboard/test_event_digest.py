import unittest
from operator_dashboard.digest_utils import aggregate_digest, aggregate_event_digest

class TestDigestEndpoints(unittest.TestCase):
    def test_digest_contract_shape(self):
        result = aggregate_digest()
        self.assertIn('ok', result)
        self.assertIn('timestamp', result)
        self.assertIn('digest', result)
        self.assertIn('summary', result)
        self.assertIn('recommendation', result)
        self.assertIn('errors', result)

    def test_event_digest_contract_shape_hit(self):
        # Try to find a real event id from the queue
        from operator_dashboard.queue_utils import safe_read_queue
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        if queue_rows:
            event_id = queue_rows[0].get('event_id') or queue_rows[0].get('event_name')
            result = aggregate_event_digest(event_id)
            self.assertIn('ok', result)
            self.assertIn('timestamp', result)
            self.assertIn('event_found', result)
            self.assertIn('event_id', result)
            self.assertIn('watchlist_snapshot', result)
            self.assertIn('anomaly_snapshot', result)
            self.assertIn('timeline_snapshot', result)
            self.assertIn('digest_summary', result)
            self.assertIn('recommendation', result)
            self.assertIn('errors', result)
            self.assertTrue(result['event_found'])
        else:
            self.skipTest('No events in queue to test hit case')

    def test_event_digest_contract_shape_miss(self):
        result = aggregate_event_digest('___nonexistent_event___')
        self.assertIn('ok', result)
        self.assertIn('timestamp', result)
        self.assertIn('event_found', result)
        self.assertFalse(result['event_found'])
        self.assertIn('event_id', result)
        self.assertIn('watchlist_snapshot', result)
        self.assertIn('anomaly_snapshot', result)
        self.assertIn('timeline_snapshot', result)
        self.assertIn('digest_summary', result)
        self.assertIn('recommendation', result)
        self.assertIn('errors', result)

if __name__ == '__main__':
    unittest.main()
