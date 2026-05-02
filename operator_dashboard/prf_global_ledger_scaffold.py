"""
Premium Report Factory global database/ledger scaffold contracts.

Defines contract-only structures for global database and ledger engine outputs.
No real database writes, no live ledger wiring, and no runtime route changes.
"""

from dataclasses import dataclass


GLOBAL_FIGHTER_DATABASE = "global_ledger.fighter_database"
GLOBAL_MATCHUP_DATABASE = "global_ledger.matchup_database"
GLOBAL_EVENT_CARD_DATABASE = "global_ledger.event_card_database"
GLOBAL_RESULT_LEDGER = "global_ledger.result_ledger"
GLOBAL_REPORT_LEDGER = "global_ledger.report_ledger"
GLOBAL_ACCURACY_LEDGER = "global_ledger.accuracy_ledger"
GLOBAL_CALIBRATION_LEDGER = "global_ledger.calibration_ledger"
DUPLICATE_CONFLICT_RESOLUTION = "global_ledger.duplicate_conflict_resolution"
SOURCE_PROVENANCE = "global_ledger.source_provenance"

GLOBAL_LEDGER_ENGINE_IDS = (
    GLOBAL_FIGHTER_DATABASE,
    GLOBAL_MATCHUP_DATABASE,
    GLOBAL_EVENT_CARD_DATABASE,
    GLOBAL_RESULT_LEDGER,
    GLOBAL_REPORT_LEDGER,
    GLOBAL_ACCURACY_LEDGER,
    GLOBAL_CALIBRATION_LEDGER,
    DUPLICATE_CONFLICT_RESOLUTION,
    SOURCE_PROVENANCE,
)


@dataclass(frozen=True)
class GlobalLedgerContract:
    """Contract metadata for global database/ledger scaffold outputs."""

    engine_id: str
    output_key: str
    required: bool
    approval_gate_required: bool


def build_global_ledger_contracts() -> dict[str, GlobalLedgerContract]:
    """Return contract-only definitions for global database/ledger engines."""

    return {
        GLOBAL_FIGHTER_DATABASE: GlobalLedgerContract(GLOBAL_FIGHTER_DATABASE, "fighter_record", True, True),
        GLOBAL_MATCHUP_DATABASE: GlobalLedgerContract(GLOBAL_MATCHUP_DATABASE, "matchup_record", True, True),
        GLOBAL_EVENT_CARD_DATABASE: GlobalLedgerContract(GLOBAL_EVENT_CARD_DATABASE, "event_card_record", True, True),
        GLOBAL_RESULT_LEDGER: GlobalLedgerContract(GLOBAL_RESULT_LEDGER, "result_ledger_row", False, True),
        GLOBAL_REPORT_LEDGER: GlobalLedgerContract(GLOBAL_REPORT_LEDGER, "report_ledger_row", True, True),
        GLOBAL_ACCURACY_LEDGER: GlobalLedgerContract(GLOBAL_ACCURACY_LEDGER, "accuracy_ledger_row", False, True),
        GLOBAL_CALIBRATION_LEDGER: GlobalLedgerContract(GLOBAL_CALIBRATION_LEDGER, "calibration_ledger_row", False, True),
        DUPLICATE_CONFLICT_RESOLUTION: GlobalLedgerContract(DUPLICATE_CONFLICT_RESOLUTION, "conflict_resolution", True, True),
        SOURCE_PROVENANCE: GlobalLedgerContract(SOURCE_PROVENANCE, "provenance_refs", True, False),
    }


def _is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list, tuple, set)):
        return len(value) > 0
    return True


def validate_global_ledger_outputs(
    engine_outputs: dict,
    operator_approval: bool,
    contracts: dict[str, GlobalLedgerContract] | None = None,
) -> dict:
    """Validate required contract outputs and approval-gate requirements."""

    rules = contracts or build_global_ledger_contracts()
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


def evaluate_global_ledger_gate(
    engine_outputs: dict,
    operator_approval: bool,
    contracts: dict[str, GlobalLedgerContract] | None = None,
) -> dict:
    """Evaluate contract-level global ledger gate readiness."""

    validation = validate_global_ledger_outputs(
        engine_outputs=engine_outputs,
        operator_approval=operator_approval,
        contracts=contracts,
    )
    if not operator_approval:
        return {
            "global_ledger_gate_ready": False,
            "reason_code": "operator_approval_required",
            "validation": validation,
        }

    if validation["ok"]:
        return {
            "global_ledger_gate_ready": True,
            "reason_code": "global_ledger_contracts_validated",
            "validation": validation,
        }

    reason = "missing_required_global_ledger_contract_outputs"

    return {
        "global_ledger_gate_ready": False,
        "reason_code": reason,
        "validation": validation,
    }
