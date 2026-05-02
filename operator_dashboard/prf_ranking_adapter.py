"""
Premium Report Factory — Button 1 ranking adapter.

Computes additive ranking enrichment for discovery and parse-preview rows.
Advisory only. No writes, no saves, no auto-selection, no approval-gate bypass.

Locked configuration:
  - Bucket thresholds defined by BUCKET_*_MIN constants.
  - Reason vocabulary defined by REASON_* constants.
  - Per-engine safe defaults defined by ENGINE_SAFE_DEFAULTS.
  - Optional diagnostics always included (INCLUDE_DIAGNOSTICS = True).
"""

from operator_dashboard.prf_ranking_scaffold import (
    build_button1_ranking_contracts,
    validate_ranking_scores,
    compute_composite_ranking_score,
    FIGHT_READINESS,
    REPORT_VALUE,
    CUSTOMER_PRIORITY,
    EVENT_CARD_PRIORITY,
    BETTING_INTEREST,
    COMMERCIAL_SELLABILITY,
    ANALYSIS_CONFIDENCE,
)

# ---------------------------------------------------------------------------
# Locked: adapter version
# ---------------------------------------------------------------------------

RANKING_ADAPTER_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Locked: bucket thresholds (composite score, 0–100)
# ---------------------------------------------------------------------------

BUCKET_PRIORITY_TIER_1_MIN = 70.0
BUCKET_PRIORITY_TIER_2_MIN = 50.0
BUCKET_WATCHLIST_TIER_MIN = 30.0

BUCKET_PRIORITY_TIER_1 = "priority_tier_1"
BUCKET_PRIORITY_TIER_2 = "priority_tier_2"
BUCKET_WATCHLIST_TIER = "watchlist_tier"
BUCKET_LOW_PRIORITY = "low_priority"
BUCKET_LOW_CONFIDENCE = "low_confidence"

# ---------------------------------------------------------------------------
# Locked: reason vocabulary
# ---------------------------------------------------------------------------

REASON_PARSE_COMPLETE = "parse_complete"
REASON_PARSE_INCOMPLETE = "parse_incomplete"
REASON_MISSING_FIGHTER_NAME = "missing_fighter_name"
REASON_CARD_POSITION_EARLY = "card_position_early"
REASON_CARD_POSITION_LATE = "card_position_late"
REASON_SOURCE_REFERENCE_PRESENT = "source_reference_present"
REASON_SOURCE_REFERENCE_MISSING = "source_reference_missing"
REASON_WEIGHT_CLASS_UNKNOWN = "weight_class_unknown"
REASON_RULESET_UNKNOWN = "ruleset_unknown"

# ---------------------------------------------------------------------------
# Locked: per-engine safe defaults (neutral mid-range, used when engine cannot
# compute a meaningful score from available preview-row inputs)
# ---------------------------------------------------------------------------

ENGINE_SAFE_DEFAULTS: dict[str, float] = {
    FIGHT_READINESS: 50.0,
    REPORT_VALUE: 50.0,
    CUSTOMER_PRIORITY: 50.0,
    EVENT_CARD_PRIORITY: 50.0,
    BETTING_INTEREST: 50.0,
    COMMERCIAL_SELLABILITY: 50.0,
    ANALYSIS_CONFIDENCE: 50.0,
}

# Optional diagnostics: always included.
INCLUDE_DIAGNOSTICS = True


# ---------------------------------------------------------------------------
# Internal per-engine scorers
# ---------------------------------------------------------------------------

def _score_fight_readiness(row: dict) -> tuple[float, list[str]]:
    """Score how ready this fight is for report building."""
    fighter_a = str(row.get("fighter_a") or "").strip()
    fighter_b = str(row.get("fighter_b") or "").strip()
    parse_status = str(row.get("parse_status") or "").strip()
    reasons: list[str] = []

    if parse_status == "parsed" and fighter_a and fighter_b:
        score = 65.0
        reasons.append(REASON_PARSE_COMPLETE)
    elif fighter_a or fighter_b:
        score = 35.0
        reasons.append(REASON_PARSE_INCOMPLETE)
    else:
        score = 20.0
        reasons.append(REASON_PARSE_INCOMPLETE)
        reasons.append(REASON_MISSING_FIGHTER_NAME)

    return score, reasons


def _score_report_value(row: dict) -> tuple[float, list[str]]:
    """Score the potential report value based on fighter identification."""
    fighter_a = str(row.get("fighter_a") or "").strip()
    fighter_b = str(row.get("fighter_b") or "").strip()
    reasons: list[str] = []

    if fighter_a and fighter_b:
        score = 60.0
        reasons.append(REASON_PARSE_COMPLETE)
    elif fighter_a or fighter_b:
        score = 35.0
        reasons.append(REASON_PARSE_INCOMPLETE)
    else:
        score = 15.0
        reasons.append(REASON_PARSE_INCOMPLETE)
        reasons.append(REASON_MISSING_FIGHTER_NAME)

    return score, reasons


def _score_customer_priority(row: dict) -> tuple[float, list[str]]:  # noqa: ARG001
    """No customer-priority signal is available at preview time; return safe default."""
    return ENGINE_SAFE_DEFAULTS[CUSTOMER_PRIORITY], []


def _score_event_card_priority(row: dict) -> tuple[float, list[str]]:
    """Score based on bout_order; lower order = higher card position = higher priority."""
    try:
        bout_order = int(row.get("bout_order") or 1)
    except (TypeError, ValueError):
        bout_order = 1

    reasons: list[str] = []

    if bout_order <= 2:
        score = 75.0
        reasons.append(REASON_CARD_POSITION_EARLY)
    elif bout_order <= 4:
        score = 60.0
        reasons.append(REASON_CARD_POSITION_EARLY)
    elif bout_order <= 6:
        score = 45.0
    else:
        score = 30.0
        reasons.append(REASON_CARD_POSITION_LATE)

    return score, reasons


def _score_betting_interest(row: dict) -> tuple[float, list[str]]:  # noqa: ARG001
    """No betting signal is available at preview time; return safe default."""
    return ENGINE_SAFE_DEFAULTS[BETTING_INTEREST], []


def _score_commercial_sellability(row: dict) -> tuple[float, list[str]]:
    """Score based on presence of a source reference."""
    source_reference = str(row.get("source_reference") or "").strip()
    reasons: list[str] = []

    if source_reference:
        score = 60.0
        reasons.append(REASON_SOURCE_REFERENCE_PRESENT)
    else:
        score = 40.0
        reasons.append(REASON_SOURCE_REFERENCE_MISSING)

    return score, reasons


def _score_analysis_confidence(row: dict) -> tuple[float, list[str]]:
    """Score analysis confidence from parse completeness and available metadata."""
    fighter_a = str(row.get("fighter_a") or "").strip()
    fighter_b = str(row.get("fighter_b") or "").strip()
    parse_status = str(row.get("parse_status") or "").strip()
    weight_class = row.get("weight_class")
    ruleset = row.get("ruleset")
    reasons: list[str] = []

    if parse_status == "parsed" and fighter_a and fighter_b:
        score = 65.0
        reasons.append(REASON_PARSE_COMPLETE)
    else:
        score = 30.0
        reasons.append(REASON_PARSE_INCOMPLETE)

    if weight_class is None:
        reasons.append(REASON_WEIGHT_CLASS_UNKNOWN)
    if ruleset is None:
        reasons.append(REASON_RULESET_UNKNOWN)

    return score, reasons


# ---------------------------------------------------------------------------
# Bucket helper
# ---------------------------------------------------------------------------

def _compute_ranking_bucket(composite: float) -> str:
    if composite >= BUCKET_PRIORITY_TIER_1_MIN:
        return BUCKET_PRIORITY_TIER_1
    if composite >= BUCKET_PRIORITY_TIER_2_MIN:
        return BUCKET_PRIORITY_TIER_2
    if composite >= BUCKET_WATCHLIST_TIER_MIN:
        return BUCKET_WATCHLIST_TIER
    return BUCKET_LOW_PRIORITY


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SCORERS = {
    FIGHT_READINESS: _score_fight_readiness,
    REPORT_VALUE: _score_report_value,
    CUSTOMER_PRIORITY: _score_customer_priority,
    EVENT_CARD_PRIORITY: _score_event_card_priority,
    BETTING_INTEREST: _score_betting_interest,
    COMMERCIAL_SELLABILITY: _score_commercial_sellability,
    ANALYSIS_CONFIDENCE: _score_analysis_confidence,
}


def compute_ranking_enrichment(row: dict) -> dict:
    """
    Compute additive ranking enrichment fields for a single Button 1 row.

    Returns all 10 additive ranking fields plus 3 diagnostics.
    Advisory only — does not trigger any writes or saves.
    Deterministic: identical input always produces identical output.
    """
    contracts = build_button1_ranking_contracts()
    engine_scores: dict[str, float] = {}
    all_reasons: list[str] = []

    for engine_id, scorer in _SCORERS.items():
        score, reasons = scorer(row)
        engine_scores[engine_id] = score
        for reason in reasons:
            if reason not in all_reasons:
                all_reasons.append(reason)

    validation = validate_ranking_scores(engine_scores, contracts)
    composite = compute_composite_ranking_score(engine_scores, contracts)

    missing_inputs: list[str] = []
    if not validation["ok"]:
        missing_inputs = sorted(validation.get("missing_engines", []))
        bucket = BUCKET_LOW_CONFIDENCE
    else:
        bucket = _compute_ranking_bucket(composite)

    # Deterministic sort for stable output
    ranking_reasons = sorted(set(all_reasons))

    result: dict = {
        "fight_readiness_score": engine_scores[FIGHT_READINESS],
        "report_value_score": engine_scores[REPORT_VALUE],
        "customer_priority_score": engine_scores[CUSTOMER_PRIORITY],
        "event_card_priority_score": engine_scores[EVENT_CARD_PRIORITY],
        "betting_interest_score": engine_scores[BETTING_INTEREST],
        "commercial_sellability_score": engine_scores[COMMERCIAL_SELLABILITY],
        "analysis_confidence_score": engine_scores[ANALYSIS_CONFIDENCE],
        "composite_ranking_score": composite,
        "ranking_bucket": bucket,
        "ranking_reasons": ranking_reasons,
    }

    if INCLUDE_DIAGNOSTICS:
        result["ranking_validation_ok"] = validation["ok"]
        result["ranking_missing_inputs"] = missing_inputs
        result["ranking_contract_version"] = RANKING_ADAPTER_VERSION

    return result


def enrich_row_with_ranking(row: dict) -> dict:
    """
    Return a copy of row with additive ranking enrichment fields merged in.

    Existing row keys are preserved unchanged. Ranking fields are additive only.
    Advisory only — does not trigger any writes or saves.
    """
    enrichment = compute_ranking_enrichment(row)
    return {**row, **enrichment}
