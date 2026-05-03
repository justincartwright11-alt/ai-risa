"""
Button 3 accuracy/calibration runtime wiring adapter.

Additive-only helpers that enrich existing Button 3 responses with deterministic
status surfaces and approval-gated learning placeholders.

No writes, no calibration mutation, no learning mutation.
"""

from __future__ import annotations


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _tri_state_match(accuracy_pct):
    val = _to_float(accuracy_pct)
    if val is None:
        return None
    return bool(val >= 100.0)


def build_learning_gate_placeholder(operator_approval: bool = False) -> dict:
    """Return deterministic learning-gate placeholder fields.

    This adapter never opens live learning/calibration writes.
    """
    if operator_approval:
        return {
            "learning_gate_status": "approval_granted_apply_not_implemented",
            "learning_gate_reason": "future_learning_apply_endpoint_required",
            "operator_approval_required": True,
        }

    return {
        "learning_gate_status": "approval_required",
        "learning_gate_reason": "operator_approval_required_for_learning_or_calibration_update",
        "operator_approval_required": True,
    }


def build_button3_compare_runtime_fields(compare_payload: dict | None) -> dict:
    payload = compare_payload if isinstance(compare_payload, dict) else {}
    result_found = bool(payload.get("result_found"))

    score = payload.get("score") if isinstance(payload.get("score"), dict) else {}
    segments = score.get("segments") if isinstance(score.get("segments"), dict) else {}
    metrics = score.get("metrics") if isinstance(score.get("metrics"), dict) else {}

    winner_match = _tri_state_match(metrics.get("winner_accuracy"))
    method_match = _tri_state_match(metrics.get("method_accuracy"))
    round_match = _tri_state_match(metrics.get("round_accuracy"))

    overall_score = _to_float(metrics.get("overall_accuracy"))
    if overall_score is None:
        overall_score = _to_float(metrics.get("winner_accuracy"))

    return {
        "result_comparison_status": "compared" if result_found else "unresolved",
        "official_result_source_status": "found" if result_found else "missing",
        "predicted_winner_match": winner_match,
        "method_match": method_match,
        "round_match": round_match,
        "confidence_accuracy_band": "unavailable",
        "section_accuracy_scores": segments,
        "overall_report_accuracy_score": overall_score,
        "calibration_recommendations": [],
        "pattern_memory_update_proposals": [],
        **build_learning_gate_placeholder(operator_approval=False),
    }


def build_button3_summary_runtime_fields(summary_payload: dict | None) -> dict:
    payload = summary_payload if isinstance(summary_payload, dict) else {}
    compared = payload.get("compared_results") if isinstance(payload.get("compared_results"), list) else []
    waiting = payload.get("waiting_for_results") if isinstance(payload.get("waiting_for_results"), list) else []
    metrics = payload.get("summary_metrics") if isinstance(payload.get("summary_metrics"), dict) else {}

    total_compared = int(metrics.get("total_compared") or 0)
    overall_accuracy_pct = _to_float(metrics.get("overall_accuracy_pct"))

    status = "ready" if total_compared > 0 else "unresolved"
    source_status = "mixed" if (total_compared > 0 and len(waiting) > 0) else ("resolved" if total_compared > 0 else "missing")

    section_scores = {
        "fighter_accuracy_pct": overall_accuracy_pct,
        "matchup_accuracy_pct": overall_accuracy_pct,
        "event_accuracy_pct": overall_accuracy_pct,
        "segment_accuracy_pct": overall_accuracy_pct,
        "total_accuracy_pct": overall_accuracy_pct,
    }

    return {
        "result_comparison_status": status,
        "official_result_source_status": source_status,
        "predicted_winner_match": None,
        "method_match": None,
        "round_match": None,
        "confidence_accuracy_band": "summary_only",
        "section_accuracy_scores": section_scores,
        "overall_report_accuracy_score": overall_accuracy_pct,
        "calibration_recommendations": [],
        "pattern_memory_update_proposals": [],
        **build_learning_gate_placeholder(operator_approval=False),
    }


def build_button3_confidence_runtime_fields(calibration_payload: dict | None) -> dict:
    payload = calibration_payload if isinstance(calibration_payload, dict) else {}
    rows = payload.get("calibration") if isinstance(payload.get("calibration"), list) else []
    has_data = bool(payload.get("has_data"))

    recommendations = []
    sortable_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        gap = _to_float(row.get("calibration_gap"))
        if gap is None:
            continue
        sortable_rows.append((abs(gap), row.get("bucket"), gap))

    sortable_rows.sort(reverse=True)
    for _, bucket, gap in sortable_rows[:3]:
        direction = "increase" if gap < 0 else "decrease"
        recommendations.append(
            {
                "recommendation_id": f"confidence_bucket_{bucket}",
                "target": "confidence_threshold",
                "bucket": bucket,
                "gap": gap,
                "action": f"{direction}_confidence_for_bucket",
                "proposal_only": True,
            }
        )

    return {
        "result_comparison_status": "ready" if has_data else "unresolved",
        "official_result_source_status": "derived_local_accuracy_ledger",
        "predicted_winner_match": None,
        "method_match": None,
        "round_match": None,
        "confidence_accuracy_band": "calibration_view",
        "section_accuracy_scores": {"confidence_calibration_buckets": len(rows)},
        "overall_report_accuracy_score": None,
        "calibration_recommendations": recommendations,
        "pattern_memory_update_proposals": [],
        **build_learning_gate_placeholder(operator_approval=False),
    }


def build_button3_calibration_review_runtime_fields(review_payload: dict | None) -> dict:
    payload = review_payload if isinstance(review_payload, dict) else {}

    fights_analyzed = int(payload.get("fights_analyzed") or 0)
    proposed = payload.get("proposed_calibrations") if isinstance(payload.get("proposed_calibrations"), list) else []
    miss_patterns = payload.get("miss_patterns") if isinstance(payload.get("miss_patterns"), dict) else {}

    proposals = []
    for key, value in miss_patterns.items():
        proposals.append(
            {
                "proposal_id": f"pattern_{key}",
                "pattern_key": str(key),
                "pattern_value": value,
                "proposal_only": True,
            }
        )

    return {
        "result_comparison_status": "ready" if fights_analyzed > 0 else "unresolved",
        "official_result_source_status": "review_input_available" if fights_analyzed > 0 else "review_input_missing",
        "predicted_winner_match": None,
        "method_match": None,
        "round_match": None,
        "confidence_accuracy_band": "review_scope",
        "section_accuracy_scores": {"fights_analyzed": fights_analyzed},
        "overall_report_accuracy_score": None,
        "calibration_recommendations": proposed,
        "pattern_memory_update_proposals": proposals,
        **build_learning_gate_placeholder(operator_approval=False),
    }
