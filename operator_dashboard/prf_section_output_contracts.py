"""
Premium Report Factory section-output contracts scaffold.

Defines deterministic contract mappings from global engine-pack outputs
(Combat Intelligence and Fighters Analytics) into the 14 premium report
sections. This module is scaffold-only and does not execute engines.
"""

from dataclasses import dataclass


PREMIUM_REPORT_SECTION_NAMES = (
    "cover_page",
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


@dataclass(frozen=True)
class SectionOutputContract:
    """Contract for section population requirements and contributor engines."""

    section_name: str
    required_engine_ids: tuple[str, ...]
    optional_engine_ids: tuple[str, ...]
    required_output_keys: tuple[str, ...]


def build_combat_intelligence_section_output_contracts() -> dict[str, SectionOutputContract]:
    """Return section contracts keyed by premium section name."""

    # Contract IDs are intentionally registry-aligned and execution-agnostic.
    contracts = {
        "cover_page": SectionOutputContract(
            section_name="cover_page",
            required_engine_ids=(),
            optional_engine_ids=(
                "combat_intelligence.report_readiness",
                "fighters_analytics.tactical_keys",
            ),
            required_output_keys=(),
        ),
        "headline_prediction": SectionOutputContract(
            section_name="headline_prediction",
            required_engine_ids=(
                "fighters_analytics.win_method_probability",
                "combat_intelligence.method_probability",
            ),
            optional_engine_ids=(
                "combat_intelligence.confidence_quality",
                "combat_intelligence.volatility_upset_lane",
            ),
            required_output_keys=("winner", "confidence", "method"),
        ),
        "executive_summary": SectionOutputContract(
            section_name="executive_summary",
            required_engine_ids=(
                "fighters_analytics.tactical_keys",
                "combat_intelligence.fighter_architecture",
            ),
            optional_engine_ids=(
                "combat_intelligence.confidence_quality",
                "combat_intelligence.report_readiness",
            ),
            required_output_keys=("summary_core",),
        ),
        "matchup_snapshot": SectionOutputContract(
            section_name="matchup_snapshot",
            required_engine_ids=(
                "fighters_analytics.pace_pressure_fatigue_range",
                "combat_intelligence.range_geography",
            ),
            optional_engine_ids=(
                "combat_intelligence.fighter_embedding_similarity",
            ),
            required_output_keys=("matchup_snapshot",),
        ),
        "decision_structure": SectionOutputContract(
            section_name="decision_structure",
            required_engine_ids=(
                "fighters_analytics.decision_structure",
                "combat_intelligence.decision_structure",
            ),
            optional_engine_ids=(
                "combat_intelligence.pattern_memory",
            ),
            required_output_keys=("decision_structure",),
        ),
        "energy_use": SectionOutputContract(
            section_name="energy_use",
            required_engine_ids=(
                "fighters_analytics.energy_use",
                "combat_intelligence.energy_economy",
            ),
            optional_engine_ids=(
                "fighters_analytics.energy_waste",
            ),
            required_output_keys=("energy_profile",),
        ),
        "fatigue_failure_points": SectionOutputContract(
            section_name="fatigue_failure_points",
            required_engine_ids=(
                "fighters_analytics.fatigue_failure_point",
                "combat_intelligence.fatigue_failure_point",
            ),
            optional_engine_ids=(),
            required_output_keys=("fatigue_failure_points",),
        ),
        "mental_condition": SectionOutputContract(
            section_name="mental_condition",
            required_engine_ids=(
                "fighters_analytics.mental_condition",
                "combat_intelligence.mental_condition",
            ),
            optional_engine_ids=(
                "fighters_analytics.composure_under_stress",
                "fighters_analytics.predictability_under_stress",
            ),
            required_output_keys=("mental_condition",),
        ),
        "collapse_triggers": SectionOutputContract(
            section_name="collapse_triggers",
            required_engine_ids=(
                "fighters_analytics.collapse_trigger",
                "combat_intelligence.collapse_trigger",
            ),
            optional_engine_ids=(
                "fighters_analytics.stoppage_trigger",
                "combat_intelligence.stoppage_sensitivity",
            ),
            required_output_keys=("collapse_triggers",),
        ),
        "deception_and_unpredictability": SectionOutputContract(
            section_name="deception_and_unpredictability",
            required_engine_ids=(
                "combat_intelligence.deception_unpredictability",
            ),
            optional_engine_ids=(
                "fighters_analytics.tactical_keys",
                "fighters_analytics.predictability_under_stress",
            ),
            required_output_keys=("deception_unpredictability",),
        ),
        "round_by_round_control_shifts": SectionOutputContract(
            section_name="round_by_round_control_shifts",
            required_engine_ids=(
                "fighters_analytics.early_mid_late_projection",
                "combat_intelligence.round_band_projection",
            ),
            optional_engine_ids=(
                "combat_intelligence.live_adaptation_momentum",
            ),
            required_output_keys=("round_control_projection",),
        ),
        "scenario_tree": SectionOutputContract(
            section_name="scenario_tree",
            required_engine_ids=(
                "fighters_analytics.scorecard_scenario",
                "combat_intelligence.scorecard_scenario",
            ),
            optional_engine_ids=(
                "combat_intelligence.volatility_upset_lane",
            ),
            required_output_keys=("scenario_tree",),
        ),
        "risk_warnings": SectionOutputContract(
            section_name="risk_warnings",
            required_engine_ids=(
                "combat_intelligence.confidence_quality",
            ),
            optional_engine_ids=(
                "fighters_analytics.sparse_case_result_completion",
                "combat_intelligence.sparse_case_result_completion",
            ),
            required_output_keys=("risk_warnings",),
        ),
        "operator_notes": SectionOutputContract(
            section_name="operator_notes",
            required_engine_ids=(),
            optional_engine_ids=(
                "combat_intelligence.report_readiness",
            ),
            required_output_keys=(),
        ),
    }
    return contracts


def evaluate_required_section_engine_outputs(
    contracts: dict[str, SectionOutputContract],
    engine_output_keys_by_engine: dict[str, set[str]],
) -> dict[str, dict]:
    """
    Evaluate required engine/output-key readiness per section.

    Returns a dict keyed by section containing:
    - ready: bool
    - missing_required_engines: list[str]
    - missing_required_output_keys: list[str]
    """

    readiness = {}
    for section_name, contract in contracts.items():
        missing_engines = [
            engine_id
            for engine_id in contract.required_engine_ids
            if engine_id not in engine_output_keys_by_engine
        ]

        available_output_keys = set()
        for engine_id in contract.required_engine_ids:
            available_output_keys.update(engine_output_keys_by_engine.get(engine_id, set()))

        missing_output_keys = [
            output_key
            for output_key in contract.required_output_keys
            if output_key not in available_output_keys
        ]

        readiness[section_name] = {
            "ready": not missing_engines and not missing_output_keys,
            "missing_required_engines": missing_engines,
            "missing_required_output_keys": missing_output_keys,
        }

    return readiness


def list_sections_missing_required_outputs(
    contracts: dict[str, SectionOutputContract],
    engine_output_keys_by_engine: dict[str, set[str]],
) -> list[str]:
    """Return section names that are not ready under required-contract rules."""

    readiness = evaluate_required_section_engine_outputs(
        contracts=contracts,
        engine_output_keys_by_engine=engine_output_keys_by_engine,
    )
    return [
        section_name
        for section_name in PREMIUM_REPORT_SECTION_NAMES
        if section_name in readiness and not readiness[section_name]["ready"]
    ]
