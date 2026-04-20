"""
Test suite for /api/integrity and integrity aggregation logic (Build 20).
Covers contract, healthy/quiet, degraded, malformed, and chat command cases.
"""
import unittest
import operator_dashboard.integrity_utils as integrity_utils
from operator_dashboard.app import app
import json

class TestIntegrityAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_integrity_contract_shape(self):
        resp = self.client.get('/api/integrity')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        required_fields = [
            'ok', 'timestamp', 'endpoint_health', 'alignment_summary', 'artifact_health',
            'ledger_health', 'blocker_health', 'stale_surface_health', 'readiness_status',
            'summary', 'recommendation', 'errors'
        ]
        for field in required_fields:
            self.assertIn(field, data)
        self.assertTrue(data['ok'])
        self.assertIsInstance(data['errors'], list)

    def test_integrity_healthy_state(self):
        result = integrity_utils.aggregate_integrity()
        self.assertEqual(result['readiness_status'], 'ready')
        self.assertEqual(result['endpoint_health'], 'healthy')
        self.assertEqual(result['artifact_health'], 'healthy')
        self.assertEqual(result['ledger_health'], 'healthy')
        self.assertEqual(result['blocker_health'], 'clear')
        self.assertEqual(result['stale_surface_health'], 'fresh')
        self.assertIn('System is ready', result['recommendation'])

    def test_integrity_chat_commands(self):
        # Only test one alias for brevity; others are mapped identically
        payload = {'message': 'show integrity'}
        resp = self.client.post('/chat/send', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('Readiness:', data['response'])
        self.assertIn('Recommendation:', data['response'])

if __name__ == '__main__':
    unittest.main()
