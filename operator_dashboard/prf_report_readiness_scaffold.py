"""
Premium Report Factory report-readiness and sparse-completion scaffold contracts.

This module is contract-only. It defines deterministic readiness evaluation
rules and sparse-case completion requirements without executing live engines
or mutating runtime behavior.
"""

from dataclasses import dataclass

DEFAULT_PLACEHOLDER_TOKENS = (
    "unavailable",
    "not available",
    "pending",
    "tbd",
    "no operator notes recorded",
    "insufficient data",
    "content will be enriched later",
    "prediction unavailable",
    "analysis unavailable",
)

DEFAULT_REQUIRED_SECTIONS = (
    "headline_prediction",
    "executive_summary",
    "matchup_snapshot",
    "decision_structure",
    "energy_use",
    "fatigue_failure_points",
    "mental_condition",
    "collapse_triggers",
    "deception_and_unpredictability",
    "round_by_round_control_shifts",
    "scenario_tree",
    "risk_warnings",
    "operator_notes",
)

SPARSE_REQUIRED_FIELDS = (
    "winner",
    "confidence",
    "method",
    "round",
    "debug_metrics",
)

STATUS_CUSTOMER_READY = "customer_ready"
STATUS_DRAFT_ONLY = "draft_only"
STATUS_BLOCKED_MISSING_ANALYSIS = "blocked_missing_analysis"


@dataclass(frozen=True)
class ReportReadinessContract:
    """Required section and placeholder policy for readiness evaluation."""

    required_sections: tuple[str, ...] = DEFAULT_REQUIRED_SECTIONS
    placeholder_tokens: tuple[str, ...] = DEFAULT_PLACEHOLDER_TOKENS


@dataclass(frozen=True)
class SparseCaseCompletionContract:
    """Required sparse-case completion fields before final promotion."""

    required_fields: tuple[str, ...] = SPARSE_REQUIRED_FIELDS


def contains_placeholder_text(
    value: str,
    placeholder_tokens: tuple[str, ...] = DEFAULT_PLACEHOLDER_TOKENS,
) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return True
    return any(token in normalized for token in placeholder_tokens)


def detect_missing_required_sections(
    sections: dict,
    contract: ReportReadinessContract | None = None,
) -> list[str]:
    rule_contract = contract or ReportReadinessContract()
    missing_sections = []
    for section_name in rule_contract.required_sections:
        content = sections.get(section_name)
        if contains_placeholder_text(content, rule_contract.placeholder_tokens):
            missing_sections.append(section_name)
    return missing_sections


def evaluate_sparse_case_completion(
    payload: dict,
    contract: SparseCaseCompletionContract | None = None,
) -> dict:
    rule_contract = contract or SparseCaseCompletionContract()
    missing_fields = []

    for field_name in rule_contract.required_fields:
        value = payload.get(field_name)
        if field_name == "debug_metrics":
            if not isinstance(value, dict):
                missing_fields.append(field_name)
            continue

        if isinstance(value, str):
            if not value.strip():
                missing_fields.append(field_name)
            continue
        if value is None:
            missing_fields.append(field_name)
            continue

    return {
        "ready": not missing_fields,
        "missing_fields": missing_fields,
    }


def evaluate_report_readiness_status(
    analysis_source_status: str,
    allow_draft: bool,
    missing_sections: list[str],
    sparse_completion_ready: bool,
) -> dict:
    """
    Evaluate scaffold readiness status using contract-only rules.

    Returns a dict with:
    - report_quality_status
    - customer_ready
    - reason_code
    """

    source_found = str(analysis_source_status or "").strip().lower() == "found"

    if source_found and not missing_sections and sparse_completion_ready:
        return {
            "report_quality_status": STATUS_CUSTOMER_READY,
            "customer_ready": True,
            "reason_code": "all_required_outputs_present",
        }

    if allow_draft:
        return {
            "report_quality_status": STATUS_DRAFT_ONLY,
            "customer_ready": False,
            "reason_code": "draft_mode_or_missing_required_outputs",
        }

    return {
        "report_quality_status": STATUS_BLOCKED_MISSING_ANALYSIS,
        "customer_ready": False,
        "reason_code": "missing_required_outputs_or_analysis",
    }
