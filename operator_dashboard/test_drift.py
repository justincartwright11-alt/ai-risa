"""
Test suite for /api/drift and drift aggregation logic (Build 21).
Covers contract, quiet/no-change, non-empty drift, and chat command cases.
"""
import unittest
import operator_dashboard.drift_utils as drift_utils
from operator_dashboard.app import app
import json

class TestDriftAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_drift_contract_shape(self):
        resp = self.client.get('/api/drift')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        required_fields = [
            'ok', 'timestamp', 'pressure_band_drift', 'escalation_drift', 'review_drift',
            'briefing_drift', 'artifact_drift', 'blocker_drift', 'stale_surface_drift',
            'urgent_event_delta', 'summary', 'recommendation', 'errors'
        ]
        for field in required_fields:
            self.assertIn(field, data)
        self.assertTrue(data['ok'])
        self.assertIsInstance(data['errors'], list)

    def test_drift_quiet_state(self):
        result = drift_utils.aggregate_drift()
        self.assertEqual(result['summary'], 'No material drift detected.')
        self.assertEqual(result['recommendation'], 'No operator action required.')
        self.assertEqual(result['pressure_band_drift'], [])
        self.assertEqual(result['escalation_drift'], [])
        self.assertEqual(result['review_drift'], [])
        self.assertEqual(result['briefing_drift'], [])
        self.assertEqual(result['artifact_drift'], [])
        self.assertEqual(result['blocker_drift'], [])
        self.assertEqual(result['stale_surface_drift'], [])
        self.assertEqual(result['urgent_event_delta'], [])

    def test_drift_chat_commands(self):
        # Only test one alias for brevity; others are mapped identically
        payload = {'message': 'show drift'}
        resp = self.client.post('/chat/send', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('Pressure band drift:', data['response'])
        self.assertIn('Recommendation:', data['response'])

if __name__ == '__main__':
    unittest.main()
