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


_ACCURACY_LEDGER_REASON_DETAILS = {
    "missing_contract_gates": "contract_gates object is required",
    "source_trust_gate_not_passed": "Source Trust gate must be passed",
    "identity_match_gate_not_passed": "Identity Match gate must be passed",
    "apply_authorization_gate_not_passed": "Apply Authorization gate must be passed",
    "accuracy_ledger_contract_gate_not_passed": "Accuracy-Ledger contract gate must be passed",
    "apply_authorization_not_eligible": "apply authorization must be eligible before ledger evaluation",
    "comparison_status_not_eligible": "comparison_status must be ready_to_compare",
    "incomplete_evidence": "complete outcome/method/timing/structural evidence is required",
    "contradictory_evidence": "conflicting result evidence detected",
    "stale_evidence": "stale result evidence detected",
    "winner_only_signal": "winner-only reinforcement is blocked",
    "lucky_prediction_signal": "lucky-prediction reinforcement is blocked",
    "unknown_state": "unknown state detected",
    "eligible": "accuracy-ledger evaluation passed with separated dimensions",
}


_CONTROLLED_LEARNING_REASON_DETAILS = {
    "missing_contract_gates": "contract_gates object is required",
    "source_trust_gate_not_passed": "Source Trust gate must be passed",
    "identity_match_gate_not_passed": "Identity Match gate must be passed",
    "apply_authorization_gate_not_passed": "Apply Authorization gate must be passed",
    "accuracy_ledger_gate_not_passed": "Accuracy-Ledger gate must be passed",
    "controlled_learning_contract_gate_not_passed": "Controlled-Learning contract gate must be passed",
    "apply_authorization_not_eligible": "apply authorization must be eligible before controlled-learning evaluation",
    "accuracy_ledger_not_eligible": "accuracy-ledger eligibility must be true before controlled-learning evaluation",
    "comparison_status_not_eligible": "comparison_status must be ready_to_compare",
    "incomplete_signals": "complete outcome/method/timing/structural signals are required",
    "contradictory_evidence": "conflicting result evidence detected",
    "stale_evidence": "stale result evidence detected",
    "winner_only_signal": "winner-only learning is blocked",
    "lucky_prediction_signal": "lucky-prediction learning is blocked",
    "unknown_state": "unknown state detected",
    "eligible": "controlled-learning candidate evaluation passed",
}


_GCID_ELIGIBILITY_REASON_DETAILS = {
    "missing_contract_gates": "contract_gates object is required",
    "source_trust_gate_not_passed": "Source Trust gate must be passed",
    "identity_match_gate_not_passed": "Identity Match gate must be passed",
    "apply_authorization_gate_not_passed": "Apply Authorization gate must be passed",
    "accuracy_ledger_gate_not_passed": "Accuracy-Ledger gate must be passed",
    "controlled_learning_gate_not_passed": "Controlled-Learning gate must be passed",
    "gcid_design_gate_not_passed": "GCID write design gate must be passed",
    "gcid_design_review_gate_not_passed": "GCID write design-review gate must be passed",
    "unknown_state": "unknown state detected",
    "comparison_status_not_eligible": "comparison_status must be ready_to_compare",
    "apply_authorization_not_eligible": "apply authorization must be eligible before GCID eligibility evaluation",
    "accuracy_ledger_not_eligible": "accuracy-ledger eligibility must be true before GCID eligibility evaluation",
    "controlled_learning_not_eligible": "controlled-learning candidate eligibility must be true before GCID eligibility evaluation",
    "missing_canonical_fight_identity_key": "canonical_fight_identity_key is required",
    "missing_source_result_record_id": "source_result_record_id is required",
    "missing_source_lineage": "source_lineage object is required",
    "missing_gate_state_lineage": "gate_state_lineage object is required",
    "incomplete_provenance": "provenance fields are incomplete",
    "missing_operator_approval": "gcid_operator_approval object is required",
    "missing_operator_id": "operator_id is required for GCID eligibility approval",
    "missing_approval_action": "approval_action must be 'evaluate_gcid_write_eligibility'",
    "missing_operation_id": "operation_id is required for GCID eligibility approval",
    "invalid_approval_state": "approval_state must be one of 'approved', 'expired', 'revoked', or 'replayed'",
    "approval_not_approved": "approval_state must be 'approved'",
    "approval_expired": "approval_state indicates approval has expired",
    "approval_revoked": "approval_state indicates approval has been revoked",
    "approval_replayed": "approval_state indicates approval replay detected",
    "missing_scope": "scope object is required for GCID eligibility approval",
    "fight_key_scope_mismatch": "approval scope fight_key does not match canonical_fight_identity_key",
    "source_record_scope_mismatch": "approval scope source_result_record_id does not match source_result_record_id",
    "operation_scope_mismatch": "approval scope operation_id does not match operation_id",
    "missing_audit_metadata": "audit_metadata object is required",
    "missing_rollback_metadata": "rollback_metadata object is required",
    "missing_denial_traceability": "audit metadata must include denial traceability fields",
    "missing_operator_traceability": "audit metadata must include operator traceability fields",
    "eligible": "GCID write eligibility evaluation passed with mutation blocked",
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_accuracy_dimensions(
    *,
    predicted_winner: str,
    predicted_method: str,
    predicted_round: str,
    predicted_time: str,
    actual_winner: str,
    actual_method: str,
    actual_round: str,
    actual_time: str,
    result_source_url: str,
    source_tier: str,
    contradiction_detected: bool,
    stale_evidence: bool,
    structural_evidence_score: float,
) -> Dict[str, Any]:
    outcome_state = _match_value(predicted_winner, actual_winner)
    method_state = _match_value(predicted_method, actual_method)

    round_state = _match_value(predicted_round, actual_round)
    time_state = _match_value(predicted_time, actual_time)
    if round_state == "unavailable" and time_state == "unavailable":
        timing_state = "unavailable"
    elif round_state == "miss" or time_state == "miss":
        timing_state = "miss"
    elif round_state == "hit" or time_state == "hit":
        timing_state = "hit"
    else:
        timing_state = "unavailable"

    normalized_tier = source_tier.lower()
    trusted_tier = normalized_tier in {"official", "tier_a", "tier_b"}
    has_source_url = bool(result_source_url)
    structural_score = max(0.0, min(1.0, structural_evidence_score))

    if stale_evidence or contradiction_detected:
        structural_state = "fail"
    elif has_source_url and trusted_tier and structural_score >= 0.8:
        structural_state = "pass"
    elif has_source_url and structural_score > 0.0:
        structural_state = "fail"
    else:
        structural_state = "unavailable"

    return {
        "outcome_accuracy_state": outcome_state,
        "method_accuracy_state": method_state,
        "timing_accuracy_state": timing_state,
        "structural_accuracy_state": structural_state,
        "structural_evidence_score": structural_score,
    }


def _accuracy_ledger_deny_payload(
    *,
    reason_code: str,
    dimensions: Dict[str, Any],
    winner_only_signal: bool,
    lucky_prediction_signal: bool,
) -> Dict[str, Any]:
    return {
        "accuracy_ledger_state": "denied",
        "accuracy_ledger_eligible": False,
        "reason_code": reason_code,
        "reason_detail": _ACCURACY_LEDGER_REASON_DETAILS.get(reason_code, "accuracy-ledger evaluation denied"),
        "dimensions": dimensions,
        "winner_only_reinforcement_blocked": winner_only_signal,
        "lucky_prediction_reinforcement_blocked": lucky_prediction_signal,
        "ledger_write_executed": False,
    }


def _evaluate_accuracy_ledger(
    payload: Dict[str, Any],
    *,
    comparison_status: str,
    apply_authorization: Dict[str, Any],
    predicted_winner: str,
    predicted_method: str,
    predicted_round: str,
    actual_winner: str,
    actual_method: str,
    actual_round: str,
    result_source_url: str,
    source_tier: str,
) -> Dict[str, Any]:
    predicted_time = _clean_str(payload.get("predicted_time", ""))
    actual_time = _clean_str(payload.get("actual_time", ""))
    contradiction_detected = _detect_conflict(payload)
    stale_evidence = _has_stale_result_evidence(payload)
    structural_evidence_score = _safe_float(payload.get("structural_evidence_score", 0.0), 0.0)

    dimensions = _build_accuracy_dimensions(
        predicted_winner=predicted_winner,
        predicted_method=predicted_method,
        predicted_round=predicted_round,
        predicted_time=predicted_time,
        actual_winner=actual_winner,
        actual_method=actual_method,
        actual_round=actual_round,
        actual_time=actual_time,
        result_source_url=result_source_url,
        source_tier=source_tier,
        contradiction_detected=contradiction_detected,
        stale_evidence=stale_evidence,
        structural_evidence_score=structural_evidence_score,
    )

    winner_only_signal = (
        dimensions["outcome_accuracy_state"] == "hit"
        and dimensions["method_accuracy_state"] in {"unavailable", "miss"}
        and dimensions["timing_accuracy_state"] in {"unavailable", "miss"}
    )
    lucky_prediction_signal = bool(payload.get("lucky_prediction_signal", False)) or (
        dimensions["outcome_accuracy_state"] == "hit"
        and dimensions["structural_accuracy_state"] != "pass"
    )

    if comparison_status != "ready_to_compare":
        return _accuracy_ledger_deny_payload(
            reason_code="comparison_status_not_eligible",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if not bool(apply_authorization.get("authorized", False)):
        return _accuracy_ledger_deny_payload(
            reason_code="apply_authorization_not_eligible",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    contract_gates = payload.get("contract_gates")
    if not isinstance(contract_gates, dict):
        return _accuracy_ledger_deny_payload(
            reason_code="missing_contract_gates",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if not bool(contract_gates.get("source_trust_gate_passed", False)):
        return _accuracy_ledger_deny_payload(
            reason_code="source_trust_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if not bool(contract_gates.get("identity_match_gate_passed", False)):
        return _accuracy_ledger_deny_payload(
            reason_code="identity_match_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if not bool(contract_gates.get("apply_authorization_gate_passed", False)):
        return _accuracy_ledger_deny_payload(
            reason_code="apply_authorization_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if not bool(contract_gates.get("accuracy_ledger_contract_gate_passed", False)):
        return _accuracy_ledger_deny_payload(
            reason_code="accuracy_ledger_contract_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if contradiction_detected:
        return _accuracy_ledger_deny_payload(
            reason_code="contradictory_evidence",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if stale_evidence:
        return _accuracy_ledger_deny_payload(
            reason_code="stale_evidence",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if winner_only_signal:
        return _accuracy_ledger_deny_payload(
            reason_code="winner_only_signal",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if lucky_prediction_signal:
        return _accuracy_ledger_deny_payload(
            reason_code="lucky_prediction_signal",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if (
        dimensions["outcome_accuracy_state"] == "unavailable"
        or dimensions["method_accuracy_state"] == "unavailable"
        or dimensions["timing_accuracy_state"] == "unavailable"
        or dimensions["structural_accuracy_state"] != "pass"
    ):
        return _accuracy_ledger_deny_payload(
            reason_code="incomplete_evidence",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    return {
        "accuracy_ledger_state": "eligible",
        "accuracy_ledger_eligible": True,
        "reason_code": "eligible",
        "reason_detail": _ACCURACY_LEDGER_REASON_DETAILS["eligible"],
        "dimensions": dimensions,
        "winner_only_reinforcement_blocked": False,
        "lucky_prediction_reinforcement_blocked": False,
        "ledger_write_executed": False,
    }


def _controlled_learning_deny_payload(
    *,
    reason_code: str,
    dimensions: Dict[str, Any],
    winner_only_signal: bool,
    lucky_prediction_signal: bool,
) -> Dict[str, Any]:
    return {
        "controlled_learning_candidate_state": "denied",
        "controlled_learning_candidate_eligible": False,
        "reason_code": reason_code,
        "reason_detail": _CONTROLLED_LEARNING_REASON_DETAILS.get(
            reason_code,
            "controlled-learning candidate evaluation denied",
        ),
        "dimensions": dimensions,
        "winner_only_learning_blocked": winner_only_signal,
        "lucky_prediction_learning_blocked": lucky_prediction_signal,
        "candidate_creation_separate_from_application": True,
        "learning_application_authorized": False,
        "learning_application_performed": False,
        "candidate_write_executed": False,
    }


def _evaluate_controlled_learning_candidate(
    payload: Dict[str, Any],
    *,
    comparison_status: str,
    apply_authorization: Dict[str, Any],
    accuracy_ledger_evaluation: Dict[str, Any],
) -> Dict[str, Any]:
    dimensions = dict(accuracy_ledger_evaluation.get("dimensions", {}))
    outcome_state = _clean_str(dimensions.get("outcome_accuracy_state", "unavailable"))
    method_state = _clean_str(dimensions.get("method_accuracy_state", "unavailable"))
    timing_state = _clean_str(dimensions.get("timing_accuracy_state", "unavailable"))
    structural_state = _clean_str(dimensions.get("structural_accuracy_state", "unavailable"))

    contradiction_detected = _detect_conflict(payload)
    stale_evidence = _has_stale_result_evidence(payload)
    winner_only_signal = bool(accuracy_ledger_evaluation.get("winner_only_reinforcement_blocked", False)) or (
        outcome_state == "hit"
        and method_state in {"unavailable", "miss"}
        and timing_state in {"unavailable", "miss"}
    )
    lucky_prediction_signal = bool(accuracy_ledger_evaluation.get("lucky_prediction_reinforcement_blocked", False)) or bool(
        payload.get("lucky_prediction_signal", False)
    )

    if comparison_status != "ready_to_compare":
        return _controlled_learning_deny_payload(
            reason_code="comparison_status_not_eligible",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if not bool(apply_authorization.get("authorized", False)):
        return _controlled_learning_deny_payload(
            reason_code="apply_authorization_not_eligible",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if not bool(accuracy_ledger_evaluation.get("accuracy_ledger_eligible", False)):
        return _controlled_learning_deny_payload(
            reason_code="accuracy_ledger_not_eligible",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    contract_gates = payload.get("contract_gates")
    if not isinstance(contract_gates, dict):
        return _controlled_learning_deny_payload(
            reason_code="missing_contract_gates",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if not bool(contract_gates.get("source_trust_gate_passed", False)):
        return _controlled_learning_deny_payload(
            reason_code="source_trust_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if not bool(contract_gates.get("identity_match_gate_passed", False)):
        return _controlled_learning_deny_payload(
            reason_code="identity_match_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if not bool(contract_gates.get("apply_authorization_gate_passed", False)):
        return _controlled_learning_deny_payload(
            reason_code="apply_authorization_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if not bool(contract_gates.get("accuracy_ledger_contract_gate_passed", False)):
        return _controlled_learning_deny_payload(
            reason_code="accuracy_ledger_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if not bool(contract_gates.get("controlled_learning_contract_gate_passed", False)):
        return _controlled_learning_deny_payload(
            reason_code="controlled_learning_contract_gate_not_passed",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if bool(contract_gates.get("unknown_state_detected", False)):
        return _controlled_learning_deny_payload(
            reason_code="unknown_state",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if contradiction_detected:
        return _controlled_learning_deny_payload(
            reason_code="contradictory_evidence",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if stale_evidence:
        return _controlled_learning_deny_payload(
            reason_code="stale_evidence",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if winner_only_signal:
        return _controlled_learning_deny_payload(
            reason_code="winner_only_signal",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )
    if lucky_prediction_signal:
        return _controlled_learning_deny_payload(
            reason_code="lucky_prediction_signal",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    if (
        outcome_state == "unavailable"
        or method_state == "unavailable"
        or timing_state == "unavailable"
        or structural_state != "pass"
    ):
        return _controlled_learning_deny_payload(
            reason_code="incomplete_signals",
            dimensions=dimensions,
            winner_only_signal=winner_only_signal,
            lucky_prediction_signal=lucky_prediction_signal,
        )

    return {
        "controlled_learning_candidate_state": "eligible",
        "controlled_learning_candidate_eligible": True,
        "reason_code": "eligible",
        "reason_detail": _CONTROLLED_LEARNING_REASON_DETAILS["eligible"],
        "dimensions": dimensions,
        "winner_only_learning_blocked": False,
        "lucky_prediction_learning_blocked": False,
        "candidate_creation_separate_from_application": True,
        "learning_application_authorized": False,
        "learning_application_performed": False,
        "candidate_write_executed": False,
    }


def _evaluate_gcid_write_eligibility(
    payload: Dict[str, Any],
    *,
    comparison_status: str,
    apply_authorization: Dict[str, Any],
    accuracy_ledger_evaluation: Dict[str, Any],
    controlled_learning_candidate_evaluation: Dict[str, Any],
    evaluation_timestamp_utc: str,
) -> Dict[str, Any]:
    contract_gates = payload.get("contract_gates")
    canonical_fight_identity_key = _clean_str(payload.get("canonical_fight_identity_key", ""))
    source_result_record_id = _clean_str(payload.get("source_result_record_id", ""))
    source_lineage = payload.get("source_lineage")
    gate_state_lineage = payload.get("gate_state_lineage")
    gcid_operator_approval = payload.get("gcid_operator_approval")
    audit_metadata = payload.get("audit_metadata")
    rollback_metadata = payload.get("rollback_metadata")

    provenance_validation = {
        "canonical_fight_identity_key_present": bool(canonical_fight_identity_key),
        "source_result_record_id_present": bool(source_result_record_id),
        "source_lineage_present": isinstance(source_lineage, dict),
        "gate_state_lineage_present": isinstance(gate_state_lineage, dict),
    }
    provenance_validation["complete"] = all(provenance_validation.values())

    audit_validation = {
        "audit_metadata_present": isinstance(audit_metadata, dict),
        "denial_traceability_present": isinstance(audit_metadata, dict)
        and bool(_clean_str((audit_metadata or {}).get("denial_reason_trace_id", ""))),
        "operator_traceability_present": isinstance(audit_metadata, dict)
        and bool(_clean_str((audit_metadata or {}).get("operator_trace_id", ""))),
    }
    audit_validation["complete"] = all(audit_validation.values())

    rollback_validation = {
        "rollback_metadata_present": isinstance(rollback_metadata, dict),
        "rollback_operation_id_present": isinstance(rollback_metadata, dict)
        and bool(_clean_str((rollback_metadata or {}).get("rollback_operation_id", ""))),
        "rollback_strategy_present": isinstance(rollback_metadata, dict)
        and bool(_clean_str((rollback_metadata or {}).get("rollback_strategy", ""))),
    }
    rollback_validation["complete"] = all(rollback_validation.values())

    approval_validation = {
        "approval_present": isinstance(gcid_operator_approval, dict),
        "operator_id_present": False,
        "approval_action_valid": False,
        "operation_id_present": False,
        "approval_state": "",
        "scope_present": False,
        "scope_match": False,
        "status": "denied",
    }

    if isinstance(gcid_operator_approval, dict):
        approval_operator_id = _clean_str(gcid_operator_approval.get("operator_id", ""))
        approval_action = _clean_str(gcid_operator_approval.get("approval_action", ""))
        approval_operation_id = _clean_str(gcid_operator_approval.get("operation_id", ""))
        approval_state = _clean_str(gcid_operator_approval.get("approval_state", "")).lower()
        approval_scope = gcid_operator_approval.get("scope")

        approval_validation["operator_id_present"] = bool(approval_operator_id)
        approval_validation["approval_action_valid"] = approval_action == "evaluate_gcid_write_eligibility"
        approval_validation["operation_id_present"] = bool(approval_operation_id)
        approval_validation["approval_state"] = approval_state
        approval_validation["scope_present"] = isinstance(approval_scope, dict)

        if isinstance(approval_scope, dict):
            scope_fight_key = _clean_str(approval_scope.get("fight_key", ""))
            scope_source_record_id = _clean_str(approval_scope.get("source_result_record_id", ""))
            scope_operation_id = _clean_str(approval_scope.get("operation_id", ""))
            approval_validation["scope_match"] = (
                bool(scope_fight_key)
                and scope_fight_key == canonical_fight_identity_key
                and bool(scope_source_record_id)
                and scope_source_record_id == source_result_record_id
                and bool(scope_operation_id)
                and scope_operation_id == approval_operation_id
            )

    def _deny(reason_code: str) -> Dict[str, Any]:
        return {
            "gcid_write_eligibility_state": "denied",
            "gcid_write_eligible": False,
            "reason_code": reason_code,
            "reason_detail": _GCID_ELIGIBILITY_REASON_DETAILS.get(reason_code, "GCID write eligibility evaluation denied"),
            "provenance_validation": provenance_validation,
            "audit_validation": audit_validation,
            "rollback_validation": rollback_validation,
            "approval_validation": approval_validation,
            "evaluation_timestamp_utc": evaluation_timestamp_utc,
            "gcid_write_authorized": False,
            "gcid_write_execution_authority_issued": False,
            "gcid_write_executed": False,
            "durable_gcid_persistence_executed": False,
        }

    if comparison_status != "ready_to_compare":
        return _deny("comparison_status_not_eligible")
    if not bool(apply_authorization.get("authorized", False)):
        return _deny("apply_authorization_not_eligible")
    if not bool(accuracy_ledger_evaluation.get("accuracy_ledger_eligible", False)):
        return _deny("accuracy_ledger_not_eligible")
    if not bool(controlled_learning_candidate_evaluation.get("controlled_learning_candidate_eligible", False)):
        return _deny("controlled_learning_not_eligible")

    if not isinstance(contract_gates, dict):
        return _deny("missing_contract_gates")
    if not bool(contract_gates.get("source_trust_gate_passed", False)):
        return _deny("source_trust_gate_not_passed")
    if not bool(contract_gates.get("identity_match_gate_passed", False)):
        return _deny("identity_match_gate_not_passed")
    if not bool(contract_gates.get("apply_authorization_gate_passed", False)):
        return _deny("apply_authorization_gate_not_passed")
    if not bool(contract_gates.get("accuracy_ledger_contract_gate_passed", False)):
        return _deny("accuracy_ledger_gate_not_passed")
    if not bool(contract_gates.get("controlled_learning_contract_gate_passed", False)):
        return _deny("controlled_learning_gate_not_passed")
    if not bool(contract_gates.get("gcid_write_design_gate_passed", False)):
        return _deny("gcid_design_gate_not_passed")
    if not bool(contract_gates.get("gcid_write_design_review_gate_passed", False)):
        return _deny("gcid_design_review_gate_not_passed")
    if bool(contract_gates.get("unknown_state_detected", False)):
        return _deny("unknown_state")

    if not canonical_fight_identity_key:
        return _deny("missing_canonical_fight_identity_key")
    if not source_result_record_id:
        return _deny("missing_source_result_record_id")
    if not isinstance(source_lineage, dict):
        return _deny("missing_source_lineage")
    if not isinstance(gate_state_lineage, dict):
        return _deny("missing_gate_state_lineage")

    source_lineage_url = _clean_str(source_lineage.get("source_url", ""))
    source_lineage_tier = _clean_str(source_lineage.get("source_tier", ""))
    gate_source_trust = _clean_str(gate_state_lineage.get("source_trust_state", ""))
    gate_identity_match = _clean_str(gate_state_lineage.get("identity_match_state", ""))
    gate_apply_authorization = _clean_str(gate_state_lineage.get("apply_authorization_state", ""))

    if (
        not source_lineage_url
        or not source_lineage_tier
        or not gate_source_trust
        or not gate_identity_match
        or not gate_apply_authorization
    ):
        return _deny("incomplete_provenance")

    if not isinstance(gcid_operator_approval, dict):
        return _deny("missing_operator_approval")

    approval_operator_id = _clean_str(gcid_operator_approval.get("operator_id", ""))
    approval_action = _clean_str(gcid_operator_approval.get("approval_action", ""))
    approval_operation_id = _clean_str(gcid_operator_approval.get("operation_id", ""))
    approval_state = _clean_str(gcid_operator_approval.get("approval_state", "")).lower()
    approval_scope = gcid_operator_approval.get("scope")

    if not approval_operator_id:
        return _deny("missing_operator_id")
    if approval_action != "evaluate_gcid_write_eligibility":
        return _deny("missing_approval_action")
    if not approval_operation_id:
        return _deny("missing_operation_id")
    if approval_state not in {"approved", "expired", "revoked", "replayed"}:
        return _deny("invalid_approval_state")
    if approval_state == "expired":
        return _deny("approval_expired")
    if approval_state == "revoked":
        return _deny("approval_revoked")
    if approval_state == "replayed":
        return _deny("approval_replayed")
    if approval_state != "approved":
        return _deny("approval_not_approved")
    if not isinstance(approval_scope, dict):
        return _deny("missing_scope")

    scope_fight_key = _clean_str(approval_scope.get("fight_key", ""))
    scope_source_record_id = _clean_str(approval_scope.get("source_result_record_id", ""))
    scope_operation_id = _clean_str(approval_scope.get("operation_id", ""))

    if not scope_fight_key or scope_fight_key != canonical_fight_identity_key:
        return _deny("fight_key_scope_mismatch")
    if not scope_source_record_id or scope_source_record_id != source_result_record_id:
        return _deny("source_record_scope_mismatch")
    if not scope_operation_id or scope_operation_id != approval_operation_id:
        return _deny("operation_scope_mismatch")

    if not isinstance(audit_metadata, dict):
        return _deny("missing_audit_metadata")
    if not isinstance(rollback_metadata, dict):
        return _deny("missing_rollback_metadata")

    denial_reason_trace_id = _clean_str(audit_metadata.get("denial_reason_trace_id", ""))
    operator_trace_id = _clean_str(audit_metadata.get("operator_trace_id", ""))
    if not denial_reason_trace_id:
        return _deny("missing_denial_traceability")
    if not operator_trace_id:
        return _deny("missing_operator_traceability")

    rollback_operation_id = _clean_str(rollback_metadata.get("rollback_operation_id", ""))
    rollback_strategy = _clean_str(rollback_metadata.get("rollback_strategy", ""))
    if not rollback_operation_id or not rollback_strategy:
        return _deny("missing_rollback_metadata")

    approval_validation["status"] = "approved"

    return {
        "gcid_write_eligibility_state": "eligible",
        "gcid_write_eligible": True,
        "reason_code": "eligible",
        "reason_detail": _GCID_ELIGIBILITY_REASON_DETAILS["eligible"],
        "provenance_validation": provenance_validation,
        "audit_validation": audit_validation,
        "rollback_validation": rollback_validation,
        "approval_validation": approval_validation,
        "evaluation_timestamp_utc": evaluation_timestamp_utc,
        "gcid_write_authorized": False,
        "gcid_write_execution_authority_issued": False,
        "gcid_write_executed": False,
        "durable_gcid_persistence_executed": False,
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
    accuracy_ledger_evaluation = _evaluate_accuracy_ledger(
        body,
        comparison_status=comparison_status,
        apply_authorization=apply_authorization,
        predicted_winner=predicted_winner,
        predicted_method=predicted_method,
        predicted_round=predicted_round,
        actual_winner=actual_winner,
        actual_method=actual_method,
        actual_round=actual_round,
        result_source_url=result_source_url,
        source_tier=source_tier,
    )
    controlled_learning_candidate_evaluation = _evaluate_controlled_learning_candidate(
        body,
        comparison_status=comparison_status,
        apply_authorization=apply_authorization,
        accuracy_ledger_evaluation=accuracy_ledger_evaluation,
    )

    evaluation_timestamp_utc = _clean_str(body.get("evaluation_timestamp_utc", ""))
    if not evaluation_timestamp_utc:
        evaluation_timestamp_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    gcid_write_eligibility_evaluation = _evaluate_gcid_write_eligibility(
        body,
        comparison_status=comparison_status,
        apply_authorization=apply_authorization,
        accuracy_ledger_evaluation=accuracy_ledger_evaluation,
        controlled_learning_candidate_evaluation=controlled_learning_candidate_evaluation,
        evaluation_timestamp_utc=evaluation_timestamp_utc,
    )

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
        "accuracy_ledger_evaluation": accuracy_ledger_evaluation,
        "accuracy_ledger_state": accuracy_ledger_evaluation.get("accuracy_ledger_state", "denied"),
        "accuracy_ledger_eligible": bool(accuracy_ledger_evaluation.get("accuracy_ledger_eligible", False)),
        "accuracy_ledger_reason_code": accuracy_ledger_evaluation.get("reason_code", "unknown_state"),
        "accuracy_ledger_reason_detail": accuracy_ledger_evaluation.get("reason_detail", "accuracy-ledger evaluation denied"),
        "outcome_accuracy_state": accuracy_ledger_evaluation.get("dimensions", {}).get("outcome_accuracy_state", "unavailable"),
        "method_accuracy_state": accuracy_ledger_evaluation.get("dimensions", {}).get("method_accuracy_state", "unavailable"),
        "timing_accuracy_state": accuracy_ledger_evaluation.get("dimensions", {}).get("timing_accuracy_state", "unavailable"),
        "structural_accuracy_state": accuracy_ledger_evaluation.get("dimensions", {}).get("structural_accuracy_state", "unavailable"),
        "structural_evidence_score": accuracy_ledger_evaluation.get("dimensions", {}).get("structural_evidence_score", 0.0),
        "winner_only_reinforcement_blocked": bool(
            accuracy_ledger_evaluation.get("winner_only_reinforcement_blocked", False)
        ),
        "lucky_prediction_reinforcement_blocked": bool(
            accuracy_ledger_evaluation.get("lucky_prediction_reinforcement_blocked", False)
        ),
        "controlled_learning_candidate_evaluation": controlled_learning_candidate_evaluation,
        "controlled_learning_candidate_state": controlled_learning_candidate_evaluation.get(
            "controlled_learning_candidate_state",
            "denied",
        ),
        "controlled_learning_candidate_eligible": bool(
            controlled_learning_candidate_evaluation.get("controlled_learning_candidate_eligible", False)
        ),
        "controlled_learning_candidate_reason_code": controlled_learning_candidate_evaluation.get(
            "reason_code",
            "unknown_state",
        ),
        "controlled_learning_candidate_reason_detail": controlled_learning_candidate_evaluation.get(
            "reason_detail",
            "controlled-learning candidate evaluation denied",
        ),
        "candidate_creation_separate_from_learning_application": bool(
            controlled_learning_candidate_evaluation.get("candidate_creation_separate_from_application", True)
        ),
        "learning_application_authorized": bool(
            controlled_learning_candidate_evaluation.get("learning_application_authorized", False)
        ),
        "winner_only_learning_blocked": bool(
            controlled_learning_candidate_evaluation.get("winner_only_learning_blocked", False)
        ),
        "lucky_prediction_learning_blocked": bool(
            controlled_learning_candidate_evaluation.get("lucky_prediction_learning_blocked", False)
        ),
        "gcid_write_eligibility_evaluation": gcid_write_eligibility_evaluation,
        "gcid_write_eligibility_state": gcid_write_eligibility_evaluation.get("gcid_write_eligibility_state", "denied"),
        "gcid_write_eligible": bool(gcid_write_eligibility_evaluation.get("gcid_write_eligible", False)),
        "gcid_write_reason_code": gcid_write_eligibility_evaluation.get("reason_code", "unknown_state"),
        "gcid_write_reason_detail": gcid_write_eligibility_evaluation.get(
            "reason_detail",
            "GCID write eligibility evaluation denied",
        ),
        "gcid_write_evaluated_at_utc": gcid_write_eligibility_evaluation.get(
            "evaluation_timestamp_utc",
            evaluation_timestamp_utc,
        ),
        "gcid_provenance_complete": bool(
            gcid_write_eligibility_evaluation.get("provenance_validation", {}).get("complete", False)
        ),
        "gcid_audit_metadata_complete": bool(
            gcid_write_eligibility_evaluation.get("audit_validation", {}).get("complete", False)
        ),
        "gcid_rollback_metadata_complete": bool(
            gcid_write_eligibility_evaluation.get("rollback_validation", {}).get("complete", False)
        ),
        "gcid_scope_match": bool(
            gcid_write_eligibility_evaluation.get("approval_validation", {}).get("scope_match", False)
        ),
        "gcid_write_authorized": bool(gcid_write_eligibility_evaluation.get("gcid_write_authorized", False)),
        "gcid_write_execution_authority_issued": bool(
            gcid_write_eligibility_evaluation.get("gcid_write_execution_authority_issued", False)
        ),
        "gcid_write_executed": bool(gcid_write_eligibility_evaluation.get("gcid_write_executed", False)),
        "durable_gcid_persistence_executed": bool(
            gcid_write_eligibility_evaluation.get("durable_gcid_persistence_executed", False)
        ),
        "operator_review_required": True,
        "mutation_performed": False,
        "save_performed": False,
        "database_write_performed": False,
        "accuracy_ledger_mutation_performed": False,
        "accuracy_ledger_write_performed": False,
        "controlled_learning_candidate_write_performed": False,
        "controlled_learning_application_performed": False,
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
