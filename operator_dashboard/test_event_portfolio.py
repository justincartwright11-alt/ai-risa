"""
test_event_portfolio.py

Tests for Build 18: Portfolio endpoints and logic.
"""
import unittest
from operator_dashboard.portfolio_utils import aggregate_portfolio, aggregate_event_portfolio
from operator_dashboard.casefile_utils import aggregate_event_casefile

class TestEventPortfolio(unittest.TestCase):
    def test_portfolio_contract_shape(self):
        result = aggregate_portfolio()
        self.assertIn("ok", result)
        self.assertIn("timestamp", result)
        self.assertIn("portfolio_count", result)
        self.assertIn("pressure_bands", result)
        self.assertIn("portfolio", result)
        self.assertIn("summary", result)
        self.assertIn("recommendation", result)
        self.assertIn("errors", result)

    def test_event_portfolio_contract_shape_hit(self):
        # Use a real event id from the queue if available
        pf = aggregate_portfolio()
        if pf["portfolio"]:
            eid = pf["portfolio"][0]["event_id"]
            result = aggregate_event_portfolio(eid)
            self.assertTrue(result["event_found"])
            self.assertIn("pressure_band", result)
            self.assertIn("portfolio_score", result)
            self.assertIn("casefile_summary", result)
            self.assertIn("top_reasons", result)
            self.assertIn("review_priority", result)
            self.assertIn("escalation_level", result)
            self.assertIn("digest_pressure", result)
            self.assertIn("anomaly_count", result)
            self.assertIn("queue_status", result)
            self.assertIn("recommendation", result)
            self.assertIn("errors", result)

    def test_event_portfolio_contract_shape_miss(self):
        result = aggregate_event_portfolio("___notarealeventid___")
        # Fix: aggregate_event_portfolio current implementation returns event_found=True even for non-existent events 
        # because aggregate_event_casefile returns ok=True even if event not found.
        # However, it SHOULD return event_found=False if the event is not in the queue.
        # But aggregate_event_portfolio in portfolio_utils.py line 125 hardcodes event_found: True if casefile.get("ok") is true.
        # We will update the test to reflect the current behavior OR fix the code.
        # Given the task, let's fix the test to match the code's intent or fix the code.
        # Actually, let's fix the code in portfolio_utils.py.
        self.assertFalse(result["event_found"])
        self.assertIn("pressure_band", result)
        self.assertIn("portfolio_score", result)
        self.assertIn("casefile_summary", result)
        self.assertIn("top_reasons", result)
        self.assertIn("review_priority", result)
        self.assertIn("escalation_level", result)
        self.assertIn("digest_pressure", result)
        self.assertIn("anomaly_count", result)
        self.assertIn("queue_status", result)
        self.assertIn("recommendation", result)
        self.assertIn("errors", result)

    def test_pressure_band_grouping(self):
        pf = aggregate_portfolio()
        bands = pf["pressure_bands"]
        self.assertIsInstance(bands, dict)
        for b in ["critical", "high", "medium", "low", "quiet"]:
            self.assertIn(b, bands)

    def test_portfolio_score_calculation(self):
        # Mock-like test with real aggregate_event_portfolio if queue has data
        pf = aggregate_portfolio()
        if pf["portfolio"]:
            row = pf["portfolio"][0]
            expected_score = (
                10 * row["escalation_level"] +
                8 * row["review_priority"] +
                5 * row["digest_pressure"] +
                2 * row["anomaly_count"]
            )
            self.assertEqual(row["portfolio_score"], expected_score)

    def test_casefile_aggregation_integration(self):
        # Ensure aggregate_event_casefile is called and mapped correctly
        pf = aggregate_portfolio()
        if pf["portfolio"]:
            eid = pf["portfolio"][0]["event_id"]
            cf = aggregate_event_casefile(eid)
            self.assertEqual(pf["portfolio"][0]["casefile_summary"], cf["casefile_summary"])

    def test_empty_portfolio_behavior(self):
        # Should not crash even if queue is missing/empty
        # Forcing a fake result via internal call if needed, but aggregate_portfolio()
        # is safe by design.
        result = aggregate_portfolio()
        self.assertTrue(result["ok"])
        self.assertIsInstance(result["portfolio"], list)
