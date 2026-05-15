"""Preview-only Gate 1 approval-token validation for Button 1 save-fights candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Dict, List, Mapping, Optional, Tuple

EXPECTED_SOURCE_BUTTON = "button1_find_fights"
EXPECTED_GATE_NAME = "Approve Save Fights"

_MUTATION_GUARD_FIELDS = (
    "mutation_performed",
    "queue_write_performed",
    "database_write_performed",
    "durable_write_performed",
    "report_export_approved",
    "learning_apply_performed",
    "calibration_write_performed",
    "auto_apply_performed",
    "write_authorized",
)


@dataclass
class Gate1ApprovalTokenCheckResult:
    ok: bool
    eligible_for_future_approval: bool
    preview_only: bool = True
    write_authorized: bool = False
    mutation_performed: bool = False
    queue_write_performed: bool = False
    database_write_performed: bool = False
    blocking_reasons: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data["blocking_reasons"] is None:
            data["blocking_reasons"] = []
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


def _has_deterministic_identifier(token_preview: Mapping[str, Any]) -> bool:
    for key in ("token_id", "operation_id", "token"):
        value = token_preview.get(key)
        if isinstance(value, str) and value.strip():
            return True
    return False


def _validate_candidate_scope(token_preview: Mapping[str, Any]) -> Tuple[bool, str]:
    scope = token_preview.get("candidate_scope")
    if scope is None:
        scope = token_preview.get("candidate_ids")
    if scope is None:
        scope = token_preview.get("candidate_keys")

    if scope is None:
        return True, ""

    if isinstance(scope, (list, tuple, dict)):
        return True, ""

    if isinstance(scope, str) and not scope.strip():
        return True, ""

    return False, "candidate scope must be present as list/tuple/dict or safely empty"


def check_gate1_approval_token_preview(
    gate_approval_token_preview: Optional[Mapping[str, Any]],
) -> Gate1ApprovalTokenCheckResult:
    """Validate Gate 1 token preview payload in fail-closed mode with no mutations."""
    blocking_reasons: List[str] = []

    if not isinstance(gate_approval_token_preview, Mapping) or not gate_approval_token_preview:
        blocking_reasons.append("missing gate_approval_token_preview")
        return Gate1ApprovalTokenCheckResult(
            ok=False,
            eligible_for_future_approval=False,
            blocking_reasons=blocking_reasons,
        )

    token_preview = gate_approval_token_preview

    if token_preview.get("source_button") != EXPECTED_SOURCE_BUTTON:
        blocking_reasons.append("source_button must be button1_find_fights")

    if token_preview.get("gate_name") != EXPECTED_GATE_NAME:
        blocking_reasons.append('gate_name must be "Approve Save Fights"')

    if token_preview.get("preview_only") is not True:
        blocking_reasons.append("preview_only must remain true")

    if token_preview.get("write_authorized") is not False:
        blocking_reasons.append("write_authorized must remain false")

    if token_preview.get("queue_write_performed") is not False:
        blocking_reasons.append("queue_write_performed must remain false")

    if token_preview.get("database_write_performed") is not False:
        blocking_reasons.append("database_write_performed must remain false")

    if not _has_deterministic_identifier(token_preview):
        blocking_reasons.append("token must include deterministic token_id, operation_id, or token")

    candidate_scope_ok, candidate_scope_reason = _validate_candidate_scope(token_preview)
    if not candidate_scope_ok:
        blocking_reasons.append(candidate_scope_reason)

    for field_name in _MUTATION_GUARD_FIELDS:
        if field_name in token_preview and token_preview.get(field_name) is True:
            blocking_reasons.append(f"mutating field not allowed: {field_name}")

    ok = len(blocking_reasons) == 0

    return Gate1ApprovalTokenCheckResult(
        ok=ok,
        eligible_for_future_approval=ok,
        blocking_reasons=blocking_reasons,
    )


__all__ = [
    "Gate1ApprovalTokenCheckResult",
    "check_gate1_approval_token_preview",
]
