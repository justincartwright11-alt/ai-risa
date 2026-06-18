"""Button 1 provider adapter execution gate scaffold (preview-only).

This module evaluates allow/deny gate decisions without executing providers,
calling sources, scraping, writing queue/database rows, or promoting to Button 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


ALLOWED_SOURCE_BUTTON = "button1_find_fights"


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_bool(value: Any) -> bool:
    return bool(value)


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _add_diag(diagnostics: List[str], reason: str) -> None:
    if reason and reason not in diagnostics:
        diagnostics.append(reason)


def evaluate_button1_provider_adapter_execution_gate(
    request: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Evaluate gate decision in preview-only scaffold mode.

    Default posture is deny. Even when an allow decision is produced for preview,
    all execution/network/write/promotion flags remain false.
    """

    req = _safe_dict(request)
    diagnostics: List[str] = []

    source_button = _safe_text(req.get("source_button"))
    provider_id = _safe_text(req.get("provider_id"))
    operator_approval_token = _safe_text(req.get("operator_approval_token"))
    provider_enabled = _safe_bool(req.get("provider_enabled"))
    enable_preview_allow_decision = _safe_bool(req.get("enable_preview_allow_decision"))

    if not source_button:
        _add_diag(diagnostics, "execution_gate_missing_source_button")
    elif source_button != ALLOWED_SOURCE_BUTTON:
        _add_diag(diagnostics, "execution_gate_invalid_source_button")

    if not provider_id:
        _add_diag(diagnostics, "execution_gate_missing_provider_id")

    if not operator_approval_token:
        _add_diag(diagnostics, "execution_gate_operator_approval_missing")

    if not provider_enabled:
        _add_diag(diagnostics, "execution_gate_provider_not_enabled")

    checked = True
    allowed = False

    # Preview-only scaffold branch to exercise allow/deny payload shape.
    # This does not execute anything and keeps all side-effect flags false.
    if not diagnostics and enable_preview_allow_decision:
        allowed = True
    elif not diagnostics:
        _add_diag(diagnostics, "execution_gate_scaffold_default_deny")

    decision = "allow" if allowed else "deny"

    return {
        "execution_gate_checked": checked,
        "execution_gate_allowed": allowed,
        "execution_gate_decision": decision,
        "execution_gate_reason_codes": diagnostics,
        "source_button": source_button,
        "provider_id": provider_id,
        "operator_approval_required": True,
        "preview_only": True,
        "decision_timestamp_utc": _now_utc_iso(),
        "provider_execution_performed": False,
        "network_calls_performed": False,
        "source_calls_performed": False,
        "scraping_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "button2_promotion_performed": False,
    }


__all__ = [
    "ALLOWED_SOURCE_BUTTON",
    "evaluate_button1_provider_adapter_execution_gate",
]
