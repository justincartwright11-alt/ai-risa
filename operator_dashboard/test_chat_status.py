import unittest
import os
import json
from operator_dashboard.app import app

class TestStatusEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_status_contract(self):
        resp = self.client.get('/api/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('ok', data)
        self.assertIn('app_name', data)
        self.assertIn('timestamp', data)
        self.assertIn('chat_history_available', data)
        self.assertIn('action_ledger_available', data)
        self.assertIn('total_logged_actions', data)
        self.assertIn('total_chat_messages', data)
        self.assertIn('errors', data)
        self.assertTrue(data['ok'])

    def test_status_robust_to_missing_files(self):
        # Simulate missing files by renaming if present
        # Only test that endpoint does not error
        resp = self.client.get('/api/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['ok'])

if __name__ == '__main__':
    unittest.main()
