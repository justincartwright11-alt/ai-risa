from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


REQUIRED_CITATION_FIELDS = (
    "source_url",
    "source_title",
    "source_date",
    "publisher_host",
    "source_confidence",
    "confidence_score",
    "extracted_winner",
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _is_stale_source_date(date_text: str, max_age_days: int = 30) -> bool:
    raw = str(date_text or "").strip()
    if not raw:
        return True

    parsed = None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        try:
            parsed = datetime.fromisoformat(raw[:10] + "T00:00:00+00:00")
        except Exception:
            return True

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)
    return abs((now_utc - parsed.astimezone(timezone.utc)).days) > max_age_days


def evaluate_official_source_acceptance_gate(preview_result: dict, *, require_approval_binding: bool = False) -> dict:
    preview = preview_result if isinstance(preview_result, dict) else {}
    reason_code = str(preview.get("reason_code") or "").strip() or "citation_incomplete"
    selected_key = str(preview.get("selected_key") or "").strip() or None

    citation = preview.get("source_citation")
    if not isinstance(citation, dict):
        citation = {}

    citation_present = bool(citation)
    fingerprint_present = bool(str(citation.get("citation_fingerprint") or "").strip())
    citation_complete = bool(citation_present and all(str(citation.get(field) or "").strip() for field in REQUIRED_CITATION_FIELDS))

    source_tier = str(citation.get("source_confidence") or "").strip().lower()
    source_tier_allowed = source_tier in {"tier_a0", "tier_a1", "tier_b"}

    confidence_score = _safe_float(citation.get("confidence_score"), 0.0)
    confidence_sufficient = confidence_score >= 0.70

    if "identity_matches_selected_row" in citation:
        identity_match_passed = bool(citation.get("identity_matches_selected_row"))
    else:
        # "or not contradicted" policy in this slice
        identity_match_passed = True

    if reason_code == "stale_source_date":
        not_stale = False
    else:
        not_stale = not _is_stale_source_date(str(citation.get("source_date") or ""))

    no_conflict = reason_code not in {"source_conflict", "source_conflict_same_tier"} and source_tier != "conflict"

    preview_boundary_safe = (
        bool(preview.get("mutation_performed")) is False
        and bool(preview.get("bulk_lookup_performed")) is False
        and bool(preview.get("scoring_semantics_changed")) is False
    )

    checks = {
        "preview_boundary_safe": preview_boundary_safe,
        "citation_present": citation_present,
        "citation_complete": citation_complete,
        "fingerprint_present": fingerprint_present,
        "source_tier_allowed": source_tier_allowed,
        "confidence_sufficient": confidence_sufficient,
        "identity_match_passed": identity_match_passed,
        "not_stale": not_stale,
        "no_conflict": no_conflict,
    }

    final_state = "rejected"
    final_reason = reason_code

    if not preview_boundary_safe:
        final_reason = "preview_only_boundary_violation"
    elif not citation_present or not citation_complete:
        final_reason = "citation_incomplete"
    elif not fingerprint_present:
        final_reason = "missing_citation_fingerprint"
    elif reason_code in {"identity_conflict", "publisher_host_mismatch"}:
        final_reason = reason_code
    elif reason_code in {"source_conflict", "source_conflict_same_tier"}:
        final_state = "manual_review"
        final_reason = reason_code
    elif reason_code == "stale_source_date":
        final_state = "manual_review"
        final_reason = "stale_source_date"
    elif source_tier == "tier_b":
        final_state = "manual_review"
        final_reason = "tier_b_without_corroboration"
    elif not confidence_sufficient:
        final_state = "manual_review"
        final_reason = "confidence_below_threshold"
    elif not source_tier_allowed:
        final_reason = "source_url_not_allowed"
    elif not identity_match_passed:
        final_reason = "identity_conflict"
    elif not not_stale:
        final_state = "manual_review"
        final_reason = "stale_source_date"
    elif not no_conflict:
        final_state = "manual_review"
        final_reason = "source_conflict"
    elif require_approval_binding and not bool(preview.get("approval_binding_valid")):
        final_reason = "approval_missing"
    else:
        final_state = "write_eligible"
        final_reason = "accepted_preview_write_eligible"

    return {
        "state": final_state,
        "write_eligible": final_state == "write_eligible",
        "reason_code": final_reason,
        "reasons": [final_reason],
        "checks": checks,
        "selected_key": selected_key,
        "citation_fingerprint": str(citation.get("citation_fingerprint") or "").strip() or None,
    }
