import unittest

from operator_dashboard.prf_betting_market_adapter import (
    BETTING_RISK_DISCLAIMER_TEXT,
    build_betting_market_enrichment,
)


class TestPrfBettingMarketAdapter(unittest.TestCase):
    def _base_record(self) -> dict:
        return {
            "fighter_a": "Alpha Fighter",
            "fighter_b": "Beta Fighter",
            "confidence": 62,
            "odds_snapshot": {
                "fighter_a_moneyline": -140,
                "fighter_b_moneyline": 120,
            },
            "odds_snapshot_verified": True,
        }

    def test_returns_all_required_additive_fields(self):
        payload = build_betting_market_enrichment(self._base_record(), {}, {})
        for key in (
            "betting_market_status",
            "odds_source_status",
            "implied_probability",
            "fair_price_estimate",
            "market_edge_summary",
            "prop_market_notes",
            "volatility_grade",
            "round_band_betting_path",
            "pass_no_bet_conditions",
            "betting_risk_disclaimer",
            "betting_engine_contributions",
            "betting_missing_inputs",
        ):
            self.assertIn(key, payload)

    def test_missing_odds_degrades_status_to_unavailable(self):
        record = {"fighter_a": "Alpha", "fighter_b": "Beta"}
        payload = build_betting_market_enrichment(record, {}, {})
        self.assertEqual(payload.get("betting_market_status"), "unavailable")
        self.assertIn("odds_snapshot", payload.get("betting_missing_inputs") or [])

    def test_disclaimer_is_always_present(self):
        payload = build_betting_market_enrichment(self._base_record(), {}, {})
        self.assertEqual(payload.get("betting_risk_disclaimer"), BETTING_RISK_DISCLAIMER_TEXT)

    def test_pass_no_bet_conditions_always_present(self):
        payload = build_betting_market_enrichment(self._base_record(), {}, {})
        conditions = payload.get("pass_no_bet_conditions") or []
        self.assertIsInstance(conditions, list)
        self.assertGreater(len(conditions), 0)

    def test_no_guaranteed_profit_language(self):
        payload = build_betting_market_enrichment(self._base_record(), {}, {})
        joined = " ".join([
            str(payload.get("betting_risk_disclaimer") or ""),
            str(payload.get("market_edge_summary") or ""),
            " ".join(payload.get("prop_market_notes") or []),
        ]).lower()
        self.assertNotIn("guaranteed profit", joined)
        self.assertNotIn("guaranteed return", joined)


if __name__ == "__main__":
    unittest.main()
