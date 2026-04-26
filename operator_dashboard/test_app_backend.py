import unittest
from app import app

class DashboardBackendTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AI-RISA Local Operator Dashboard', resp.data)

    def test_run_local_ai_invalid(self):
        resp = self.client.post('/run_local_ai', json={'request_type': 'invalid'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'Invalid request type', resp.data)

    def test_open_file_invalid(self):
        resp = self.client.get('/open_file?file=not_a_file')
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'Invalid file type', resp.data)

    def test_accuracy_comparison_summary_contract(self):
        resp = self.client.get('/api/accuracy/comparison-summary')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('compared_results', data)
        self.assertIn('waiting_for_results', data)
        self.assertIn('summary_metrics', data)
        self.assertIsInstance(data.get('compared_results'), list)
        self.assertIsInstance(data.get('waiting_for_results'), list)
        self.assertIsInstance(data.get('summary_metrics'), dict)

    def test_operator_waiting_queue_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Waiting For Real Results', resp.data)
        self.assertIn(b'/api/accuracy/comparison-summary', resp.data)

    def test_signal_breakdown_contract(self):
        resp = self.client.get('/api/accuracy/signal-breakdown')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('breakdown', data)
        self.assertIn('has_data', data)
        self.assertIsInstance(data.get('breakdown'), list)
        buckets = [b['bucket'] for b in data['breakdown']]
        self.assertIn('0.00–0.10', buckets)
        self.assertIn('0.11–0.20', buckets)
        self.assertIn('0.21–0.30', buckets)
        self.assertIn('0.31+', buckets)

    def test_signal_breakdown_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Signal Gap Accuracy Breakdown', resp.data)
        self.assertIn(b'/api/accuracy/signal-breakdown', resp.data)

if __name__ == '__main__':
    unittest.main()
