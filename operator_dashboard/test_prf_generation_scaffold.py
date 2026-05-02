import unittest

from operator_dashboard.prf_generation_scaffold import (
    CUSTOMER_READY_QA,
    DRAFT_WATERMARK,
    EXPORT_PROOF,
    GENERATION_ENGINE_IDS,
    PREMIUM_PDF_GENERATION,
    SINGLE_MATCHUP_REPORT,
    build_generation_contracts,
    evaluate_generation_gate,
    validate_generation_outputs,
)


class TestPrfGenerationScaffold(unittest.TestCase):
    def test_contracts_cover_expected_generation_engines(self):
        contracts = build_generation_contracts()
        self.assertEqual(set(contracts.keys()), set(GENERATION_ENGINE_IDS))
        self.assertEqual(len(contracts), 12)

    def test_validate_generation_outputs_detects_missing_required(self):
        validation = validate_generation_outputs({})
        self.assertFalse(validation["ok"])
        self.assertIn(PREMIUM_PDF_GENERATION, validation["missing_required_engines"])
        self.assertIn(CUSTOMER_READY_QA, validation["missing_required_engines"])
        self.assertIn(EXPORT_PROOF, validation["missing_required_engines"])

    def test_validate_generation_outputs_detects_empty_required_values(self):
        outputs = {
            PREMIUM_PDF_GENERATION: {"premium_pdf_artifact": ""},
            SINGLE_MATCHUP_REPORT: {"single_matchup_report_artifact": " "},
            CUSTOMER_READY_QA: {"customer_ready_qa_result": ""},
            DRAFT_WATERMARK: {"draft_watermark_result": "applied"},
            EXPORT_PROOF: {"export_proof_record": None},
        }
        validation = validate_generation_outputs(outputs)
        self.assertFalse(validation["ok"])
        self.assertIn("premium_pdf_artifact", validation["missing_required_output_values"])
        self.assertIn("single_matchup_report_artifact", validation["missing_required_output_values"])
        self.assertIn("export_proof_record", validation["missing_required_output_values"])

    def test_generation_gate_customer_ready_when_qa_and_export_pass(self):
        outputs = {
            PREMIUM_PDF_GENERATION: {"premium_pdf_artifact": "report.pdf"},
            SINGLE_MATCHUP_REPORT: {"single_matchup_report_artifact": "single.json"},
            CUSTOMER_READY_QA: {"customer_ready_qa_result": "pass"},
            DRAFT_WATERMARK: {"draft_watermark_result": "not_required"},
            EXPORT_PROOF: {"export_proof_record": {"file": "report.pdf", "sha256": "abc"}},
        }
        gate = evaluate_generation_gate(outputs, allow_draft=False)
        self.assertTrue(gate["generation_gate_ready"])
        self.assertEqual(gate["report_quality_status"], "customer_ready")

    def test_generation_gate_returns_draft_only_when_draft_allowed(self):
        outputs = {
            PREMIUM_PDF_GENERATION: {"premium_pdf_artifact": "report.pdf"},
            SINGLE_MATCHUP_REPORT: {"single_matchup_report_artifact": "single.json"},
            CUSTOMER_READY_QA: {"customer_ready_qa_result": "fail"},
            DRAFT_WATERMARK: {"draft_watermark_result": "applied"},
            EXPORT_PROOF: {"export_proof_record": {"file": "report.pdf", "sha256": "abc"}},
        }
        gate = evaluate_generation_gate(outputs, allow_draft=True)
        self.assertFalse(gate["generation_gate_ready"])
        self.assertEqual(gate["report_quality_status"], "draft_only")


if __name__ == "__main__":
    unittest.main()
