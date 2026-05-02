import unittest

from operator_dashboard.prf_report_readiness_scaffold import (
    ReportReadinessContract,
    SparseCaseCompletionContract,
    detect_missing_required_sections,
    evaluate_sparse_case_completion,
    evaluate_report_readiness_status,
    STATUS_BLOCKED_MISSING_ANALYSIS,
    STATUS_CUSTOMER_READY,
    STATUS_DRAFT_ONLY,
)


class TestPrfReportReadinessScaffold(unittest.TestCase):
    def test_detect_missing_required_sections_flags_unavailable_and_empty(self):
        contract = ReportReadinessContract(required_sections=("headline_prediction", "executive_summary"))
        sections = {
            "headline_prediction": "Prediction unavailable - pending source",
            "executive_summary": "",
        }
        missing = detect_missing_required_sections(sections, contract)
        self.assertEqual(missing, ["headline_prediction", "executive_summary"])

    def test_detect_missing_required_sections_passes_when_content_present(self):
        contract = ReportReadinessContract(required_sections=("headline_prediction", "executive_summary"))
        sections = {
            "headline_prediction": "Projected winner via decision with confidence rationale.",
            "executive_summary": "Control pathway and risk lanes are summarized.",
        }
        missing = detect_missing_required_sections(sections, contract)
        self.assertEqual(missing, [])

    def test_evaluate_sparse_case_completion_requires_five_fields(self):
        contract = SparseCaseCompletionContract()
        payload = {
            "winner": "Alpha",
            "confidence": 0.63,
            "method": "decision",
            "round": "R3",
            "debug_metrics": {"signal_count": 5},
        }
        result = evaluate_sparse_case_completion(payload, contract)
        self.assertTrue(result["ready"])
        self.assertEqual(result["missing_fields"], [])

    def test_sparse_case_completion_reports_missing_fields(self):
        result = evaluate_sparse_case_completion(
            {
                "winner": "Alpha",
                "confidence": None,
                "method": "",
                "round": "R3",
                "debug_metrics": "not-a-dict",
            }
        )
        self.assertFalse(result["ready"])
        self.assertEqual(
            result["missing_fields"],
            ["confidence", "method", "debug_metrics"],
        )

    def test_customer_ready_status_when_requirements_complete(self):
        result = evaluate_report_readiness_status(
            analysis_source_status="found",
            allow_draft=False,
            missing_sections=[],
            sparse_completion_ready=True,
        )
        self.assertEqual(result["report_quality_status"], STATUS_CUSTOMER_READY)
        self.assertTrue(result["customer_ready"])

    def test_blocked_missing_analysis_without_draft(self):
        result = evaluate_report_readiness_status(
            analysis_source_status="not_found",
            allow_draft=False,
            missing_sections=["headline_prediction"],
            sparse_completion_ready=False,
        )
        self.assertEqual(result["report_quality_status"], STATUS_BLOCKED_MISSING_ANALYSIS)
        self.assertFalse(result["customer_ready"])

    def test_draft_only_when_draft_allowed(self):
        result = evaluate_report_readiness_status(
            analysis_source_status="not_found",
            allow_draft=True,
            missing_sections=["headline_prediction"],
            sparse_completion_ready=False,
        )
        self.assertEqual(result["report_quality_status"], STATUS_DRAFT_ONLY)
        self.assertFalse(result["customer_ready"])


if __name__ == "__main__":
    unittest.main()
