import unittest

from operator_dashboard.prf_accuracy_calibration_adapter import (
    build_button3_calibration_review_runtime_fields,
    build_button3_compare_runtime_fields,
    build_button3_confidence_runtime_fields,
    build_button3_summary_runtime_fields,
    build_learning_gate_placeholder,
)


class TestPrfAccuracyCalibrationAdapter(unittest.TestCase):
    def test_learning_gate_placeholder_requires_approval_by_default(self):
        payload = build_learning_gate_placeholder(operator_approval=False)
        self.assertEqual(payload.get("learning_gate_status"), "approval_required")
        self.assertTrue(payload.get("operator_approval_required"))

    def test_compare_runtime_fields_are_additive_and_deterministic(self):
        compare_payload = {
            "result_found": True,
            "score": {
                "segments": {"winner": {"score": 1}},
                "metrics": {
                    "winner_accuracy": 100,
                    "method_accuracy": 0,
                    "round_accuracy": 100,
                    "overall_accuracy": 75,
                },
            },
        }
        runtime = build_button3_compare_runtime_fields(compare_payload)
        self.assertEqual(runtime.get("result_comparison_status"), "compared")
        self.assertTrue(runtime.get("predicted_winner_match"))
        self.assertFalse(runtime.get("method_match"))
        self.assertTrue(runtime.get("round_match"))
        self.assertEqual(runtime.get("overall_report_accuracy_score"), 75.0)

    def test_summary_runtime_fields_emit_accuracy_display_surface(self):
        summary_payload = {
            "compared_results": [{"fight_name": "a_vs_b"}],
            "waiting_for_results": [{"fight_name": "x_vs_y"}],
            "summary_metrics": {"overall_accuracy_pct": 66.67, "total_compared": 1},
        }
        runtime = build_button3_summary_runtime_fields(summary_payload)
        self.assertEqual(runtime.get("result_comparison_status"), "ready")
        self.assertEqual(runtime.get("official_result_source_status"), "mixed")
        section_scores = runtime.get("section_accuracy_scores") or {}
        self.assertIn("fighter_accuracy_pct", section_scores)
        self.assertIn("total_accuracy_pct", section_scores)

    def test_confidence_runtime_fields_produce_proposal_only_recommendations(self):
        calibration_payload = {
            "has_data": True,
            "calibration": [
                {"bucket": "0.61–0.70", "calibration_gap": -0.12},
                {"bucket": "0.71–0.80", "calibration_gap": 0.08},
            ],
        }
        runtime = build_button3_confidence_runtime_fields(calibration_payload)
        recommendations = runtime.get("calibration_recommendations") or []
        self.assertGreaterEqual(len(recommendations), 1)
        self.assertTrue(all(r.get("proposal_only") for r in recommendations))

    def test_calibration_review_runtime_fields_emit_pattern_proposals(self):
        review_payload = {
            "fights_analyzed": 5,
            "proposed_calibrations": [{"field": "confidence"}],
            "miss_patterns": {"method": 2},
        }
        runtime = build_button3_calibration_review_runtime_fields(review_payload)
        self.assertEqual(runtime.get("result_comparison_status"), "ready")
        self.assertEqual(runtime.get("calibration_recommendations"), [{"field": "confidence"}])
        proposals = runtime.get("pattern_memory_update_proposals") or []
        self.assertEqual(len(proposals), 1)
        self.assertTrue(proposals[0].get("proposal_only"))


if __name__ == "__main__":
    unittest.main()
