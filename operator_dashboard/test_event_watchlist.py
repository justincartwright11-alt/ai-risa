import unittest
from operator_dashboard.app import app

class TestEventWatchlist(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_watchlist_contract(self):
        resp = self.client.get('/api/watchlist')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('watchlist', data)
        self.assertIn('watchlist_count', data)
        self.assertIn('summary', data)
        self.assertIn('recommendation', data)
        self.assertIsInstance(data['watchlist'], list)
        # If non-empty, check row contract
        if data['watchlist']:
            row = data['watchlist'][0]
            for k in ['event_id','watch_score','priority','reasons','queue_status','anomaly_count','recent_activity_count','last_relevant_timestamp','recommendation']:
                self.assertIn(k, row)

    def test_event_watchlist_contract_hit_and_miss(self):
        # Try a known event (may be absent if queue is empty)
        resp = self.client.get('/api/watchlist')
        data = resp.get_json()
        event_id = None
        if data['watchlist']:
            event_id = data['watchlist'][0]['event_id']
        if event_id:
            resp2 = self.client.get(f'/api/queue/event/{event_id}/watchlist')
            self.assertEqual(resp2.status_code, 200)
            d2 = resp2.get_json()
            self.assertTrue(d2['ok'])
            self.assertTrue(d2['event_found'])
            self.assertEqual(d2['event_id'], event_id)
            self.assertIn('watch_score', d2)
            self.assertIn('priority', d2)
            self.assertIn('reasons', d2)
        # Miss case
        resp3 = self.client.get('/api/queue/event/zzz/watchlist')
        self.assertEqual(resp3.status_code, 200)
        d3 = resp3.get_json()
        self.assertTrue(d3['ok'])
        self.assertFalse(d3['event_found'])
        self.assertEqual(d3['event_id'], 'zzz')
        self.assertIn('errors', d3)

if __name__ == '__main__':
    unittest.main()
