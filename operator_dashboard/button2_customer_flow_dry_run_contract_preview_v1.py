"""Decision-only dry-run contract for Button 2 customer-flow boundary checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping

from operator_dashboard.button2_pdf_output_root_config_v1 import (
    OutputRootInvalidError,
    OutputRootNotConfiguredError,
    get_pdf_output_root,
)


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _safe_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _safe_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    result: List[str] = []
    for value in values:
        text = _safe_text(value)
        if text:
            result.append(text)
    return result


@dataclass
class Button2CustomerFlowDryRunContractPreviewResult:
    ok: bool
    dry_run: bool = True
    customer_generation_permitted: bool = False
    render_execution_performed: bool = False
    pdf_file_write_performed: bool = False
    delivery_performed: bool = False
    queue_database_write_performed: bool = False
    button1_changed: bool = False
    button3_changed: bool = False
    decision: str = "blocked"
    blocking_reasons: List[str] = None
    readiness_snapshot: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data["blocking_reasons"] is None:
            data["blocking_reasons"] = []
        if data["readiness_snapshot"] is None:
            data["readiness_snapshot"] = {}
        return data


def run_button2_customer_flow_dry_run_contract_preview(request_data: Mapping[str, Any] | None) -> Button2CustomerFlowDryRunContractPreviewResult:
    """Evaluate customer-flow readiness without rendering, writing, or delivery."""
    payload = _safe_dict(request_data)
    if not isinstance(request_data, dict):
        return Button2CustomerFlowDryRunContractPreviewResult(
            ok=False,
            decision="blocked",
            blocking_reasons=[
                "request body must be an object",
                "customer_generation_not_authorized",
                "dry_run_only",
                "operator_gate_required",
                "no_customer_delivery_authority",
                "no_queue_database_write_authority",
            ],
            readiness_snapshot={
                "operator_approved": False,
                "fight_id_present": False,
                "ingest_payload_present": False,
                "render_gate_ready": False,
                "output_root_ready": False,
                "output_root_value": "",
                "output_root_error": "request body must be an object",
            },
        )

    operator_approved = _safe_bool(payload.get("operator_approved"), default=False)
    fight_id = _safe_text(payload.get("fight_id"))
    ingest_payload = payload.get("ingest_payload")
    ingest_payload_present = isinstance(ingest_payload, dict) and bool(ingest_payload)
    render_gate_ready = _safe_bool(payload.get("render_gate_ready"), default=False)

    output_root_ready = False
    output_root_value = ""
    output_root_error = ""
    try:
        output_root_value = get_pdf_output_root()
        output_root_ready = True
    except (OutputRootNotConfiguredError, OutputRootInvalidError) as exc:
        output_root_error = str(exc)

    readiness_snapshot = {
        "operator_approved": operator_approved,
        "fight_id_present": bool(fight_id),
        "fight_id": fight_id,
        "ingest_payload_present": ingest_payload_present,
        "render_gate_ready": render_gate_ready,
        "output_root_ready": output_root_ready,
        "output_root_value": output_root_value,
        "output_root_error": output_root_error,
        "request_flags": {
            "render_gate_ready": render_gate_ready,
            "controlled_non_customer_payload_present": ingest_payload_present,
        },
    }

    blocking_reasons = [
        "customer_generation_not_authorized",
        "dry_run_only",
        "no_customer_delivery_authority",
        "no_queue_database_write_authority",
    ]
    if not operator_approved:
        blocking_reasons.append("operator_gate_required")

    preconditions_met = bool(
        operator_approved
        and fight_id
        and ingest_payload_present
        and render_gate_ready
        and output_root_ready
    )

    decision = "preconditions_validated_readonly" if preconditions_met else "blocked"

    return Button2CustomerFlowDryRunContractPreviewResult(
        ok=True,
        decision=decision,
        blocking_reasons=_safe_list(blocking_reasons),
        readiness_snapshot=readiness_snapshot,
    )


__all__ = [
    "Button2CustomerFlowDryRunContractPreviewResult",
    "run_button2_customer_flow_dry_run_contract_preview",
]