"""
Premium Report Factory global engine-pack ranking scaffold contracts.

This module defines contract-only structures for Button 1 ranking engines.
No runtime route wiring or live ranking execution is performed here.
"""

from dataclasses import dataclass


FIGHT_READINESS = "ranking.fight_readiness"
REPORT_VALUE = "ranking.report_value"
CUSTOMER_PRIORITY = "ranking.customer_priority"
EVENT_CARD_PRIORITY = "ranking.event_card_priority"
BETTING_INTEREST = "ranking.betting_interest"
COMMERCIAL_SELLABILITY = "ranking.commercial_sellability"
ANALYSIS_CONFIDENCE = "ranking.analysis_confidence"

RANKING_ENGINE_IDS = (
    FIGHT_READINESS,
    REPORT_VALUE,
    CUSTOMER_PRIORITY,
    EVENT_CARD_PRIORITY,
    BETTING_INTEREST,
    COMMERCIAL_SELLABILITY,
    ANALYSIS_CONFIDENCE,
)


@dataclass(frozen=True)
class RankingScoreContract:
    """Contract metadata for a single ranking score."""

    engine_id: str
    output_key: str
    min_score: float
    max_score: float
    weight: float


def build_button1_ranking_contracts() -> dict[str, RankingScoreContract]:
    """Return contract definitions for all Button 1 ranking engines."""

    return {
        FIGHT_READINESS: RankingScoreContract(FIGHT_READINESS, "fight_readiness_score", 0.0, 100.0, 0.22),
        REPORT_VALUE: RankingScoreContract(REPORT_VALUE, "report_value_score", 0.0, 100.0, 0.16),
        CUSTOMER_PRIORITY: RankingScoreContract(CUSTOMER_PRIORITY, "customer_priority_score", 0.0, 100.0, 0.15),
        EVENT_CARD_PRIORITY: RankingScoreContract(EVENT_CARD_PRIORITY, "event_card_priority_score", 0.0, 100.0, 0.12),
        BETTING_INTEREST: RankingScoreContract(BETTING_INTEREST, "betting_interest_score", 0.0, 100.0, 0.12),
        COMMERCIAL_SELLABILITY: RankingScoreContract(COMMERCIAL_SELLABILITY, "commercial_sellability_score", 0.0, 100.0, 0.12),
        ANALYSIS_CONFIDENCE: RankingScoreContract(ANALYSIS_CONFIDENCE, "analysis_confidence_score", 0.0, 100.0, 0.11),
    }


def validate_ranking_scores(
    ranking_scores: dict,
    contracts: dict[str, RankingScoreContract] | None = None,
) -> dict:
    """Validate ranking score payload against contract completeness and range."""

    score_contracts = contracts or build_button1_ranking_contracts()
    missing_engines = []
    unknown_engines = []
    out_of_range = []

    for engine_id in score_contracts:
        if engine_id not in ranking_scores:
            missing_engines.append(engine_id)

    for engine_id, score in ranking_scores.items():
        contract = score_contracts.get(engine_id)
        if contract is None:
            unknown_engines.append(engine_id)
            continue

        try:
            numeric_score = float(score)
        except Exception:
            out_of_range.append(engine_id)
            continue

        if numeric_score < contract.min_score or numeric_score > contract.max_score:
            out_of_range.append(engine_id)

    ok = not missing_engines and not unknown_engines and not out_of_range
    return {
        "ok": ok,
        "missing_engines": sorted(missing_engines),
        "unknown_engines": sorted(unknown_engines),
        "out_of_range_engines": sorted(out_of_range),
    }


def compute_composite_ranking_score(
    ranking_scores: dict,
    contracts: dict[str, RankingScoreContract] | None = None,
) -> float:
    """Compute weighted composite ranking score from contract-defined inputs."""

    score_contracts = contracts or build_button1_ranking_contracts()
    total = 0.0
    for engine_id, contract in score_contracts.items():
        score = float(ranking_scores.get(engine_id, 0.0))
        total += score * contract.weight
    return round(total, 4)


def build_ranked_matchup_rows(matchup_rows: list[dict]) -> list[dict]:
    """
    Build deterministic ranked rows from contract-compliant matchup score payloads.

    Expected per-row input:
    - matchup_id
    - ranking_scores: dict[engine_id -> numeric_score]
    """

    contracts = build_button1_ranking_contracts()
    ranked = []

    for row in matchup_rows:
        matchup_id = str(row.get("matchup_id") or "").strip()
        scores = row.get("ranking_scores") or {}
        validation = validate_ranking_scores(scores, contracts)
        composite = compute_composite_ranking_score(scores, contracts)

        ranked.append(
            {
                "matchup_id": matchup_id,
                "ranking_scores": scores,
                "ranking_validation": validation,
                "composite_ranking_score": composite,
                "rank_ready": validation["ok"],
            }
        )

    ranked.sort(
        key=lambda item: (
            not item["rank_ready"],
            -item["composite_ranking_score"],
            item["matchup_id"],
        )
    )
    return ranked
