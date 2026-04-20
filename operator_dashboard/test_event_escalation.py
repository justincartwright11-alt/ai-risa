"""
Test escalation endpoints and contract for Build 14.
"""
import unittest
import operator_dashboard.app as app

class TestEventEscalation(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_escalations_contract(self):
        resp = self.client.get('/api/escalations')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('ok', data)
        self.assertIn('timestamp', data)
        self.assertIn('escalation_count', data)
        self.assertIn('escalations', data)
        self.assertIn('summary', data)
        self.assertIn('recommendation', data)
        self.assertIn('errors', data)
        self.assertIsInstance(data['escalations'], list)
        # If any escalations, check row contract
        if data['escalations']:
            row = data['escalations'][0]
            for k in ['event_id','escalation_score','escalation_level','reasons','queue_status','anomaly_count','watch_score','digest_pressure','last_relevant_timestamp','recommendation','source_layers']:
                self.assertIn(k, row)

    def test_event_escalation_contract_hit_and_miss(self):
        # Try a likely miss
        resp = self.client.get('/api/queue/event/NO_SUCH_EVENT/escalation')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('ok', data)
        self.assertIn('timestamp', data)
        self.assertIn('event_found', data)
        self.assertFalse(data['event_found'])
        self.assertIn('event_id', data)
        self.assertIn('escalation_score', data)
        self.assertIn('escalation_level', data)
        self.assertIn('reasons', data)
        self.assertIn('queue_status', data)
        self.assertIn('anomaly_count', data)
        self.assertIn('watch_score', data)
        self.assertIn('digest_pressure', data)
        self.assertIn('timeline_pressure', data)
        self.assertIn('recommendation', data)
        self.assertIn('errors', data)
        # Try a likely hit if any events exist
        esc = self.client.get('/api/escalations').get_json()
        if esc['escalations']:
            event_id = esc['escalations'][0]['event_id']
            resp2 = self.client.get(f'/api/queue/event/{event_id}/escalation')
            self.assertEqual(resp2.status_code, 200)
            data2 = resp2.get_json()
            self.assertTrue(data2['event_found'])
            self.assertEqual(data2['event_id'], event_id)
            self.assertIn('escalation_score', data2)
            self.assertIn('escalation_level', data2)
            self.assertIn('reasons', data2)
            self.assertIn('queue_status', data2)
            self.assertIn('anomaly_count', data2)
            self.assertIn('watch_score', data2)
            self.assertIn('digest_pressure', data2)
            self.assertIn('timeline_pressure', data2)
            self.assertIn('recommendation', data2)
            self.assertIn('errors', data2)

if __name__ == '__main__':
    unittest.main()
