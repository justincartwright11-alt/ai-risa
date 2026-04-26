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

    def test_method_round_breakdown_contract(self):
        resp = self.client.get('/api/accuracy/method-round-breakdown')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('method_accuracy', data)
        self.assertIn('round_accuracy', data)
        self.assertIn('stoppage_propensity_buckets', data)
        self.assertIn('round_finish_tendency_buckets', data)
        m = data['method_accuracy']
        for key in ('total_available', 'method_hits', 'method_misses', 'method_accuracy_pct'):
            self.assertIn(key, m)
        r = data['round_accuracy']
        for key in ('total_available', 'round_hits', 'round_misses', 'round_accuracy_pct'):
            self.assertIn(key, r)
        # Each propensity list should have 4 buckets
        self.assertEqual(len(data['stoppage_propensity_buckets']), 4)
        self.assertEqual(len(data['round_finish_tendency_buckets']), 4)
        buckets = [b['bucket'] for b in data['stoppage_propensity_buckets']]
        for expected in ('0.00–0.25', '0.26–0.50', '0.51–0.75', '0.76–1.00'):
            self.assertIn(expected, buckets)

    def test_method_round_panels_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Method &amp; Round Reliability', resp.data)
        self.assertIn(b'Stoppage / Finish Tendency Accuracy', resp.data)
        self.assertIn(b'/api/accuracy/method-round-breakdown', resp.data)

    def test_confidence_calibration_contract(self):
        resp = self.client.get('/api/accuracy/confidence-calibration')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('calibration', data)
        self.assertIsInstance(data['calibration'], list)
        self.assertEqual(len(data['calibration']), 5)
        buckets = [b['bucket'] for b in data['calibration']]
        for expected in ('0.50–0.60', '0.61–0.70', '0.71–0.80', '0.81–0.90', '0.91–1.00'):
            self.assertIn(expected, buckets)
        for b in data['calibration']:
            for key in ('total_compared', 'predicted_confidence_avg', 'actual_win_rate', 'calibration_gap'):
                self.assertIn(key, b)

    def test_confidence_calibration_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Confidence Calibration', resp.data)
        self.assertIn(b'/api/accuracy/confidence-calibration', resp.data)

    def test_error_patterns_contract(self):
        resp = self.client.get('/api/accuracy/error-patterns')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('total_misses', data)
        self.assertIn('top_failure_patterns', data)
        self.assertIn('miss_breakdowns', data)
        bd = data['miss_breakdowns']
        for key in ('by_signal_gap', 'by_confidence', 'by_method', 'by_round_range'):
            self.assertIn(key, bd)
            self.assertIsInstance(bd[key], list)
        self.assertIsInstance(data['top_failure_patterns'], list)
        self.assertIsInstance(data['total_misses'], int)

    def test_failure_patterns_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Failure Patterns', resp.data)
        self.assertIn(b'/api/accuracy/error-patterns', resp.data)

if __name__ == '__main__':
    unittest.main()
