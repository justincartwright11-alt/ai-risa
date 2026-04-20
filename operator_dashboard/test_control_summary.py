import unittest
from operator_dashboard.control_summary_utils import aggregate_control_summary

class TestControlSummary(unittest.TestCase):
    def test_contract_shape(self):
        result = aggregate_control_summary()
        self.assertIsInstance(result, dict)
        for key in [
            'ok', 'timestamp', 'total_tracked_events', 'pressure_band_counts',
            'escalation_status_counts', 'review_status_counts', 'briefing_status_counts',
            'top_urgent_events', 'recent_changes', 'summary', 'recommendation', 'errors']:
            self.assertIn(key, result)
    def test_quiet_state(self):
        result = aggregate_control_summary()
        self.assertTrue(result['ok'])
        self.assertIsInstance(result['total_tracked_events'], int)
        self.assertIsInstance(result['pressure_band_counts'], dict)
        self.assertIsInstance(result['top_urgent_events'], list)
        self.assertIsInstance(result['recent_changes'], list)
        self.assertIsInstance(result['errors'], list)
        self.assertIsInstance(result['summary'], str)
        self.assertIsInstance(result['recommendation'], str)
    def test_deterministic_output(self):
        r1 = aggregate_control_summary()
        r2 = aggregate_control_summary()
        self.assertEqual(r1, r2)

if __name__ == '__main__':
    unittest.main()
