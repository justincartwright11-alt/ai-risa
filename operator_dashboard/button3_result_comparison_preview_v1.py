"""
button3_result_comparison_preview_v1.py

Preview-only Button 3 result comparison builder.
No apply path, no mutation path, no learning/calibration writes.
"""

from typing import Any, Dict


_SUPPORTED_STATUSES = {
    "result_found",
    "no_result_found",
    "needs_source",
    "conflict",
    "ready_to_compare",
    "needs_manual_review",
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
        "operator_review_required": True,
        "mutation_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "queue_write_performed": False,
        "button3_mutation_performed": False,
    }
