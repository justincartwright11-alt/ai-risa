"""Button 1 provider adapter execution gate scaffold (preview-only).

This module evaluates allow/deny gate decisions without executing providers,
calling sources, scraping, writing queue/database rows, or promoting to Button 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


ALLOWED_SOURCE_BUTTON = "button1_find_fights"
_APPROVED_PROVIDER_IDS = {"ufc_official_events", "one_fc_official_events"}
_APPROVED_SOURCE_DOMAINS = {
    "ufc_official_events": {"ufc.com", "www.ufc.com", "ufcstats.com", "www.ufcstats.com"},
    "one_fc_official_events": {"onefc.com", "www.onefc.com"},
}
_ALLOWED_HTTP_METHODS = {"GET"}
_SUPPORTED_RESPONSE_TYPES = {"html", "json", "xml", "rss"}
_MAX_RESULT_COUNT_BOUND = 100
_TIMEOUT_SECONDS_BOUND = 60
_REASON_CODE_PRIORITY = (
    "execution_gate_operator_approval_missing",
    "source_call_authorization_missing",
    "max_result_count_unbounded",
    "timeout_unbounded",
    "provenance_required_missing",
    "network_call_not_authorized",
)


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


def _normalized_reason_codes(reason_codes: List[str]) -> List[str]:
    # Keep known blocker codes in a stable order and sort any extras for determinism.
    codes = {code for code in reason_codes if _safe_text(code)}
    ordered = [code for code in _REASON_CODE_PRIORITY if code in codes]
    extras = sorted(code for code in codes if code not in set(_REASON_CODE_PRIORITY))
    return ordered + extras


def _coerce_positive_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text.isdigit():
            return None
        try:
            parsed = int(text)
        except Exception:
            return None
        return parsed if parsed > 0 else None
    return None


def _is_provider_approved(provider_id: str) -> bool:
    return provider_id in _APPROVED_PROVIDER_IDS


def _is_source_domain_authorized(provider_id: str, requested_source_url_or_domain: str) -> bool:
    if not provider_id or provider_id not in _APPROVED_SOURCE_DOMAINS:
        return False
    text = _safe_text(requested_source_url_or_domain).lower()
    if not text:
        return False
    return any(domain in text for domain in _APPROVED_SOURCE_DOMAINS.get(provider_id, set()))


def _is_http_method_authorized(requested_http_method: str) -> bool:
    return _safe_text(requested_http_method).upper() in _ALLOWED_HTTP_METHODS


def _is_response_type_supported(expected_response_type: str) -> bool:
    return _safe_text(expected_response_type).lower() in _SUPPORTED_RESPONSE_TYPES


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
    provider_enabled = _safe_bool(req.get("provider_enabled"))
    enable_preview_allow_decision = _safe_bool(req.get("enable_preview_allow_decision"))

    operator_approval_present = _safe_bool(req.get("operator_approval_present"))
    if not operator_approval_present:
        operator_approval_present = bool(_safe_text(req.get("operator_approval_token")))

    operator_approval_valid = _safe_bool(req.get("operator_approval_valid"))
    if "operator_approval_valid" not in req:
        operator_approval_valid = operator_approval_present and _safe_bool(req.get("token_format_valid"))

    source_call_authorization_present = _safe_bool(req.get("source_call_authorization_present"))
    source_call_authorization_valid = _safe_bool(req.get("source_call_authorization_valid"))
    requested_http_method = _safe_text(req.get("requested_http_method"))
    requested_source_url_or_domain = _safe_text(req.get("requested_source_url_or_domain"))
    expected_response_type = _safe_text(req.get("expected_response_type"))
    max_result_count = _coerce_positive_int(req.get("max_result_count"))
    timeout_seconds = _coerce_positive_int(req.get("timeout_seconds"))
    provenance_required = True if "provenance_required" not in req else _safe_bool(req.get("provenance_required"))
    provenance_complete = _safe_bool(req.get("provenance_complete"))
    save_requested = _safe_bool(req.get("save_requested"))
    customer_output_requested = _safe_bool(req.get("customer_output_requested"))
    learning_update_requested = _safe_bool(req.get("learning_update_requested"))
    button2_promotion_requested = _safe_bool(req.get("button2_promotion_requested"))
    token_secret_exposed = _safe_bool(req.get("token_secret_exposed")) or bool(_safe_text(req.get("token_secret")))

    if not source_button:
        _add_diag(diagnostics, "execution_gate_missing_source_button")
    elif source_button != ALLOWED_SOURCE_BUTTON:
        _add_diag(diagnostics, "execution_gate_invalid_source_button")

    if not provider_id:
        _add_diag(diagnostics, "execution_gate_missing_provider_id")
    elif not _is_provider_approved(provider_id):
        _add_diag(diagnostics, "provider_id_not_approved")

    if not provider_enabled:
        _add_diag(diagnostics, "execution_gate_provider_not_enabled")
        _add_diag(diagnostics, "provider_execution_not_authorized")

    if not operator_approval_present:
        _add_diag(diagnostics, "execution_gate_operator_approval_missing")
    elif not operator_approval_valid:
        _add_diag(diagnostics, "execution_gate_operator_approval_invalid")

    if not source_call_authorization_present:
        _add_diag(diagnostics, "source_call_authorization_missing")
    elif not source_call_authorization_valid:
        _add_diag(diagnostics, "source_call_authorization_invalid")

    source_domain_authorized = _is_source_domain_authorized(provider_id, requested_source_url_or_domain)
    http_method_authorized = _is_http_method_authorized(requested_http_method)
    response_type_supported = _is_response_type_supported(expected_response_type)

    if requested_source_url_or_domain and not source_domain_authorized:
        _add_diag(diagnostics, "source_domain_not_authorized")
    if requested_http_method and not http_method_authorized:
        _add_diag(diagnostics, "http_method_not_authorized")
    if expected_response_type and not response_type_supported:
        _add_diag(diagnostics, "response_type_not_supported")
    if max_result_count is None or max_result_count > _MAX_RESULT_COUNT_BOUND:
        _add_diag(diagnostics, "max_result_count_unbounded")
    if timeout_seconds is None or timeout_seconds > _TIMEOUT_SECONDS_BOUND:
        _add_diag(diagnostics, "timeout_unbounded")
    if not provenance_required or not provenance_complete:
        _add_diag(diagnostics, "provenance_required_missing")

    if save_requested:
        _add_diag(diagnostics, "save_request_blocked")
    if customer_output_requested:
        _add_diag(diagnostics, "customer_output_request_blocked")
    if button2_promotion_requested:
        _add_diag(diagnostics, "button2_promotion_request_blocked")
    if learning_update_requested:
        _add_diag(diagnostics, "learning_update_request_blocked")
    if token_secret_exposed:
        _add_diag(diagnostics, "token_secret_exposure_blocked")
    if not source_call_authorization_valid:
        _add_diag(diagnostics, "network_call_not_authorized")

    checked = True
    allowed = False

    # Preview-only scaffold branch to exercise allow/deny payload shape.
    # This does not execute anything and keeps all side-effect flags false.
    if not diagnostics and enable_preview_allow_decision:
        allowed = True
    elif not diagnostics:
        _add_diag(diagnostics, "execution_gate_scaffold_default_deny")

    reason_codes = _normalized_reason_codes(diagnostics)
    decision = "allow" if allowed else "deny"
    no_write_flags = {
        "provider_execution_performed": False,
        "network_calls_performed": False,
        "source_calls_performed": False,
        "scraping_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "customer_pdf_generation_performed": False,
        "button2_promotion_performed": False,
        "learning_write_performed": False,
        "calibration_write_performed": False,
        "auto_save_performed": False,
    }

    audit_fields = {
        "provider_enabled": provider_enabled,
        "operator_approval_present": operator_approval_present,
        "operator_approval_valid": operator_approval_valid,
        "source_call_authorization_present": source_call_authorization_present,
        "source_call_authorization_valid": source_call_authorization_valid,
        "source_domain_authorized": source_domain_authorized,
        "http_method_authorized": http_method_authorized,
        "response_type_supported": response_type_supported,
        "provenance_required": provenance_required,
        "provenance_complete": provenance_complete,
        "token_present": operator_approval_present,
        "token_valid": operator_approval_valid,
        "no_write_flags": dict(no_write_flags),
    }

    return {
        "decision": decision,
        "allowed": allowed,
        "reason_codes": reason_codes,
        "execution_gate_checked": checked,
        "execution_gate_allowed": allowed,
        "execution_gate_decision": decision,
        "execution_gate_reason_codes": reason_codes,
        "source_button": source_button,
        "provider_id": provider_id,
        "provider_enabled": provider_enabled,
        "operator_approval_present": operator_approval_present,
        "operator_approval_valid": operator_approval_valid,
        "token_present": operator_approval_present,
        "token_valid": operator_approval_valid,
        "source_call_authorization_present": source_call_authorization_present,
        "source_call_authorization_valid": source_call_authorization_valid,
        "requested_http_method": requested_http_method,
        "requested_source_url_or_domain": requested_source_url_or_domain,
        "expected_response_type": expected_response_type,
        "max_result_count": max_result_count,
        "timeout_seconds": timeout_seconds,
        "source_domain_authorized": source_domain_authorized,
        "http_method_authorized": http_method_authorized,
        "response_type_supported": response_type_supported,
        "provenance_required": provenance_required,
        "provenance_complete": provenance_complete,
        "save_requested": save_requested,
        "customer_output_requested": customer_output_requested,
        "learning_update_requested": learning_update_requested,
        "button2_promotion_requested": button2_promotion_requested,
        "operator_approval_required": True,
        "preview_only": True,
        "decision_timestamp_utc": _now_utc_iso(),
        "audit_fields": audit_fields,
        "no_write_flags": dict(no_write_flags),
        "save_allowed": False,
        "live_save_allowed": False,
        **no_write_flags,
    }


__all__ = [
    "ALLOWED_SOURCE_BUTTON",
    "evaluate_button1_provider_adapter_execution_gate",
]
