"""
button3_result_comparison_preview_v1.py

Preview-only Button 3 result comparison builder.
No apply path, no mutation path, no learning/calibration writes.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict


_SUPPORTED_STATUSES = {
    "result_found",
    "no_result_found",
    "needs_source",
    "conflict",
    "ready_to_compare",
    "needs_manual_review",
}

_BUTTON2_STRUCTURED_PREDICTION_CONTRACT_VERSION = "button2_structured_prediction_v1"


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


_CUSTOMER_OUTPUT_RELEASE_REASON_DETAILS = {
    "missing_contract_gates": "contract_gates object is required",
    "source_trust_gate_not_passed": "Source Trust gate must be passed",
    "identity_match_gate_not_passed": "Identity Match gate must be passed",
    "apply_authorization_gate_not_passed": "Apply Authorization gate must be passed",
    "accuracy_ledger_gate_not_passed": "Accuracy-Ledger gate must be passed",
    "controlled_learning_gate_not_passed": "Controlled-Learning gate must be passed",
    "gcid_runtime_impl_gate_not_passed": "GCID runtime implementation gate must be passed",
    "gcid_runtime_proof_review_gate_not_passed": "GCID runtime proof/review gate must be passed",
    "customer_output_design_gate_not_passed": "Customer-output release design gate must be passed",
    "customer_output_design_review_gate_not_passed": "Customer-output release design-review gate must be passed",
    "unknown_state": "unknown state detected",
    "comparison_status_not_eligible": "comparison_status must be ready_to_compare",
    "apply_authorization_not_eligible": "apply authorization must be eligible before customer-output-release eligibility evaluation",
    "accuracy_ledger_not_eligible": "accuracy-ledger eligibility must be true before customer-output-release eligibility evaluation",
    "controlled_learning_not_eligible": "controlled-learning candidate eligibility must be true before customer-output-release eligibility evaluation",
    "gcid_not_eligible": "gcid-write eligibility must be true before customer-output-release eligibility evaluation",
    "missing_canonical_fight_identity_key": "canonical_fight_identity_key is required",
    "missing_source_result_record_id": "source_result_record_id is required",
    "missing_source_lineage": "source_lineage object is required",
    "missing_gate_state_lineage": "gate_state_lineage object is required",
    "missing_customer_output_target_lineage": "customer_output_target_lineage object is required",
    "incomplete_provenance": "provenance fields are incomplete",
    "missing_operator_approval": "customer_output_release_operator_approval object is required",
    "missing_operator_id": "operator_id is required for customer-output-release eligibility approval",
    "missing_approval_action": "approval_action must be 'evaluate_customer_output_release_eligibility'",
    "missing_operation_id": "operation_id is required for customer-output-release eligibility approval",
    "invalid_approval_state": "approval_state must be one of 'approved', 'expired', 'revoked', or 'replayed'",
    "approval_not_approved": "approval_state must be 'approved'",
    "approval_expired": "approval_state indicates approval has expired",
    "approval_revoked": "approval_state indicates approval has been revoked",
    "approval_replayed": "approval_state indicates approval replay detected",
    "missing_scope": "scope object is required for customer-output-release eligibility approval",
    "fight_key_scope_mismatch": "approval scope fight_key does not match canonical_fight_identity_key",
    "source_record_scope_mismatch": "approval scope source_result_record_id does not match source_result_record_id",
    "operation_scope_mismatch": "approval scope operation_id does not match operation_id",
    "target_scope_mismatch": "approval scope customer_output_target_id does not match customer_output_target_lineage target id",
    "missing_audit_metadata": "audit_metadata object is required",
    "missing_rollback_metadata": "rollback_metadata object is required",
    "missing_release_traceability_metadata": "release_traceability_metadata object is required",
    "missing_denial_traceability": "audit metadata must include denial traceability fields",
    "missing_operator_traceability": "audit metadata must include operator traceability fields",
    "missing_release_traceability": "release traceability metadata must include release traceability fields",
    "eligible": "customer-output-release eligibility evaluation passed with mutation blocked",
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


def _build_learning_recommendation_preview(
    *,
    comparison_status: str,
    predicted_winner: str,
    predicted_method: str,
    predicted_round: str,
    actual_winner: str,
    actual_method: str,
    actual_round: str,
    result_source_url: str,
    source_tier: str,
    accuracy_preview: Dict[str, Any],
    structural_evidence_preview: Dict[str, Any],
) -> Dict[str, Any]:
    source_present = bool(result_source_url) and source_tier.lower() != "unknown"
    required_prediction_complete = bool(predicted_winner and predicted_method)
    required_result_complete = bool(actual_winner and actual_method)
    uncertainty_flags = []
    if comparison_status in {"conflict", "needs_manual_review"}:
        uncertainty_flags.append(comparison_status)
    if not required_prediction_complete:
        uncertainty_flags.append("incomplete_prediction_fields")
    if not required_result_complete:
        uncertainty_flags.append("incomplete_official_result_fields")
    if not source_present:
        uncertainty_flags.append("missing_result_source")

    right = {
        "winner_correctness": accuracy_preview.get("winner") == "hit",
        "method_correctness": accuracy_preview.get("method") == "hit",
        "round_or_range_correctness": accuracy_preview.get("round") == "hit" if predicted_round and actual_round else "unavailable",
        "source_provenance_quality": source_present,
    }
    missed = {
        "wrong_winner": accuracy_preview.get("winner") == "miss",
        "wrong_method": accuracy_preview.get("method") == "miss",
        "wrong_round_or_range": accuracy_preview.get("round") == "miss" if predicted_round and actual_round else False,
        "weak_or_missing_source_evidence": not source_present,
        "incomplete_prediction_fields": not required_prediction_complete,
        "uncertainty_or_conflict_flags": uncertainty_flags,
    }

    if not source_present:
        diagnosis = "BAD_OR_MISSING_SOURCE_DATA"
    elif not required_prediction_complete or not required_result_complete:
        diagnosis = "LOW_CONFIDENCE_OR_INCOMPLETE_EVIDENCE"
    elif comparison_status in {"conflict", "needs_manual_review"}:
        diagnosis = "NEEDS_OPERATOR_REVIEW"
    elif missed["wrong_winner"]:
        diagnosis = "WINNER_MISMATCH"
    elif missed["wrong_method"]:
        diagnosis = "METHOD_MISMATCH"
    elif missed["wrong_round_or_range"]:
        diagnosis = "ROUND_OR_TIMING_MISMATCH"
    else:
        diagnosis = "NO_ERROR_DETECTED"

    if uncertainty_flags or comparison_status != "ready_to_compare":
        status = "OPERATOR_REVIEW_REQUIRED"
        summary = "This comparison requires operator review before any learning decision."
    elif diagnosis == "NO_ERROR_DETECTED":
        status = "NO_LEARNING_NEEDED"
        summary = "The official result reinforces AI-RISA's analysis; no learning is recommended."
    else:
        status = "LEARNING_RECOMMENDED"
        summary = "The official result partially challenges AI-RISA's analysis; review the learning recommendation."

    return {
        "learning_preview_only": True,
        "what_ai_risa_got_right": right,
        "what_ai_risa_missed": missed,
        "error_diagnosis_category": diagnosis,
        "controlled_learning_status": status,
        "operator_facing_summary": summary,
        "safety_flags": {
            "learning_preview_only": True,
            "learning_applied": False,
            "calibration_write_authorized": False,
            "accuracy_ledger_write_authorized": False,
            "gCID_write_authorized": False,
            "operator_approval_required": True,
        },
        "structural_evidence_state": structural_evidence_preview.get("state", "unavailable"),
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


def _parse_scheduled_rounds(value: Any) -> int | None:
    if isinstance(value, int) and value in {3, 5}:
        return value
    cleaned = _clean_str(value)
    if cleaned in {"3", "5"}:
        return int(cleaned)
    return None


def _normalize_method_value(value: Any) -> str:
    cleaned = _clean_str(value)
    lowered = cleaned.lower()
    if not lowered:
        return ""

    if lowered in {"doctor stoppage", "doctor"} or "doctor stoppage" in lowered:
        return "doctor_stoppage"

    if "decision" in lowered or lowered in {"ud", "sd", "md"}:
        return "decision"

    if (
        lowered in {"ko", "tko", "ko/tko", "knockout", "technical knockout"}
        or "ko/tko" in lowered
        or "technical knockout" in lowered
    ):
        return "ko_tko"

    if (
        lowered in {"submission", "sub", "tapout", "rear-naked choke", "armbar", "guillotine"}
        or "rear-naked choke" in lowered
        or "armbar" in lowered
        or "guillotine" in lowered
    ):
        return "submission"

    return lowered


def _normalize_round_value(value: Any, scheduled_rounds: int | None) -> tuple[str, bool]:
    cleaned = _clean_str(value)
    lowered = cleaned.lower()
    if not lowered:
        return "", False

    if lowered.isdigit():
        return str(int(lowered)), False

    r_match = re.match(r"^r\s*([1-9]\d*)$", lowered)
    if r_match:
        return str(int(r_match.group(1))), False

    round_match = re.match(r"^round\s*([1-9]\d*)$", lowered)
    if round_match:
        return str(int(round_match.group(1))), False

    if lowered in {
        "full distance",
        "full time",
        "goes distance",
        "distance",
        "full fight",
    }:
        if scheduled_rounds is not None:
            return str(scheduled_rounds), True
        return "full_distance", False

    return lowered, False


def _build_method_round_normalization_preview(
    predicted_method: str,
    actual_method: str,
    predicted_round: str,
    actual_round: str,
    scheduled_rounds: int | None,
) -> Dict[str, Any]:
    predicted_method_normalized = _normalize_method_value(predicted_method)
    actual_method_normalized = _normalize_method_value(actual_method)
    predicted_round_normalized, full_distance_resolved = _normalize_round_value(predicted_round, scheduled_rounds)
    actual_round_normalized, _ = _normalize_round_value(actual_round, scheduled_rounds)

    return {
        "predicted_method_normalized": predicted_method_normalized,
        "actual_method_normalized": actual_method_normalized,
        "predicted_round_normalized": predicted_round_normalized,
        "actual_round_normalized": actual_round_normalized,
        "scheduled_rounds": scheduled_rounds,
        "full_distance_resolved": full_distance_resolved,
        "non_mutating": True,
        "learning_eligibility_effect": "none",
    }


def _resolve_predicted_fields_from_payload(body: Dict[str, Any]) -> Dict[str, Any]:
    predicted_winner_top = _clean_str(body.get("predicted_winner", ""))
    predicted_method_top = _clean_str(body.get("predicted_method", ""))
    predicted_round_top = _normalize_round(body.get("predicted_round", ""))

    structured = body.get("structured_prediction")
    if not isinstance(structured, dict):
        return {
            "predicted_winner": predicted_winner_top,
            "predicted_method": predicted_method_top,
            "predicted_round": predicted_round_top,
            "structured_prediction_context": None,
        }

    contract_version = _clean_str(structured.get("contract_version", ""))
    if contract_version != _BUTTON2_STRUCTURED_PREDICTION_CONTRACT_VERSION:
        return {
            "predicted_winner": predicted_winner_top,
            "predicted_method": predicted_method_top,
            "predicted_round": predicted_round_top,
            "structured_prediction_context": None,
        }

    predicted_winner_structured = _clean_str(structured.get("predicted_winner", ""))
    predicted_method_structured = _clean_str(structured.get("predicted_method", ""))
    predicted_round_structured = _normalize_round(structured.get("predicted_round", ""))

    structural_reasoning = _clean_str(structured.get("structural_reasoning", ""))
    tactical_pathway = _clean_str(structured.get("tactical_pathway", ""))
    evidence_notes = _clean_str(structured.get("evidence_notes", ""))

    return {
        "predicted_winner": predicted_winner_structured or predicted_winner_top,
        "predicted_method": predicted_method_structured or predicted_method_top,
        "predicted_round": predicted_round_structured or predicted_round_top,
        "structured_prediction_context": {
            "source": "button2_structured_prediction_contract",
            "contract_version": _BUTTON2_STRUCTURED_PREDICTION_CONTRACT_VERSION,
            "structural_reasoning_present": bool(structural_reasoning),
            "tactical_pathway_present": bool(tactical_pathway),
            "evidence_notes_present": bool(evidence_notes),
        },
    }


def _build_structural_evidence_preview(body: Dict[str, Any]) -> Dict[str, Any]:
    structured = body.get("structured_prediction")
    if not isinstance(structured, dict):
        return {
            "score": 0.0,
            "state": "unavailable",
            "reason_code": "no_structured_prediction_contract",
            "non_mutating": True,
            "learning_eligibility_effect": "none",
        }

    contract_version = _clean_str(structured.get("contract_version", ""))
    if contract_version != _BUTTON2_STRUCTURED_PREDICTION_CONTRACT_VERSION:
        return {
            "score": 0.0,
            "state": "unavailable",
            "reason_code": "no_structured_prediction_contract",
            "non_mutating": True,
            "learning_eligibility_effect": "none",
        }

    structural_reasoning = _clean_str(structured.get("structural_reasoning", ""))
    tactical_pathway = _clean_str(structured.get("tactical_pathway", ""))
    evidence_notes = _clean_str(structured.get("evidence_notes", ""))
    present_count = sum(
        1
        for value in (structural_reasoning, tactical_pathway, evidence_notes)
        if bool(value)
    )

    score_by_count = {
        0: 0.0,
        1: 0.33,
        2: 0.66,
        3: 1.0,
    }
    state_by_count = {
        0: "unavailable",
        1: "weak",
        2: "partial",
        3: "supported",
    }
    reason_by_count = {
        0: "no_structural_fields_present",
        1: "one_structural_field_present",
        2: "two_structural_fields_present",
        3: "all_structural_fields_present",
    }

    return {
        "score": score_by_count[present_count],
        "state": state_by_count[present_count],
        "reason_code": reason_by_count[present_count],
        "non_mutating": True,
        "learning_eligibility_effect": "none",
    }


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


def _evaluate_customer_output_release_eligibility(
    payload: Dict[str, Any],
    *,
    comparison_status: str,
    apply_authorization: Dict[str, Any],
    accuracy_ledger_evaluation: Dict[str, Any],
    controlled_learning_candidate_evaluation: Dict[str, Any],
    gcid_write_eligibility_evaluation: Dict[str, Any],
    evaluation_timestamp_utc: str,
) -> Dict[str, Any]:
    contract_gates = payload.get("contract_gates")
    canonical_fight_identity_key = _clean_str(payload.get("canonical_fight_identity_key", ""))
    source_result_record_id = _clean_str(payload.get("source_result_record_id", ""))
    source_lineage = payload.get("source_lineage")
    gate_state_lineage = payload.get("gate_state_lineage")
    customer_output_target_lineage = payload.get("customer_output_target_lineage")
    release_operator_approval = payload.get("customer_output_release_operator_approval")
    audit_metadata = payload.get("audit_metadata")
    rollback_metadata = payload.get("rollback_metadata")
    release_traceability_metadata = payload.get("release_traceability_metadata")

    target_id = ""
    if isinstance(customer_output_target_lineage, dict):
        target_id = _clean_str(customer_output_target_lineage.get("customer_output_target_id", ""))

    provenance_validation = {
        "canonical_fight_identity_key_present": bool(canonical_fight_identity_key),
        "source_result_record_id_present": bool(source_result_record_id),
        "source_lineage_present": isinstance(source_lineage, dict),
        "gate_state_lineage_present": isinstance(gate_state_lineage, dict),
        "customer_output_target_lineage_present": isinstance(customer_output_target_lineage, dict),
    }
    provenance_validation["complete"] = all(provenance_validation.values()) and bool(target_id)

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

    release_traceability_validation = {
        "release_traceability_metadata_present": isinstance(release_traceability_metadata, dict),
        "release_trace_id_present": isinstance(release_traceability_metadata, dict)
        and bool(_clean_str((release_traceability_metadata or {}).get("release_trace_id", ""))),
        "release_target_binding_present": isinstance(release_traceability_metadata, dict)
        and bool(_clean_str((release_traceability_metadata or {}).get("customer_output_target_id", ""))),
    }
    release_traceability_validation["complete"] = all(release_traceability_validation.values())

    approval_validation = {
        "approval_present": isinstance(release_operator_approval, dict),
        "operator_id_present": False,
        "approval_action_valid": False,
        "operation_id_present": False,
        "approval_state": "",
        "scope_present": False,
        "scope_match": False,
        "status": "denied",
    }

    if isinstance(release_operator_approval, dict):
        approval_operator_id = _clean_str(release_operator_approval.get("operator_id", ""))
        approval_action = _clean_str(release_operator_approval.get("approval_action", ""))
        approval_operation_id = _clean_str(release_operator_approval.get("operation_id", ""))
        approval_state = _clean_str(release_operator_approval.get("approval_state", "")).lower()
        approval_scope = release_operator_approval.get("scope")

        approval_validation["operator_id_present"] = bool(approval_operator_id)
        approval_validation["approval_action_valid"] = approval_action == "evaluate_customer_output_release_eligibility"
        approval_validation["operation_id_present"] = bool(approval_operation_id)
        approval_validation["approval_state"] = approval_state
        approval_validation["scope_present"] = isinstance(approval_scope, dict)

        if isinstance(approval_scope, dict):
            scope_fight_key = _clean_str(approval_scope.get("fight_key", ""))
            scope_source_record_id = _clean_str(approval_scope.get("source_result_record_id", ""))
            scope_operation_id = _clean_str(approval_scope.get("operation_id", ""))
            scope_target_id = _clean_str(approval_scope.get("customer_output_target_id", ""))
            approval_validation["scope_match"] = (
                bool(scope_fight_key)
                and scope_fight_key == canonical_fight_identity_key
                and bool(scope_source_record_id)
                and scope_source_record_id == source_result_record_id
                and bool(scope_operation_id)
                and scope_operation_id == approval_operation_id
                and bool(scope_target_id)
                and scope_target_id == target_id
            )

    def _deny(reason_code: str) -> Dict[str, Any]:
        return {
            "customer_output_release_eligibility_state": "denied",
            "customer_output_release_eligible": False,
            "reason_code": reason_code,
            "reason_detail": _CUSTOMER_OUTPUT_RELEASE_REASON_DETAILS.get(
                reason_code,
                "customer-output-release eligibility evaluation denied",
            ),
            "provenance_validation": provenance_validation,
            "audit_validation": audit_validation,
            "rollback_validation": rollback_validation,
            "release_traceability_validation": release_traceability_validation,
            "approval_validation": approval_validation,
            "evaluation_timestamp_utc": evaluation_timestamp_utc,
            "customer_output_release_authorized": False,
            "customer_output_release_execution_authority_issued": False,
            "customer_output_release_executed": False,
            "report_regeneration_executed": False,
            "durable_customer_output_persistence_executed": False,
        }

    if comparison_status != "ready_to_compare":
        return _deny("comparison_status_not_eligible")
    if not bool(apply_authorization.get("authorized", False)):
        return _deny("apply_authorization_not_eligible")
    if not bool(accuracy_ledger_evaluation.get("accuracy_ledger_eligible", False)):
        return _deny("accuracy_ledger_not_eligible")
    if not bool(controlled_learning_candidate_evaluation.get("controlled_learning_candidate_eligible", False)):
        return _deny("controlled_learning_not_eligible")
    if not bool(gcid_write_eligibility_evaluation.get("gcid_write_eligible", False)):
        return _deny("gcid_not_eligible")

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
    if not bool(contract_gates.get("gcid_write_runtime_implementation_gate_passed", False)):
        return _deny("gcid_runtime_impl_gate_not_passed")
    if not bool(contract_gates.get("gcid_write_runtime_proof_review_gate_passed", False)):
        return _deny("gcid_runtime_proof_review_gate_not_passed")
    if not bool(contract_gates.get("customer_output_release_design_gate_passed", False)):
        return _deny("customer_output_design_gate_not_passed")
    if not bool(contract_gates.get("customer_output_release_design_review_gate_passed", False)):
        return _deny("customer_output_design_review_gate_not_passed")
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
    if not isinstance(customer_output_target_lineage, dict):
        return _deny("missing_customer_output_target_lineage")

    source_lineage_url = _clean_str(source_lineage.get("source_url", ""))
    source_lineage_tier = _clean_str(source_lineage.get("source_tier", ""))
    gate_source_trust = _clean_str(gate_state_lineage.get("source_trust_state", ""))
    gate_identity_match = _clean_str(gate_state_lineage.get("identity_match_state", ""))
    gate_apply_authorization = _clean_str(gate_state_lineage.get("apply_authorization_state", ""))
    target_channel = _clean_str(customer_output_target_lineage.get("target_channel", ""))
    if (
        not source_lineage_url
        or not source_lineage_tier
        or not gate_source_trust
        or not gate_identity_match
        or not gate_apply_authorization
        or not target_id
        or not target_channel
    ):
        return _deny("incomplete_provenance")

    if not isinstance(release_operator_approval, dict):
        return _deny("missing_operator_approval")

    approval_operator_id = _clean_str(release_operator_approval.get("operator_id", ""))
    approval_action = _clean_str(release_operator_approval.get("approval_action", ""))
    approval_operation_id = _clean_str(release_operator_approval.get("operation_id", ""))
    approval_state = _clean_str(release_operator_approval.get("approval_state", "")).lower()
    approval_scope = release_operator_approval.get("scope")

    if not approval_operator_id:
        return _deny("missing_operator_id")
    if approval_action != "evaluate_customer_output_release_eligibility":
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
    scope_target_id = _clean_str(approval_scope.get("customer_output_target_id", ""))

    if not scope_fight_key or scope_fight_key != canonical_fight_identity_key:
        return _deny("fight_key_scope_mismatch")
    if not scope_source_record_id or scope_source_record_id != source_result_record_id:
        return _deny("source_record_scope_mismatch")
    if not scope_operation_id or scope_operation_id != approval_operation_id:
        return _deny("operation_scope_mismatch")
    if not scope_target_id or scope_target_id != target_id:
        return _deny("target_scope_mismatch")

    if not isinstance(audit_metadata, dict):
        return _deny("missing_audit_metadata")
    if not isinstance(rollback_metadata, dict):
        return _deny("missing_rollback_metadata")
    if not isinstance(release_traceability_metadata, dict):
        return _deny("missing_release_traceability_metadata")

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

    release_trace_id = _clean_str(release_traceability_metadata.get("release_trace_id", ""))
    release_target_id = _clean_str(release_traceability_metadata.get("customer_output_target_id", ""))
    if not release_trace_id or not release_target_id or release_target_id != target_id:
        return _deny("missing_release_traceability")

    approval_validation["status"] = "approved"

    return {
        "customer_output_release_eligibility_state": "eligible",
        "customer_output_release_eligible": True,
        "reason_code": "eligible",
        "reason_detail": _CUSTOMER_OUTPUT_RELEASE_REASON_DETAILS["eligible"],
        "provenance_validation": provenance_validation,
        "audit_validation": audit_validation,
        "rollback_validation": rollback_validation,
        "release_traceability_validation": release_traceability_validation,
        "approval_validation": approval_validation,
        "evaluation_timestamp_utc": evaluation_timestamp_utc,
        "customer_output_release_authorized": False,
        "customer_output_release_execution_authority_issued": False,
        "customer_output_release_executed": False,
        "report_regeneration_executed": False,
        "durable_customer_output_persistence_executed": False,
    }


def build_button3_result_comparison_preview(payload: Dict[str, Any]) -> Dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}

    result_source_url = _clean_str(body.get("result_source_url", ""))
    source_tier = _clean_str(body.get("source_tier", "")) or "unknown"

    predicted_resolution = _resolve_predicted_fields_from_payload(body)
    predicted_winner = predicted_resolution["predicted_winner"]
    predicted_method = predicted_resolution["predicted_method"]
    predicted_round = predicted_resolution["predicted_round"]
    structured_prediction_context = predicted_resolution["structured_prediction_context"]
    structural_evidence_preview = _build_structural_evidence_preview(body)

    actual_winner = _clean_str(body.get("actual_winner", ""))
    actual_method = _clean_str(body.get("actual_method", ""))
    actual_round = _normalize_round(body.get("actual_round", ""))
    scheduled_rounds = _parse_scheduled_rounds(body.get("scheduled_rounds"))

    method_round_normalization_preview = _build_method_round_normalization_preview(
        predicted_method=predicted_method,
        actual_method=actual_method,
        predicted_round=predicted_round,
        actual_round=actual_round,
        scheduled_rounds=scheduled_rounds,
    )

    predicted_method_normalized = method_round_normalization_preview["predicted_method_normalized"]
    actual_method_normalized = method_round_normalization_preview["actual_method_normalized"]
    predicted_round_normalized = method_round_normalization_preview["predicted_round_normalized"]
    actual_round_normalized = method_round_normalization_preview["actual_round_normalized"]

    comparison_status = _resolve_status(body, result_source_url, actual_winner, predicted_winner)

    accuracy_preview = _build_accuracy_preview(
        comparison_status=comparison_status,
        predicted_winner=predicted_winner,
        predicted_method=predicted_method_normalized,
        predicted_round=predicted_round_normalized,
        actual_winner=actual_winner,
        actual_method=actual_method_normalized,
        actual_round=actual_round_normalized,
    )
    learning_recommendation_preview = _build_learning_recommendation_preview(
        comparison_status=comparison_status,
        predicted_winner=predicted_winner,
        predicted_method=predicted_method_normalized,
        predicted_round=predicted_round_normalized,
        actual_winner=actual_winner,
        actual_method=actual_method_normalized,
        actual_round=actual_round_normalized,
        result_source_url=result_source_url,
        source_tier=source_tier,
        accuracy_preview=accuracy_preview,
        structural_evidence_preview=structural_evidence_preview,
    )

    apply_authorization = _evaluate_apply_authorization(body, comparison_status)
    accuracy_ledger_evaluation = _evaluate_accuracy_ledger(
        body,
        comparison_status=comparison_status,
        apply_authorization=apply_authorization,
        predicted_winner=predicted_winner,
        predicted_method=predicted_method_normalized,
        predicted_round=predicted_round_normalized,
        actual_winner=actual_winner,
        actual_method=actual_method_normalized,
        actual_round=actual_round_normalized,
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

    customer_output_release_eligibility_evaluation = _evaluate_customer_output_release_eligibility(
        body,
        comparison_status=comparison_status,
        apply_authorization=apply_authorization,
        accuracy_ledger_evaluation=accuracy_ledger_evaluation,
        controlled_learning_candidate_evaluation=controlled_learning_candidate_evaluation,
        gcid_write_eligibility_evaluation=gcid_write_eligibility_evaluation,
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
        "structured_prediction_context": structured_prediction_context,
        "structural_evidence_preview": structural_evidence_preview,
        "method_round_normalization_preview": method_round_normalization_preview,
        "actual_winner": actual_winner,
        "actual_method": actual_method,
        "actual_round": actual_round,
        "result_source_url": result_source_url,
        "source_tier": source_tier,
        "comparison_status": comparison_status,
        "accuracy_preview": accuracy_preview,
        "learning_recommendation_preview": learning_recommendation_preview,
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
        "customer_output_release_eligibility_evaluation": customer_output_release_eligibility_evaluation,
        "customer_output_release_eligibility_state": customer_output_release_eligibility_evaluation.get(
            "customer_output_release_eligibility_state",
            "denied",
        ),
        "customer_output_release_eligible": bool(
            customer_output_release_eligibility_evaluation.get("customer_output_release_eligible", False)
        ),
        "customer_output_release_reason_code": customer_output_release_eligibility_evaluation.get(
            "reason_code",
            "unknown_state",
        ),
        "customer_output_release_reason_detail": customer_output_release_eligibility_evaluation.get(
            "reason_detail",
            "customer-output-release eligibility evaluation denied",
        ),
        "customer_output_release_evaluated_at_utc": customer_output_release_eligibility_evaluation.get(
            "evaluation_timestamp_utc",
            evaluation_timestamp_utc,
        ),
        "customer_output_provenance_complete": bool(
            customer_output_release_eligibility_evaluation.get("provenance_validation", {}).get("complete", False)
        ),
        "customer_output_audit_metadata_complete": bool(
            customer_output_release_eligibility_evaluation.get("audit_validation", {}).get("complete", False)
        ),
        "customer_output_rollback_metadata_complete": bool(
            customer_output_release_eligibility_evaluation.get("rollback_validation", {}).get("complete", False)
        ),
        "customer_output_release_traceability_complete": bool(
            customer_output_release_eligibility_evaluation.get("release_traceability_validation", {}).get(
                "complete",
                False,
            )
        ),
        "customer_output_scope_match": bool(
            customer_output_release_eligibility_evaluation.get("approval_validation", {}).get("scope_match", False)
        ),
        "customer_output_release_authorized": bool(
            customer_output_release_eligibility_evaluation.get("customer_output_release_authorized", False)
        ),
        "customer_output_release_execution_authority_issued": bool(
            customer_output_release_eligibility_evaluation.get(
                "customer_output_release_execution_authority_issued",
                False,
            )
        ),
        "customer_output_release_executed": bool(
            customer_output_release_eligibility_evaluation.get("customer_output_release_executed", False)
        ),
        "report_regeneration_executed": bool(
            customer_output_release_eligibility_evaluation.get("report_regeneration_executed", False)
        ),
        "durable_customer_output_persistence_executed": bool(
            customer_output_release_eligibility_evaluation.get(
                "durable_customer_output_persistence_executed",
                False,
            )
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
