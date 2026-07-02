"""
button3_result_comparison_preview_v1.py

Preview-only Button 3 result comparison builder.
No apply path, no mutation path, no learning/calibration writes.
"""

from datetime import datetime, timezone
from typing import Any, Dict


_SUPPORTED_STATUSES = {
    "result_found",
    "no_result_found",
    "needs_source",
    "conflict",
    "ready_to_compare",
    "needs_manual_review",
}


_AUTHORIZATION_ALLOWED_COMPARISON_STATUSES = {"ready_to_compare"}

_AUTHORIZATION_REASON_DETAILS = {
    "missing_operator_id": "operator_id is required for apply authorization evaluation",
    "missing_approval_action": "approval_action must be 'apply_official_result'",
    "missing_operation_id": "operation_id or request_id is required",
    "missing_upstream_states": "upstream_states object is required",
    "malformed_upstream_states": "upstream_states must be a JSON object",
    "invalid_approval_state": "approval_state must be one of 'approved', 'expired', 'revoked', or 'replayed'",
    "approval_not_approved": "approval_state must be 'approved'",
    "approval_expired": "approval_state indicates approval has expired",
    "approval_revoked": "approval_state indicates approval has been revoked",
    "approval_replayed": "approval_state indicates approval replay detected",
    "stale_context": "stale_context cannot be true",
    "scope_mismatch": "scope_match must be true",
    "conflict_detected": "conflict_detected cannot be true",
    "source_trust_not_passed": "source_trust_passed must be true",
    "identity_match_not_passed": "identity_match_passed must be true",
    "unknown_state": "unknown_state_detected cannot be true",
    "comparison_status_not_eligible": "comparison_status must be ready_to_compare",
}


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_round(value: Any) -> str:
    cleaned = _clean_str(value)
    if not cleaned:
        return ""
    if cleaned.isdigit():
        return str(int(cleaned))
    return cleaned


def _detect_conflict(payload: Dict[str, Any]) -> bool:
    if bool(payload.get("source_conflict", False)):
        return True

    conflicting_sources = payload.get("conflicting_sources", [])
    if isinstance(conflicting_sources, list) and len(conflicting_sources) > 1:
        winners = set()
        methods = set()
        rounds = set()
        for item in conflicting_sources:
            if not isinstance(item, dict):
                continue
            winner = _clean_str(item.get("actual_winner", ""))
            method = _clean_str(item.get("actual_method", ""))
            round_value = _normalize_round(item.get("actual_round", ""))
            if winner:
                winners.add(winner.lower())
            if method:
                methods.add(method.lower())
            if round_value:
                rounds.add(round_value.lower())
        if len(winners) > 1 or len(methods) > 1 or len(rounds) > 1:
            return True

    return _clean_str(payload.get("comparison_status", "")).lower() == "conflict"


def _has_duplicate_result_evidence(payload: Dict[str, Any]) -> bool:
    conflicting_sources = payload.get("conflicting_sources", [])
    if not isinstance(conflicting_sources, list) or len(conflicting_sources) < 2:
        return False

    seen = set()
    for item in conflicting_sources:
        if not isinstance(item, dict):
            continue
        identity = (
            _clean_str(item.get("actual_winner", "")).lower(),
            _clean_str(item.get("actual_method", "")).lower(),
            _normalize_round(item.get("actual_round", "")).lower(),
        )
        if identity in seen:
            return True
        seen.add(identity)
    return False


def _has_partial_result_evidence(actual_winner: str, actual_method: str, actual_round: str) -> bool:
    fields = [bool(actual_winner), bool(actual_method), bool(actual_round)]
    return any(fields) and not all(fields)


def _has_stale_result_evidence(payload: Dict[str, Any]) -> bool:
    return bool(payload.get("stale_result_evidence", False))


def _resolve_status(payload: Dict[str, Any], result_source_url: str, actual_winner: str, predicted_winner: str) -> str:
    explicit_status = _clean_str(payload.get("comparison_status", "")).lower()
    if explicit_status:
        if explicit_status in _SUPPORTED_STATUSES:
            return explicit_status
        return "needs_manual_review"

    actual_method = _clean_str(payload.get("actual_method", ""))
    actual_round = _normalize_round(payload.get("actual_round", ""))

    if _has_stale_result_evidence(payload):
        return "needs_manual_review"

    if _detect_conflict(payload):
        return "conflict"
    if _has_duplicate_result_evidence(payload):
        return "needs_manual_review"
    if not result_source_url:
        return "needs_source"
    if not actual_winner:
        return "no_result_found"
    if _has_partial_result_evidence(actual_winner, actual_method, actual_round):
        return "needs_manual_review"
    if bool(payload.get("manual_review_candidate", False)):
        return "needs_manual_review"
    if not predicted_winner:
        return "result_found"
    return "ready_to_compare"


def _match_value(predicted: str, actual: str) -> str:
    if not predicted or not actual:
        return "unavailable"
    return "hit" if predicted.lower() == actual.lower() else "miss"


def _build_accuracy_preview(
    comparison_status: str,
    predicted_winner: str,
    predicted_method: str,
    predicted_round: str,
    actual_winner: str,
    actual_method: str,
    actual_round: str,
) -> Dict[str, Any]:
    winner_result = _match_value(predicted_winner, actual_winner)
    method_result = _match_value(predicted_method, actual_method)
    round_result = _match_value(predicted_round, actual_round)

    if comparison_status != "ready_to_compare":
        return {
            "winner": winner_result if comparison_status == "result_found" else "unavailable",
            "method": "unavailable",
            "round": "unavailable",
            "overall": "unavailable",
            "winner_match": winner_result == "hit",
            "method_mismatch": False,
            "round_mismatch": False,
        }

    winner_match = winner_result == "hit"
    method_mismatch = method_result == "miss"
    round_mismatch = round_result == "miss"

    if winner_result == "miss":
        overall = "miss"
    elif method_mismatch or round_mismatch:
        overall = "partial"
    else:
        overall = "hit"

    return {
        "winner": winner_result,
        "method": method_result,
        "round": round_result,
        "overall": overall,
        "winner_match": winner_match,
        "method_mismatch": method_mismatch,
        "round_mismatch": round_mismatch,
    }


def _authorization_deny_payload(
    *,
    reason_code: str,
    operator_id: str,
    approval_action: str,
    operation_id: str,
) -> Dict[str, Any]:
    reason_detail = _AUTHORIZATION_REASON_DETAILS.get(reason_code, "apply authorization denied")
    return {
        "authorization_state": "denied",
        "authorized": False,
        "reason_code": reason_code,
        "reason_detail": reason_detail,
        "operator_id": operator_id,
        "approval_action": approval_action,
        "operation_id": operation_id,
    }


def _evaluate_apply_authorization(
    payload: Dict[str, Any],
    comparison_status: str,
) -> Dict[str, Any]:
    operator_id = _clean_str(payload.get("operator_id", ""))
    approval_action = _clean_str(payload.get("approval_action", ""))
    operation_id = _clean_str(payload.get("operation_id", "")) or _clean_str(payload.get("request_id", ""))

    if not operator_id:
        return _authorization_deny_payload(
            reason_code="missing_operator_id",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if approval_action != "apply_official_result":
        return _authorization_deny_payload(
            reason_code="missing_approval_action",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if not operation_id:
        return _authorization_deny_payload(
            reason_code="missing_operation_id",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )

    upstream_states = payload.get("upstream_states")
    if upstream_states is None:
        return _authorization_deny_payload(
            reason_code="missing_upstream_states",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if not isinstance(upstream_states, dict):
        return _authorization_deny_payload(
            reason_code="malformed_upstream_states",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )

    approval_state = _clean_str(payload.get("approval_state", "")).lower()
    if approval_state not in {"approved", "expired", "revoked", "replayed"}:
        return _authorization_deny_payload(
            reason_code="invalid_approval_state",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if approval_state == "expired":
        return _authorization_deny_payload(
            reason_code="approval_expired",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if approval_state == "revoked":
        return _authorization_deny_payload(
            reason_code="approval_revoked",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if approval_state == "replayed":
        return _authorization_deny_payload(
            reason_code="approval_replayed",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if approval_state != "approved":
        return _authorization_deny_payload(
            reason_code="approval_not_approved",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )

    source_trust_passed = bool(upstream_states.get("source_trust_passed", False))
    identity_match_passed = bool(upstream_states.get("identity_match_passed", False))
    scope_match = bool(upstream_states.get("scope_match", False))
    conflict_detected = bool(upstream_states.get("conflict_detected", False))
    stale_context = bool(upstream_states.get("stale_context", False))
    unknown_state_detected = bool(upstream_states.get("unknown_state_detected", False))

    if not source_trust_passed:
        return _authorization_deny_payload(
            reason_code="source_trust_not_passed",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if not identity_match_passed:
        return _authorization_deny_payload(
            reason_code="identity_match_not_passed",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if stale_context:
        return _authorization_deny_payload(
            reason_code="stale_context",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if conflict_detected:
        return _authorization_deny_payload(
            reason_code="conflict_detected",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if not scope_match:
        return _authorization_deny_payload(
            reason_code="scope_mismatch",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )
    if unknown_state_detected:
        return _authorization_deny_payload(
            reason_code="unknown_state",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )

    if comparison_status not in _AUTHORIZATION_ALLOWED_COMPARISON_STATUSES:
        return _authorization_deny_payload(
            reason_code="comparison_status_not_eligible",
            operator_id=operator_id,
            approval_action=approval_action,
            operation_id=operation_id,
        )

    return {
        "authorization_state": "eligible",
        "authorized": True,
        "reason_code": "eligible",
        "reason_detail": "all deny-first preconditions passed",
        "operator_id": operator_id,
        "approval_action": approval_action,
        "operation_id": operation_id,
    }


def build_button3_result_comparison_preview(payload: Dict[str, Any]) -> Dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}

    result_source_url = _clean_str(body.get("result_source_url", ""))
    source_tier = _clean_str(body.get("source_tier", "")) or "unknown"

    predicted_winner = _clean_str(body.get("predicted_winner", ""))
    predicted_method = _clean_str(body.get("predicted_method", ""))
    predicted_round = _normalize_round(body.get("predicted_round", ""))

    actual_winner = _clean_str(body.get("actual_winner", ""))
    actual_method = _clean_str(body.get("actual_method", ""))
    actual_round = _normalize_round(body.get("actual_round", ""))

    comparison_status = _resolve_status(body, result_source_url, actual_winner, predicted_winner)

    accuracy_preview = _build_accuracy_preview(
        comparison_status=comparison_status,
        predicted_winner=predicted_winner,
        predicted_method=predicted_method,
        predicted_round=predicted_round,
        actual_winner=actual_winner,
        actual_method=actual_method,
        actual_round=actual_round,
    )

    apply_authorization = _evaluate_apply_authorization(body, comparison_status)

    evaluation_timestamp_utc = _clean_str(body.get("evaluation_timestamp_utc", ""))
    if not evaluation_timestamp_utc:
        evaluation_timestamp_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "ok": True,
        "preview_only": True,
        "operator_approval_gate_required_for_apply": True,
        "fight_id": _clean_str(body.get("fight_id", "")),
        "event_name": _clean_str(body.get("event_name", "")),
        "fighter_a": _clean_str(body.get("fighter_a", "")),
        "fighter_b": _clean_str(body.get("fighter_b", "")),
        "predicted_winner": predicted_winner,
        "predicted_method": predicted_method,
        "predicted_round": predicted_round,
        "actual_winner": actual_winner,
        "actual_method": actual_method,
        "actual_round": actual_round,
        "result_source_url": result_source_url,
        "source_tier": source_tier,
        "comparison_status": comparison_status,
        "accuracy_preview": accuracy_preview,
        "apply_authorization": apply_authorization,
        "authorization_state": apply_authorization.get("authorization_state", "denied"),
        "authorized": bool(apply_authorization.get("authorized", False)),
        "authorization_reason_code": apply_authorization.get("reason_code", "unknown_state"),
        "authorization_reason_detail": apply_authorization.get("reason_detail", "apply authorization denied"),
        "authorization_operator_id": apply_authorization.get("operator_id", ""),
        "authorization_approval_action": apply_authorization.get("approval_action", ""),
        "authorization_operation_id": apply_authorization.get("operation_id", ""),
        "authorization_evaluated_at_utc": evaluation_timestamp_utc,
        "operator_review_required": True,
        "mutation_performed": False,
        "save_performed": False,
        "database_write_performed": False,
        "accuracy_ledger_mutation_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "gcid_write_performed": False,
        "customer_output_changed": False,
        "customer_report_generated": False,
        "queue_write_performed": False,
        "button1_source_call_authorized": False,
        "button2_generation_authorized": False,
        "button3_mutation_performed": False,
    }
