"""
Premium Report Factory Button 3 accuracy/calibration scaffold contracts.

Defines contract-only structures for accuracy segment, calibration
recommendation, pattern memory update, result comparison output, and the
operator-approved learning gate.

No live learning/calibration wiring is executed here.
"""

from dataclasses import dataclass


ACCURACY_SEGMENT_ENGINE = "combat_intelligence.accuracy_segment"
CALIBRATION_RECOMMENDATION_ENGINE = "combat_intelligence.calibration_recommendation"
PATTERN_MEMORY_UPDATE_ENGINE = "combat_intelligence.pattern_memory_update"
RESULT_COMPARISON_OUTPUT_ENGINE = "button3.result_comparison_output"
OPERATOR_APPROVED_LEARNING_GATE_ENGINE = "button3.operator_approved_learning_gate"

ACCURACY_CALIBRATION_ENGINE_IDS = (
    ACCURACY_SEGMENT_ENGINE,
    CALIBRATION_RECOMMENDATION_ENGINE,
    PATTERN_MEMORY_UPDATE_ENGINE,
    RESULT_COMPARISON_OUTPUT_ENGINE,
    OPERATOR_APPROVED_LEARNING_GATE_ENGINE,
)


@dataclass(frozen=True)
class AccuracyCalibrationContract:
    """Contract metadata for one Button 3 accuracy/calibration scaffold output."""

    engine_id: str
    output_key: str
    required: bool
    approval_gate_required: bool


def build_accuracy_calibration_contracts() -> dict[str, AccuracyCalibrationContract]:
    """Return contract-only definitions for Button 3 scaffold engines."""

    return {
        ACCURACY_SEGMENT_ENGINE: AccuracyCalibrationContract(
            ACCURACY_SEGMENT_ENGINE,
            "accuracy_segment",
            True,
            False,
        ),
        CALIBRATION_RECOMMENDATION_ENGINE: AccuracyCalibrationContract(
            CALIBRATION_RECOMMENDATION_ENGINE,
            "calibration_recommendation",
            True,
            True,
        ),
        PATTERN_MEMORY_UPDATE_ENGINE: AccuracyCalibrationContract(
            PATTERN_MEMORY_UPDATE_ENGINE,
            "pattern_memory_update",
            False,
            True,
        ),
        RESULT_COMPARISON_OUTPUT_ENGINE: AccuracyCalibrationContract(
            RESULT_COMPARISON_OUTPUT_ENGINE,
            "result_comparison_output",
            True,
            False,
        ),
        OPERATOR_APPROVED_LEARNING_GATE_ENGINE: AccuracyCalibrationContract(
            OPERATOR_APPROVED_LEARNING_GATE_ENGINE,
            "operator_learning_gate",
            True,
            True,
        ),
    }


def _is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list, tuple, set)):
        return len(value) > 0
    return True


def validate_accuracy_calibration_outputs(
    engine_outputs: dict,
    operator_approval: bool,
    contracts: dict[str, AccuracyCalibrationContract] | None = None,
) -> dict:
    """Validate required contract outputs and approval-gate constraints."""

    rules = contracts or build_accuracy_calibration_contracts()
    missing_required_engines = []
    missing_required_output_values = []
    unknown_engines = []
    approval_gate_violations = []

    for engine_id, contract in rules.items():
        if contract.required and engine_id not in engine_outputs:
            missing_required_engines.append(engine_id)

    for engine_id, payload in engine_outputs.items():
        contract = rules.get(engine_id)
        if contract is None:
            unknown_engines.append(engine_id)
            continue

        if contract.required:
            value = payload.get(contract.output_key) if isinstance(payload, dict) else None
            if not _is_present(value):
                missing_required_output_values.append(contract.output_key)

        if contract.approval_gate_required and not operator_approval:
            approval_gate_violations.append(engine_id)

    ok = (
        not missing_required_engines
        and not missing_required_output_values
        and not unknown_engines
        and not approval_gate_violations
    )
    return {
        "ok": ok,
        "missing_required_engines": sorted(missing_required_engines),
        "missing_required_output_values": sorted(missing_required_output_values),
        "unknown_engines": sorted(unknown_engines),
        "approval_gate_violations": sorted(approval_gate_violations),
    }


def evaluate_operator_learning_gate(
    operator_approval: bool,
    gate_payload: dict,
) -> dict:
    """Evaluate contract-level operator-approved learning gate status."""

    allowed = bool(operator_approval and str(gate_payload.get("operator_learning_gate") or "").strip().lower() == "approved")
    if allowed:
        return {
            "learning_gate_open": True,
            "reason_code": "operator_approved_learning_gate_open",
        }

    return {
        "learning_gate_open": False,
        "reason_code": "operator_approval_required_for_learning",
    }


def evaluate_accuracy_calibration_gate(
    engine_outputs: dict,
    operator_approval: bool,
    contracts: dict[str, AccuracyCalibrationContract] | None = None,
) -> dict:
    """Evaluate contract-level Button 3 accuracy/calibration gate readiness."""

    validation = validate_accuracy_calibration_outputs(
        engine_outputs=engine_outputs,
        operator_approval=operator_approval,
        contracts=contracts,
    )

    learning_payload = engine_outputs.get(OPERATOR_APPROVED_LEARNING_GATE_ENGINE) or {}
    learning_gate = evaluate_operator_learning_gate(operator_approval, learning_payload)

    if validation["ok"] and learning_gate["learning_gate_open"]:
        return {
            "accuracy_calibration_gate_ready": True,
            "reason_code": "accuracy_calibration_contracts_validated",
            "validation": validation,
            "learning_gate": learning_gate,
        }

    reason_code = (
        "operator_approval_required"
        if not operator_approval
        else "missing_required_accuracy_calibration_contract_outputs"
    )
    return {
        "accuracy_calibration_gate_ready": False,
        "reason_code": reason_code,
        "validation": validation,
        "learning_gate": learning_gate,
    }
