import unittest

from operator_dashboard.prf_accuracy_calibration_scaffold import (
    ACCURACY_CALIBRATION_ENGINE_IDS,
    ACCURACY_SEGMENT_ENGINE,
    CALIBRATION_RECOMMENDATION_ENGINE,
    OPERATOR_APPROVED_LEARNING_GATE_ENGINE,
    RESULT_COMPARISON_OUTPUT_ENGINE,
    build_accuracy_calibration_contracts,
    evaluate_accuracy_calibration_gate,
    evaluate_operator_learning_gate,
    validate_accuracy_calibration_outputs,
)


class TestPrfAccuracyCalibrationScaffold(unittest.TestCase):
    def test_contracts_cover_requested_button3_scaffold_engines(self):
        contracts = build_accuracy_calibration_contracts()
        self.assertEqual(set(contracts.keys()), set(ACCURACY_CALIBRATION_ENGINE_IDS))
        self.assertEqual(len(contracts), 5)

    def test_validation_detects_missing_required_engines(self):
        validation = validate_accuracy_calibration_outputs({}, operator_approval=True)
        self.assertFalse(validation["ok"])
        self.assertIn(ACCURACY_SEGMENT_ENGINE, validation["missing_required_engines"])
        self.assertIn(RESULT_COMPARISON_OUTPUT_ENGINE, validation["missing_required_engines"])

    def test_validation_detects_approval_gate_violations(self):
        outputs = {
            ACCURACY_SEGMENT_ENGINE: {"accuracy_segment": {"segment": "main"}},
            CALIBRATION_RECOMMENDATION_ENGINE: {"calibration_recommendation": {"action": "tune"}},
            RESULT_COMPARISON_OUTPUT_ENGINE: {"result_comparison_output": {"matched": True}},
            OPERATOR_APPROVED_LEARNING_GATE_ENGINE: {"operator_learning_gate": "approved"},
        }
        validation = validate_accuracy_calibration_outputs(outputs, operator_approval=False)
        self.assertFalse(validation["ok"])
        self.assertIn(CALIBRATION_RECOMMENDATION_ENGINE, validation["approval_gate_violations"])
        self.assertIn(OPERATOR_APPROVED_LEARNING_GATE_ENGINE, validation["approval_gate_violations"])

    def test_operator_learning_gate_contract(self):
        denied = evaluate_operator_learning_gate(False, {"operator_learning_gate": "approved"})
        self.assertFalse(denied["learning_gate_open"])

        allowed = evaluate_operator_learning_gate(True, {"operator_learning_gate": "approved"})
        self.assertTrue(allowed["learning_gate_open"])

    def test_accuracy_calibration_gate_ready_when_all_requirements_met(self):
        outputs = {
            ACCURACY_SEGMENT_ENGINE: {"accuracy_segment": {"segment": "main"}},
            CALIBRATION_RECOMMENDATION_ENGINE: {"calibration_recommendation": {"action": "tune"}},
            RESULT_COMPARISON_OUTPUT_ENGINE: {"result_comparison_output": {"matched": True}},
            OPERATOR_APPROVED_LEARNING_GATE_ENGINE: {"operator_learning_gate": "approved"},
        }
        gate = evaluate_accuracy_calibration_gate(outputs, operator_approval=True)
        self.assertTrue(gate["accuracy_calibration_gate_ready"])
        self.assertEqual(gate["reason_code"], "accuracy_calibration_contracts_validated")


if __name__ == "__main__":
    unittest.main()
