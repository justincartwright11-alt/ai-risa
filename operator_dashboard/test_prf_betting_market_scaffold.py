import unittest

from operator_dashboard.prf_betting_market_scaffold import (
    BETTING_ENGINE_IDS,
    BETTING_RISK_DISCLAIMER,
    FAIR_PRICE,
    IMPLIED_PROBABILITY,
    MARKET_EDGE,
    ODDS_INGESTION,
    PASS_NO_BET,
    VOLATILITY_GRADE,
    build_betting_market_contracts,
    evaluate_betting_output_gate,
    validate_betting_outputs,
)


class TestPrfBettingMarketScaffold(unittest.TestCase):
    def test_contracts_cover_required_betting_engines(self):
        contracts = build_betting_market_contracts()
        self.assertEqual(set(contracts.keys()), set(BETTING_ENGINE_IDS))
        self.assertEqual(len(contracts), 8)

    def test_validate_betting_outputs_detects_missing_required_engines(self):
        validation = validate_betting_outputs({})
        self.assertFalse(validation["ok"])
        self.assertIn(ODDS_INGESTION, validation["missing_required_engines"])
        self.assertIn(PASS_NO_BET, validation["missing_required_engines"])

    def test_validate_betting_outputs_detects_empty_required_values(self):
        outputs = {
            ODDS_INGESTION: {"odds_snapshot": {}},
            IMPLIED_PROBABILITY: {"implied_probability": None},
            FAIR_PRICE: {"fair_price": ""},
            MARKET_EDGE: {"market_edge": ""},
            VOLATILITY_GRADE: {"volatility_grade": "high"},
            PASS_NO_BET: {"pass_no_bet_condition": ""},
            BETTING_RISK_DISCLAIMER: {"betting_risk_disclaimer": ""},
        }
        validation = validate_betting_outputs(outputs)
        self.assertFalse(validation["ok"])
        self.assertIn("implied_probability", validation["missing_required_output_values"])
        self.assertIn("pass_no_bet_condition", validation["missing_required_output_values"])

    def test_evaluate_betting_output_gate_passes_when_required_outputs_present(self):
        outputs = {
            ODDS_INGESTION: {"odds_snapshot": {"book": "sample", "price": "+120"}},
            IMPLIED_PROBABILITY: {"implied_probability": 0.47},
            FAIR_PRICE: {"fair_price": "+113"},
            MARKET_EDGE: {"market_edge": 0.03},
            VOLATILITY_GRADE: {"volatility_grade": "medium"},
            PASS_NO_BET: {"pass_no_bet_condition": "pass"},
            BETTING_RISK_DISCLAIMER: {"betting_risk_disclaimer": "For informational use only."},
        }
        gate = evaluate_betting_output_gate(outputs)
        self.assertTrue(gate["betting_gate_ready"])
        self.assertEqual(gate["reason_code"], "required_betting_contract_outputs_present")

    def test_evaluate_betting_output_gate_blocks_with_unknown_engine(self):
        outputs = {
            ODDS_INGESTION: {"odds_snapshot": {"book": "sample", "price": "+120"}},
            IMPLIED_PROBABILITY: {"implied_probability": 0.47},
            FAIR_PRICE: {"fair_price": "+113"},
            MARKET_EDGE: {"market_edge": 0.03},
            VOLATILITY_GRADE: {"volatility_grade": "medium"},
            PASS_NO_BET: {"pass_no_bet_condition": "no_bet"},
            BETTING_RISK_DISCLAIMER: {"betting_risk_disclaimer": "For informational use only."},
            "betting.unknown": {"foo": "bar"},
        }
        gate = evaluate_betting_output_gate(outputs)
        self.assertFalse(gate["betting_gate_ready"])
        self.assertIn("betting.unknown", gate["validation"]["unknown_engines"])


if __name__ == "__main__":
    unittest.main()
