"""Button 1 auto-discovery readiness ranking (preview-only).

This module enriches candidate rows with deterministic readiness ranking metadata.
It is side-effect free and never performs saves, writes, delivery, or mutation.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from operator_dashboard.approved_combat_sport_source_registry import classify_source_url, get_source_governance


_TIER_SCORE = {
    "A": 100,
    "B": 82,
    "C": 58,
    "D": 25,
    "UNKNOWN": 0,
}

_COMPLETENESS_SCORE = {
    "full_card_confirmed": 100,
    "partial_card_confirmed": 72,
    "headline_only": 45,
    "unknown": 52,
}

_BUTTON2_READINESS_SCORE = {
    "ready_for_button2_preview": 100,
    "ready_to_save": 92,
    "ready": 85,
    "review_only": 38,
    "not_ready": 26,
    "selection_pending": 26,
    "unknown": 40,
}

_PROMOTION_PRIORITY = {
    "ufc": 100,
    "matchroom": 95,
    "glory": 88,
    "one": 82,
    "queensberry": 78,
    "top rank": 75,
    "no limit": 72,
}

_SPORT_PRIORITY = {
    "boxing": 94,
    "mma": 93,
    "kickboxing": 86,
    "muay_thai": 80,
    "multi_sport_alert": 74,
    "unknown": 60,
}

_BAND_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
    "blocked": 3,
}


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "ready", "blocked"}
    return bool(value)


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _parse_event_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _event_date_proximity_score(event_date_text: str, today: date) -> int:
    parsed = _parse_event_date(event_date_text)
    if parsed is None:
        return 45
    delta_days = (parsed - today).days
    if delta_days < 0:
        return 30
    if delta_days <= 14:
        return 100
    if delta_days <= 45:
        return 86
    if delta_days <= 90:
        return 72
    return 58


def _promotion_priority_score(promotion: str) -> int:
    normalized = promotion.lower()
    for key, score in _PROMOTION_PRIORITY.items():
        if key in normalized:
            return score
    return 62


def _sport_priority_score(sport_value: str) -> int:
    return _SPORT_PRIORITY.get(sport_value.lower(), _SPORT_PRIORITY["unknown"])


def _source_tier_from_row(row: Dict[str, Any]) -> str:
    direct = _as_text(row.get("source_tier") or row.get("tier"))
    if direct:
        upper = direct.upper()
        if upper in _TIER_SCORE:
            return upper

    source_url = _as_text(row.get("source_url") or row.get("event_url") or row.get("canonical_source_url"))
    if source_url:
        classification = classify_source_url(source_url)
        if isinstance(classification, dict):
            tier = _as_text(classification.get("tier")).upper()
            if tier in _TIER_SCORE:
                return tier
    return "UNKNOWN"


def _resolve_governance_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    source_url = _as_text(row.get("source_url") or row.get("event_url") or row.get("canonical_source_url"))
    if not source_url:
        return {}
    try:
        governance = get_source_governance(source_url)
        return governance if isinstance(governance, dict) else {}
    except Exception:
        return {}


def _derive_completeness_status(row: Dict[str, Any]) -> str:
    status = _as_text(row.get("card_completeness_status")).lower()
    if status in _COMPLETENESS_SCORE:
        return status

    expected = row.get("expected_matchup_count")
    matchup_count = row.get("matchup_count")
    if isinstance(expected, int) and isinstance(matchup_count, int) and expected > 0:
        if matchup_count >= expected:
            return "full_card_confirmed"
        if matchup_count >= max(1, int(expected * 0.5)):
            return "partial_card_confirmed"
        return "headline_only"

    if isinstance(row.get("matchups"), list) and len(row.get("matchups", [])) >= 5:
        return "full_card_confirmed"

    if isinstance(matchup_count, int) and matchup_count > 1:
        return "partial_card_confirmed"

    return "headline_only"


def _derive_button2_readiness_status(row: Dict[str, Any]) -> str:
    candidates = [
        row.get("button2_readiness_status"),
        row.get("report_ready_status"),
        row.get("ready_state"),
    ]
    for value in candidates:
        status = _as_text(value).lower()
        if status:
            if status in _BUTTON2_READINESS_SCORE:
                return status
            if "ready" in status and "not" not in status:
                return "ready_for_button2_preview"
            if "review" in status:
                return "review_only"
    return "unknown"


def _derive_provenance_status(row: Dict[str, Any]) -> str:
    explicit = _as_text(row.get("provenance_status")).lower()
    if explicit:
        return explicit
    source_backed = _as_bool(row.get("source_backed")) or bool(_as_text(row.get("source_url")))
    return "source_backed_ready" if source_backed else "review_only"


def _derive_matchup_count(row: Dict[str, Any]) -> int:
    if isinstance(row.get("matchup_count"), int):
        return max(0, int(row.get("matchup_count")))
    matchups = row.get("matchups")
    if isinstance(matchups, list):
        return len(matchups)
    fighter_a = _as_text(row.get("fighter_a") or row.get("fighter_a_name") or row.get("red_fighter"))
    fighter_b = _as_text(row.get("fighter_b") or row.get("fighter_b_name") or row.get("blue_fighter"))
    return 1 if fighter_a and fighter_b else 0


def _row_identity_key(row: Dict[str, Any], index: int) -> str:
    event = _as_text(row.get("event_name") or row.get("event") or row.get("event_title"))
    fighter_a = _as_text(row.get("fighter_a") or row.get("fighter_a_name") or row.get("red_fighter"))
    fighter_b = _as_text(row.get("fighter_b") or row.get("fighter_b_name") or row.get("blue_fighter"))
    candidate_id = _as_text(row.get("candidate_id") or row.get("matchup_id") or row.get("fight_id") or row.get("fight_key") or row.get("id"))
    return "|".join([candidate_id or f"idx_{index}", event.lower(), fighter_a.lower(), fighter_b.lower()])


def _evaluate_row(row: Dict[str, Any], index: int, today: date) -> Dict[str, Any]:
    source_url = _as_text(row.get("source_url") or row.get("event_url") or row.get("canonical_source_url"))
    source_tier = _source_tier_from_row(row)
    governance = _resolve_governance_from_row(row)

    queue_save_eligible = _as_bool(row.get("queue_save_eligible"))
    if "queue_save_eligible" not in row and governance:
        queue_save_eligible = bool(governance.get("queue_save_eligible", False))

    requires_secondary = _as_bool(row.get("requires_secondary_confirmation"))
    if "requires_secondary_confirmation" not in row and governance:
        requires_secondary = bool(governance.get("requires_secondary_confirmation", False))

    source_backed = _as_bool(row.get("source_backed")) or bool(source_url)
    provenance_status = _derive_provenance_status(row)
    completeness_status = _derive_completeness_status(row)
    matchup_count = _derive_matchup_count(row)
    button2_status = _derive_button2_readiness_status(row)

    sport = _as_text(row.get("sport") or row.get("modality") or governance.get("sport") if governance else "") or "unknown"
    promotion = _as_text(row.get("promotion") or row.get("organization") or row.get("league"))
    event_date = _as_text(row.get("event_date") or row.get("date"))

    fighter_a = _as_text(row.get("fighter_a") or row.get("fighter_a_name") or row.get("red_fighter"))
    fighter_b = _as_text(row.get("fighter_b") or row.get("fighter_b_name") or row.get("blue_fighter"))

    duplicate_flag = _as_bool(row.get("duplicate_or_conflict")) or _as_bool(row.get("is_duplicate")) or _as_bool(row.get("duplicate"))
    conflict_flag = _as_bool(row.get("conflict")) or _as_bool(row.get("has_conflict"))
    needs_review_flag = _as_bool(row.get("needs_review")) or _as_text(row.get("ready_state")).lower() == "needs_review"

    tier_score = _TIER_SCORE.get(source_tier, _TIER_SCORE["UNKNOWN"])
    provenance_score = 100 if provenance_status == "source_backed_ready" else 40
    source_quality_score = _clamp_score((tier_score * 0.62) + (provenance_score * 0.25) + (100 if source_url else 0) * 0.13)

    completeness_score = _clamp_score(
        (_COMPLETENESS_SCORE.get(completeness_status, _COMPLETENESS_SCORE["unknown"]) * 0.7)
        + (min(matchup_count, 12) / 12.0) * 30.0
    )

    button2_readiness_score = _BUTTON2_READINESS_SCORE.get(button2_status, _BUTTON2_READINESS_SCORE["unknown"])
    date_score = _event_date_proximity_score(event_date, today)
    promotion_score = _promotion_priority_score(promotion)
    sport_score = _sport_priority_score(sport)

    ranking_reasons: List[str] = []
    blocking_reasons: List[str] = []

    if source_tier != "UNKNOWN":
        ranking_reasons.append(f"source_tier={source_tier}")
    ranking_reasons.append(f"provenance_status={provenance_status}")
    ranking_reasons.append(f"card_completeness_status={completeness_status}")
    ranking_reasons.append(f"matchup_count={matchup_count}")
    ranking_reasons.append(f"button2_readiness_status={button2_status}")

    if not source_backed or not source_url:
        blocking_reasons.append("source_backed_provenance_required")
    if not fighter_a and not fighter_b and matchup_count <= 0:
        blocking_reasons.append("fighter_identity_missing")
    if conflict_flag:
        blocking_reasons.append("duplicate_or_conflict")
    if _as_bool(row.get("unsafe_queue_save_blocked")):
        blocking_reasons.append("unsafe_queue_save_blocked")

    review_penalty = 0
    if requires_secondary:
        ranking_reasons.append("requires_secondary_confirmation")
        review_penalty += 10
    if needs_review_flag:
        ranking_reasons.append("needs_review")
        review_penalty += 12
    if duplicate_flag and not conflict_flag:
        ranking_reasons.append("duplicate_detected")
        review_penalty += 18

    readiness_score = _clamp_score(
        (source_quality_score * 0.34)
        + (completeness_score * 0.26)
        + (button2_readiness_score * 0.22)
        + (date_score * 0.10)
        + (promotion_score * 0.05)
        + (sport_score * 0.03)
        - review_penalty
    )

    if blocking_reasons:
        readiness_band = "blocked"
    elif readiness_score >= 80:
        readiness_band = "high"
    elif readiness_score >= 58:
        readiness_band = "medium"
    else:
        readiness_band = "low"

    if readiness_band == "blocked":
        if "source_backed_provenance_required" in blocking_reasons:
            action = "review_source"
        elif "fighter_identity_missing" in blocking_reasons:
            action = "review_identity"
        else:
            action = "blocked"
    elif needs_review_flag or requires_secondary or duplicate_flag:
        action = "review_source" if not fighter_a or not fighter_b else "review_identity"
    elif completeness_status in {"headline_only", "partial_card_confirmed"} and matchup_count < 3:
        action = "wait_for_more_card_data"
    elif queue_save_eligible and button2_readiness_score >= 80:
        action = "save_to_queue"
    elif not queue_save_eligible:
        action = "review_source"
    else:
        action = "wait_for_more_card_data"

    if action == "review_source" and fighter_a and fighter_b and source_backed:
        action = "review_identity" if duplicate_flag or needs_review_flag else action

    return {
        "row_key": _row_identity_key(row, index),
        "source_tier": source_tier,
        "provenance_status": provenance_status,
        "card_completeness_status": completeness_status,
        "matchup_count": matchup_count,
        "button2_readiness_status": button2_status,
        "queue_save_eligible": queue_save_eligible,
        "source_quality_score": source_quality_score,
        "completeness_score": completeness_score,
        "button2_report_readiness_score": button2_readiness_score,
        "readiness_score": readiness_score,
        "readiness_band": readiness_band,
        "recommended_operator_action": action,
        "ranking_reasons": ranking_reasons,
        "blocking_reasons": blocking_reasons,
        "sort_key": (
            _BAND_ORDER[readiness_band],
            -readiness_score,
            -source_quality_score,
            -completeness_score,
            -button2_readiness_score,
            _as_text(row.get("event_name") or row.get("event") or row.get("event_title")).lower(),
            _as_text(row.get("fighter_a") or row.get("fighter_a_name") or row.get("red_fighter")).lower(),
            _as_text(row.get("fighter_b") or row.get("fighter_b_name") or row.get("blue_fighter")).lower(),
            _as_text(row.get("candidate_id") or row.get("matchup_id") or row.get("fight_id") or row.get("id")).lower(),
            index,
        ),
    }


def _attach_rank_fields(row: Dict[str, Any], rank_info: Dict[str, Any], rank_value: int) -> Dict[str, Any]:
    out = dict(row)
    out["discovery_rank"] = rank_value
    out["readiness_score"] = int(rank_info["readiness_score"])
    out["readiness_band"] = rank_info["readiness_band"]
    out["ranking_reasons"] = list(rank_info["ranking_reasons"])
    out["blocking_reasons"] = list(rank_info["blocking_reasons"])
    out["recommended_operator_action"] = rank_info["recommended_operator_action"]
    out["source_quality_score"] = int(rank_info["source_quality_score"])
    out["completeness_score"] = int(rank_info["completeness_score"])
    out["button2_report_readiness_score"] = int(rank_info["button2_report_readiness_score"])
    out["source_tier"] = rank_info["source_tier"]
    out["provenance_status"] = rank_info["provenance_status"]
    out["card_completeness_status"] = rank_info["card_completeness_status"]
    out["button2_readiness_status"] = rank_info["button2_readiness_status"]
    out["matchup_count"] = rank_info["matchup_count"]
    out["queue_save_eligible"] = bool(rank_info["queue_save_eligible"])

    matchups = out.get("matchups")
    if isinstance(matchups, list):
        enriched_matchups: List[Dict[str, Any]] = []
        for idx, matchup in enumerate(matchups):
            if not isinstance(matchup, dict):
                continue
            matchup_row = dict(out)
            matchup_row.update(matchup)
            matchup_row["matchups"] = []
            matchup_info = _evaluate_row(matchup_row, idx, date.today())
            enriched_matchup = dict(matchup)
            enriched_matchup["discovery_rank"] = rank_value
            enriched_matchup["readiness_score"] = int(matchup_info["readiness_score"])
            enriched_matchup["readiness_band"] = matchup_info["readiness_band"]
            enriched_matchup["ranking_reasons"] = list(matchup_info["ranking_reasons"])
            enriched_matchup["blocking_reasons"] = list(matchup_info["blocking_reasons"])
            enriched_matchup["recommended_operator_action"] = matchup_info["recommended_operator_action"]
            enriched_matchup["source_quality_score"] = int(matchup_info["source_quality_score"])
            enriched_matchup["completeness_score"] = int(matchup_info["completeness_score"])
            enriched_matchup["button2_report_readiness_score"] = int(matchup_info["button2_report_readiness_score"])
            enriched_matchups.append(enriched_matchup)
        out["matchups"] = enriched_matchups

    return out


def build_button1_auto_discovery_readiness_ranking(
    candidate_rows: List[Dict[str, Any]],
    today: date | None = None,
) -> List[Dict[str, Any]]:
    rows = [dict(row) for row in candidate_rows if isinstance(row, dict)]
    if not rows:
        return []

    rank_day = today or date.today()
    evaluations = [_evaluate_row(row, idx, rank_day) for idx, row in enumerate(rows)]

    ordered_indices = sorted(range(len(rows)), key=lambda i: evaluations[i]["sort_key"])
    rank_by_index = {idx: rank + 1 for rank, idx in enumerate(ordered_indices)}

    enriched: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        rank_info = evaluations[idx]
        discovery_rank = rank_by_index[idx]
        enriched.append(_attach_rank_fields(row, rank_info, discovery_rank))

    return enriched


__all__ = ["build_button1_auto_discovery_readiness_ranking"]
