import unittest
from operator_dashboard.review_queue_utils import aggregate_review_queue, aggregate_event_review_queue

class TestReviewQueue(unittest.TestCase):
    def test_review_queue_contract(self):
        result = aggregate_review_queue()
        self.assertTrue(result['ok'])
        self.assertIn('review_queue', result)
        self.assertIn('review_count', result)
        self.assertIsInstance(result['review_queue'], list)
        for row in result['review_queue']:
            self.assertIn('event_id', row)
            self.assertIn('review_score', row)
            self.assertIn('review_priority', row)
            self.assertIn('escalation_level', row)
            self.assertIn('watch_score', row)
            self.assertIn('digest_pressure', row)
            self.assertIn('anomaly_count', row)
            self.assertIn('queue_status', row)
            self.assertIn('last_relevant_timestamp', row)
            self.assertIn('recommendation', row)
            self.assertIn('source_layers', row)
            self.assertIsInstance(row['source_layers'], list)

    def test_event_review_queue_hit_and_miss(self):
        # Try a known event from the review queue
        queue = aggregate_review_queue()['review_queue']
        if queue:
            event_id = queue[0]['event_id']
            result = aggregate_event_review_queue(event_id)
            self.assertTrue(result['ok'])
            self.assertTrue(result['event_found'])
            self.assertEqual(result['event_id'], event_id)
            self.assertIn('review_score', result)
            self.assertIn('review_priority', result)
            self.assertIn('escalation_level', result)
            self.assertIn('watch_score', result)
            self.assertIn('digest_pressure', result)
            self.assertIn('anomaly_count', result)
            self.assertIn('queue_status', result)
            self.assertIn('timeline_pressure', result)
            self.assertIn('last_relevant_timestamp', result)
            self.assertIn('recommendation', result)
            self.assertIn('errors', result)
        # Miss case
        miss = aggregate_event_review_queue('zzz_not_a_real_event')
        self.assertTrue(miss['ok'])
        self.assertFalse(miss['event_found'])
        self.assertEqual(miss['event_id'], 'zzz_not_a_real_event')
        self.assertIn('review_score', miss)
        self.assertIn('review_priority', miss)
        self.assertIn('errors', miss)

if __name__ == '__main__':
    unittest.main()
