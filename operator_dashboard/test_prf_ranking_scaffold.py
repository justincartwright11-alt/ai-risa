import unittest

from operator_dashboard.prf_ranking_scaffold import (
    ANALYSIS_CONFIDENCE,
    BETTING_INTEREST,
    COMMERCIAL_SELLABILITY,
    CUSTOMER_PRIORITY,
    EVENT_CARD_PRIORITY,
    FIGHT_READINESS,
    REPORT_VALUE,
    RANKING_ENGINE_IDS,
    build_button1_ranking_contracts,
    build_ranked_matchup_rows,
    compute_composite_ranking_score,
    validate_ranking_scores,
)


class TestPrfRankingScaffold(unittest.TestCase):
    def test_contracts_cover_all_button1_ranking_engines(self):
        contracts = build_button1_ranking_contracts()
        self.assertEqual(set(contracts.keys()), set(RANKING_ENGINE_IDS))
        self.assertEqual(len(contracts), 7)

    def test_validate_scores_detects_missing_unknown_and_out_of_range(self):
        result = validate_ranking_scores(
            {
                FIGHT_READINESS: 80,
                REPORT_VALUE: 90,
                "ranking.unknown": 10,
                CUSTOMER_PRIORITY: 200,
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn(EVENT_CARD_PRIORITY, result["missing_engines"])
        self.assertIn("ranking.unknown", result["unknown_engines"])
        self.assertIn(CUSTOMER_PRIORITY, result["out_of_range_engines"])

    def test_validate_scores_passes_for_complete_valid_payload(self):
        result = validate_ranking_scores(
            {
                FIGHT_READINESS: 80,
                REPORT_VALUE: 90,
                CUSTOMER_PRIORITY: 70,
                EVENT_CARD_PRIORITY: 60,
                BETTING_INTEREST: 50,
                COMMERCIAL_SELLABILITY: 40,
                ANALYSIS_CONFIDENCE: 75,
            }
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["missing_engines"], [])
        self.assertEqual(result["unknown_engines"], [])
        self.assertEqual(result["out_of_range_engines"], [])

    def test_composite_score_is_deterministic(self):
        score = compute_composite_ranking_score(
            {
                FIGHT_READINESS: 100,
                REPORT_VALUE: 100,
                CUSTOMER_PRIORITY: 100,
                EVENT_CARD_PRIORITY: 100,
                BETTING_INTEREST: 100,
                COMMERCIAL_SELLABILITY: 100,
                ANALYSIS_CONFIDENCE: 100,
            }
        )
        self.assertEqual(score, 100.0)

    def test_ranked_rows_sort_ready_then_composite_then_matchup_id(self):
        rows = [
            {
                "matchup_id": "m2",
                "ranking_scores": {
                    FIGHT_READINESS: 50,
                    REPORT_VALUE: 50,
                    CUSTOMER_PRIORITY: 50,
                    EVENT_CARD_PRIORITY: 50,
                    BETTING_INTEREST: 50,
                    COMMERCIAL_SELLABILITY: 50,
                    ANALYSIS_CONFIDENCE: 50,
                },
            },
            {
                "matchup_id": "m1",
                "ranking_scores": {
                    FIGHT_READINESS: 90,
                    REPORT_VALUE: 90,
                    CUSTOMER_PRIORITY: 90,
                    EVENT_CARD_PRIORITY: 90,
                    BETTING_INTEREST: 90,
                    COMMERCIAL_SELLABILITY: 90,
                    ANALYSIS_CONFIDENCE: 90,
                },
            },
            {
                "matchup_id": "m3",
                "ranking_scores": {
                    FIGHT_READINESS: 90,
                },
            },
        ]

        ranked = build_ranked_matchup_rows(rows)
        self.assertEqual(ranked[0]["matchup_id"], "m1")
        self.assertEqual(ranked[1]["matchup_id"], "m2")
        self.assertEqual(ranked[2]["matchup_id"], "m3")
        self.assertFalse(ranked[2]["rank_ready"])


if __name__ == "__main__":
    unittest.main()
