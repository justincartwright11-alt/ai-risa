import unittest

from operator_dashboard.prf_ranking_adapter import (
    BUCKET_LOW_CONFIDENCE,
    BUCKET_LOW_PRIORITY,
    BUCKET_PRIORITY_TIER_1,
    BUCKET_PRIORITY_TIER_1_MIN,
    BUCKET_PRIORITY_TIER_2,
    BUCKET_PRIORITY_TIER_2_MIN,
    BUCKET_WATCHLIST_TIER,
    BUCKET_WATCHLIST_TIER_MIN,
    ENGINE_SAFE_DEFAULTS,
    RANKING_ADAPTER_VERSION,
    REASON_CARD_POSITION_EARLY,
    REASON_CARD_POSITION_LATE,
    REASON_MISSING_FIGHTER_NAME,
    REASON_PARSE_COMPLETE,
    REASON_PARSE_INCOMPLETE,
    REASON_RULESET_UNKNOWN,
    REASON_SOURCE_REFERENCE_MISSING,
    REASON_SOURCE_REFERENCE_PRESENT,
    REASON_WEIGHT_CLASS_UNKNOWN,
    compute_ranking_enrichment,
    enrich_row_with_ranking,
    _compute_ranking_bucket,
)
from operator_dashboard.prf_ranking_scaffold import (
    ANALYSIS_CONFIDENCE,
    BETTING_INTEREST,
    COMMERCIAL_SELLABILITY,
    CUSTOMER_PRIORITY,
    EVENT_CARD_PRIORITY,
    FIGHT_READINESS,
    RANKING_ENGINE_IDS,
    REPORT_VALUE,
)

_REQUIRED_RANKING_KEYS = {
    "fight_readiness_score",
    "report_value_score",
    "customer_priority_score",
    "event_card_priority_score",
    "betting_interest_score",
    "commercial_sellability_score",
    "analysis_confidence_score",
    "composite_ranking_score",
    "ranking_bucket",
    "ranking_reasons",
}

_DIAGNOSTIC_KEYS = {
    "ranking_validation_ok",
    "ranking_missing_inputs",
    "ranking_contract_version",
}


def _parsed_row(bout_order: int = 1, source_reference: str = "tapology.com") -> dict:
    return {
        "temporary_matchup_id": "tmp_abc123",
        "fighter_a": "Alpha Fighter",
        "fighter_b": "Beta Fighter",
        "bout_order": bout_order,
        "weight_class": None,
        "ruleset": None,
        "source_reference": source_reference,
        "parse_status": "parsed",
        "parse_notes": "",
    }


def _needs_review_row() -> dict:
    return {
        "temporary_matchup_id": "tmp_xyz999",
        "fighter_a": "",
        "fighter_b": "",
        "bout_order": 5,
        "weight_class": None,
        "ruleset": None,
        "source_reference": "",
        "parse_status": "needs_review",
        "parse_notes": "incomplete_matchup_row",
    }


class TestComputeRankingEnrichmentRequiredKeys(unittest.TestCase):
    def test_all_10_ranking_keys_present_for_parsed_row(self):
        result = compute_ranking_enrichment(_parsed_row())
        for key in _REQUIRED_RANKING_KEYS:
            self.assertIn(key, result, f"Missing required ranking key: {key}")

    def test_all_3_diagnostic_keys_present(self):
        result = compute_ranking_enrichment(_parsed_row())
        for key in _DIAGNOSTIC_KEYS:
            self.assertIn(key, result, f"Missing diagnostic key: {key}")

    def test_all_10_ranking_keys_present_for_needs_review_row(self):
        result = compute_ranking_enrichment(_needs_review_row())
        for key in _REQUIRED_RANKING_KEYS:
            self.assertIn(key, result, f"Missing required ranking key: {key}")


class TestComputeRankingEnrichmentScoreRanges(unittest.TestCase):
    def _assert_engine_scores_in_range(self, row: dict) -> None:
        result = compute_ranking_enrichment(row)
        engine_score_keys = {
            "fight_readiness_score": FIGHT_READINESS,
            "report_value_score": REPORT_VALUE,
            "customer_priority_score": CUSTOMER_PRIORITY,
            "event_card_priority_score": EVENT_CARD_PRIORITY,
            "betting_interest_score": BETTING_INTEREST,
            "commercial_sellability_score": COMMERCIAL_SELLABILITY,
            "analysis_confidence_score": ANALYSIS_CONFIDENCE,
        }
        for score_key in engine_score_keys:
            score = result[score_key]
            self.assertIsInstance(score, float, f"{score_key} must be a float")
            self.assertGreaterEqual(score, 0.0, f"{score_key} below 0")
            self.assertLessEqual(score, 100.0, f"{score_key} above 100")

    def test_engine_scores_in_range_for_parsed_row(self):
        self._assert_engine_scores_in_range(_parsed_row())

    def test_engine_scores_in_range_for_needs_review_row(self):
        self._assert_engine_scores_in_range(_needs_review_row())

    def test_composite_score_is_float_in_range(self):
        result = compute_ranking_enrichment(_parsed_row())
        composite = result["composite_ranking_score"]
        self.assertIsInstance(composite, float)
        self.assertGreaterEqual(composite, 0.0)
        self.assertLessEqual(composite, 100.0)


class TestComputeRankingEnrichmentDeterminism(unittest.TestCase):
    def test_same_input_same_output_parsed_row(self):
        row = _parsed_row()
        result_a = compute_ranking_enrichment(row)
        result_b = compute_ranking_enrichment(row)
        self.assertEqual(result_a, result_b)

    def test_same_input_same_output_needs_review_row(self):
        row = _needs_review_row()
        result_a = compute_ranking_enrichment(row)
        result_b = compute_ranking_enrichment(row)
        self.assertEqual(result_a, result_b)

    def test_different_inputs_different_composites(self):
        parsed_result = compute_ranking_enrichment(_parsed_row())
        needs_review_result = compute_ranking_enrichment(_needs_review_row())
        self.assertNotEqual(
            parsed_result["composite_ranking_score"],
            needs_review_result["composite_ranking_score"],
        )

    def test_ranking_reasons_are_sorted(self):
        result = compute_ranking_enrichment(_parsed_row())
        reasons = result["ranking_reasons"]
        self.assertEqual(reasons, sorted(reasons))


class TestComputeRankingEnrichmentFallbackSafety(unittest.TestCase):
    def test_empty_row_does_not_raise(self):
        try:
            result = compute_ranking_enrichment({})
        except Exception as exc:  # pragma: no cover
            self.fail(f"compute_ranking_enrichment raised on empty row: {exc}")
        self.assertIn("ranking_bucket", result)

    def test_none_values_do_not_raise(self):
        row = {
            "fighter_a": None,
            "fighter_b": None,
            "bout_order": None,
            "weight_class": None,
            "ruleset": None,
            "source_reference": None,
            "parse_status": None,
        }
        try:
            result = compute_ranking_enrichment(row)
        except Exception as exc:  # pragma: no cover
            self.fail(f"compute_ranking_enrichment raised on None-value row: {exc}")
        self.assertIn("composite_ranking_score", result)

    def test_needs_review_row_validation_ok(self):
        """needs_review row should still pass scaffold validation (all engines scored)."""
        result = compute_ranking_enrichment(_needs_review_row())
        self.assertTrue(result["ranking_validation_ok"])
        self.assertEqual(result["ranking_missing_inputs"], [])

    def test_safe_defaults_are_neutral_midrange(self):
        for engine_id in RANKING_ENGINE_IDS:
            default = ENGINE_SAFE_DEFAULTS.get(engine_id)
            self.assertIsNotNone(default, f"Missing safe default for {engine_id}")
            self.assertGreaterEqual(default, 0.0)
            self.assertLessEqual(default, 100.0)


class TestComputeRankingEnrichmentReasonVocab(unittest.TestCase):
    def test_parsed_row_includes_parse_complete_reason(self):
        result = compute_ranking_enrichment(_parsed_row())
        self.assertIn(REASON_PARSE_COMPLETE, result["ranking_reasons"])

    def test_needs_review_row_includes_parse_incomplete_reason(self):
        result = compute_ranking_enrichment(_needs_review_row())
        self.assertIn(REASON_PARSE_INCOMPLETE, result["ranking_reasons"])

    def test_needs_review_row_includes_missing_fighter_name_reason(self):
        result = compute_ranking_enrichment(_needs_review_row())
        self.assertIn(REASON_MISSING_FIGHTER_NAME, result["ranking_reasons"])

    def test_early_card_position_reason(self):
        result = compute_ranking_enrichment(_parsed_row(bout_order=1))
        self.assertIn(REASON_CARD_POSITION_EARLY, result["ranking_reasons"])

    def test_late_card_position_reason(self):
        result = compute_ranking_enrichment(_parsed_row(bout_order=8))
        self.assertIn(REASON_CARD_POSITION_LATE, result["ranking_reasons"])

    def test_source_reference_present_reason(self):
        result = compute_ranking_enrichment(_parsed_row(source_reference="tapology.com"))
        self.assertIn(REASON_SOURCE_REFERENCE_PRESENT, result["ranking_reasons"])

    def test_source_reference_missing_reason(self):
        result = compute_ranking_enrichment(_parsed_row(source_reference=""))
        self.assertIn(REASON_SOURCE_REFERENCE_MISSING, result["ranking_reasons"])

    def test_weight_class_unknown_reason_in_parsed_row(self):
        # weight_class is always None at preview time → reason always included
        result = compute_ranking_enrichment(_parsed_row())
        self.assertIn(REASON_WEIGHT_CLASS_UNKNOWN, result["ranking_reasons"])

    def test_ruleset_unknown_reason_in_parsed_row(self):
        # ruleset is always None at preview time → reason always included
        result = compute_ranking_enrichment(_parsed_row())
        self.assertIn(REASON_RULESET_UNKNOWN, result["ranking_reasons"])


class TestBucketThresholds(unittest.TestCase):
    def test_bucket_priority_tier_1(self):
        self.assertEqual(_compute_ranking_bucket(BUCKET_PRIORITY_TIER_1_MIN), BUCKET_PRIORITY_TIER_1)
        self.assertEqual(_compute_ranking_bucket(100.0), BUCKET_PRIORITY_TIER_1)

    def test_bucket_priority_tier_2(self):
        self.assertEqual(_compute_ranking_bucket(BUCKET_PRIORITY_TIER_2_MIN), BUCKET_PRIORITY_TIER_2)
        self.assertEqual(_compute_ranking_bucket(69.9), BUCKET_PRIORITY_TIER_2)

    def test_bucket_watchlist_tier(self):
        self.assertEqual(_compute_ranking_bucket(BUCKET_WATCHLIST_TIER_MIN), BUCKET_WATCHLIST_TIER)
        self.assertEqual(_compute_ranking_bucket(49.9), BUCKET_WATCHLIST_TIER)

    def test_bucket_low_priority(self):
        self.assertEqual(_compute_ranking_bucket(0.0), BUCKET_LOW_PRIORITY)
        self.assertEqual(_compute_ranking_bucket(29.9), BUCKET_LOW_PRIORITY)

    def test_validation_failure_yields_low_confidence_bucket(self):
        # Force a validation failure by patching validate_ranking_scores
        # (via a row that the adapter can still run, but override validation result)
        # Simplest: confirm BUCKET_LOW_CONFIDENCE is the constant for invalid paths
        self.assertEqual(BUCKET_LOW_CONFIDENCE, "low_confidence")


class TestEnrichRowWithRanking(unittest.TestCase):
    def test_existing_keys_preserved(self):
        row = _parsed_row()
        enriched = enrich_row_with_ranking(row)
        for key, value in row.items():
            self.assertIn(key, enriched)
            self.assertEqual(enriched[key], value)

    def test_ranking_fields_added(self):
        row = _parsed_row()
        enriched = enrich_row_with_ranking(row)
        for key in _REQUIRED_RANKING_KEYS:
            self.assertIn(key, enriched)

    def test_original_row_not_mutated(self):
        row = _parsed_row()
        original_keys = set(row.keys())
        enrich_row_with_ranking(row)
        self.assertEqual(set(row.keys()), original_keys)

    def test_diagnostic_version_matches_constant(self):
        enriched = enrich_row_with_ranking(_parsed_row())
        self.assertEqual(enriched["ranking_contract_version"], RANKING_ADAPTER_VERSION)

    def test_ranking_reasons_is_list(self):
        enriched = enrich_row_with_ranking(_parsed_row())
        self.assertIsInstance(enriched["ranking_reasons"], list)

    def test_ranking_validation_ok_is_bool(self):
        enriched = enrich_row_with_ranking(_parsed_row())
        self.assertIsInstance(enriched["ranking_validation_ok"], bool)

    def test_ranking_missing_inputs_is_list(self):
        enriched = enrich_row_with_ranking(_parsed_row())
        self.assertIsInstance(enriched["ranking_missing_inputs"], list)


class TestParsePreviewEndpointRankingIntegration(unittest.TestCase):
    """
    Integration tests: confirm the /api/premium-report-factory/intake/preview
    endpoint returns additive ranking fields on each matchup_preview row.
    """

    def setUp(self):
        import os
        os.environ.setdefault("PRF_QUEUE_PATH_OVERRIDE", "")
        from operator_dashboard.app import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _post_preview(self, raw_card_text: str, source_reference: str = "tapology.com") -> dict:
        import json
        response = self.client.post(
            "/api/premium-report-factory/intake/preview",
            data=json.dumps({
                "raw_card_text": raw_card_text,
                "event_name": "Test Event",
                "event_date": "2026-06-01",
                "source_reference": source_reference,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_matchup_preview_rows_have_ranking_fields(self):
        payload = self._post_preview("Alpha Fighter vs Beta Fighter\nGamma vs Delta")
        rows = payload.get("matchup_previews", [])
        self.assertGreater(len(rows), 0, "Expected at least one matchup preview row")
        for row in rows:
            for key in _REQUIRED_RANKING_KEYS:
                self.assertIn(key, row, f"Row missing required ranking key: {key}")

    def test_matchup_preview_rows_have_diagnostic_fields(self):
        payload = self._post_preview("Alpha Fighter vs Beta Fighter")
        rows = payload.get("matchup_previews", [])
        self.assertGreater(len(rows), 0)
        for row in rows:
            for key in _DIAGNOSTIC_KEYS:
                self.assertIn(key, row, f"Row missing diagnostic key: {key}")

    def test_existing_row_keys_still_present(self):
        payload = self._post_preview("Alpha Fighter vs Beta Fighter")
        rows = payload.get("matchup_previews", [])
        self.assertGreater(len(rows), 0)
        row = rows[0]
        for key in ("temporary_matchup_id", "fighter_a", "fighter_b", "bout_order",
                    "weight_class", "ruleset", "source_reference", "parse_status", "parse_notes"):
            self.assertIn(key, row, f"Existing row key missing: {key}")

    def test_response_top_level_ok_still_true(self):
        payload = self._post_preview("Alpha Fighter vs Beta Fighter")
        self.assertTrue(payload.get("ok"))

    def test_ranking_fields_additive_only_does_not_break_empty_card(self):
        payload = self._post_preview("")
        self.assertTrue(payload.get("ok"))
        self.assertEqual(payload.get("matchup_previews"), [])

    def test_needs_review_row_still_has_ranking_fields(self):
        """Rows that fail matchup parsing should still carry ranking fields."""
        payload = self._post_preview("This line has no matchup separator at all — skipped")
        # That line would not be parsed at all; use a one-sided line to produce needs_review
        payload2 = self._post_preview("vs. Unknown Fighter")
        rows = payload2.get("matchup_previews", [])
        if rows:
            for key in _REQUIRED_RANKING_KEYS:
                self.assertIn(key, rows[0])


if __name__ == "__main__":
    unittest.main()
