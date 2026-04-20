import unittest
from operator_dashboard.forecast_utils import get_operator_forecast

class TestForecast(unittest.TestCase):
    def test_forecast_contract_shape(self):
        result = get_operator_forecast()
        self.assertTrue(result["ok"])
        self.assertIn("timestamp", result)
        self.assertIn("forecast_status", result)
        self.assertIn("projected_risk_bands", result)
        self.assertIn("early_warning_items", result)
        self.assertIn("escalation_risk", result)
        self.assertIn("artifact_risk", result)
        self.assertIn("blocker_risk", result)
        self.assertIn("stale_surface_risk", result)
        self.assertIn("urgent_event_forecast", result)
        self.assertIn("summary", result)
        self.assertIn("recommendation", result)
        self.assertIn("errors", result)

    def test_forecast_quiet_state(self):
        result = get_operator_forecast()
        self.assertEqual(result["forecast_status"], "stable")
        self.assertEqual(result["summary"], "No material risk detected.")
        self.assertEqual(result["recommendation"], "No operator action required.")
        self.assertIsInstance(result["early_warning_items"], list)
        self.assertIsInstance(result["urgent_event_forecast"], list)

    # Additional tests for elevated risk, ordering, and error handling can be added as needed

if __name__ == "__main__":
    unittest.main()
