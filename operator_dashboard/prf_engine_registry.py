"""
Premium Report Factory global engine-pack registry scaffold.

This module defines engine contract structures and a deterministic registry
for the phased global engine-pack rollout. It is intentionally scaffold-only:
no engine execution behavior is implemented here.
"""

from dataclasses import dataclass
from typing import Iterable

BUTTON_1 = "button_1"
BUTTON_2 = "button_2"
BUTTON_3 = "button_3"
ADVANCED_DASHBOARD = "advanced_dashboard"

ALLOWED_BUTTONS = (BUTTON_1, BUTTON_2, BUTTON_3, ADVANCED_DASHBOARD)


@dataclass(frozen=True)
class EngineContract:
    """Normalized contract metadata for a single engine."""

    engine_id: str
    engine_group: str
    display_name: str
    buttons: tuple[str, ...]
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    output_schema_version: str = "v1"
    approval_gate_required: bool = False


class EngineRegistry:
    """Deterministic in-memory registry for engine contracts."""

    def __init__(self) -> None:
        self._contracts: dict[str, EngineContract] = {}

    def register(self, contract: EngineContract) -> None:
        if contract.engine_id in self._contracts:
            raise ValueError("duplicate_engine_id: {}".format(contract.engine_id))
        unknown_buttons = [b for b in contract.buttons if b not in ALLOWED_BUTTONS]
        if unknown_buttons:
            raise ValueError("unknown_buttons: {}".format(",".join(unknown_buttons)))
        self._contracts[contract.engine_id] = contract

    def register_many(self, contracts: Iterable[EngineContract]) -> None:
        for contract in contracts:
            self.register(contract)

    def get(self, engine_id: str) -> EngineContract | None:
        return self._contracts.get(str(engine_id or "").strip())

    def list_all(self) -> list[EngineContract]:
        return [self._contracts[key] for key in sorted(self._contracts)]

    def list_by_group(self, engine_group: str) -> list[EngineContract]:
        group = str(engine_group or "").strip()
        return [
            contract
            for contract in self.list_all()
            if contract.engine_group == group
        ]

    def list_by_button(self, button: str) -> list[EngineContract]:
        button_name = str(button or "").strip()
        return [
            contract
            for contract in self.list_all()
            if button_name in contract.buttons
        ]

    def groups(self) -> list[str]:
        return sorted({contract.engine_group for contract in self._contracts.values()})

    def count(self) -> int:
        return len(self._contracts)

    def to_manifest_rows(self) -> list[dict]:
        rows = []
        for contract in self.list_all():
            rows.append(
                {
                    "engine_id": contract.engine_id,
                    "engine_group": contract.engine_group,
                    "display_name": contract.display_name,
                    "buttons": list(contract.buttons),
                    "required_inputs": list(contract.required_inputs),
                    "required_outputs": list(contract.required_outputs),
                    "output_schema_version": contract.output_schema_version,
                    "approval_gate_required": contract.approval_gate_required,
                }
            )
        return rows


def _contract(
    engine_id: str,
    engine_group: str,
    display_name: str,
    buttons: tuple[str, ...],
    required_outputs: tuple[str, ...],
    approval_gate_required: bool = False,
) -> EngineContract:
    return EngineContract(
        engine_id=engine_id,
        engine_group=engine_group,
        display_name=display_name,
        buttons=buttons,
        required_inputs=("workflow_context",),
        required_outputs=required_outputs,
        output_schema_version="v1",
        approval_gate_required=approval_gate_required,
    )


def build_global_engine_pack_registry() -> EngineRegistry:
    """Build the default scaffold registry for global engine-pack planning."""

    fighters_analytics = [
        _contract("fighters_analytics.tactical_keys", "fighters_analytics", "Tactical Keys Engine", (BUTTON_2,), ("tactical_keys",)),
        _contract("fighters_analytics.dominance_danger_zone", "fighters_analytics", "Dominance / Danger Zone Engine", (BUTTON_2,), ("dominance_danger_zone",)),
        _contract("fighters_analytics.pace_pressure_fatigue_range", "fighters_analytics", "Pace / Pressure / Fatigue / Range Engine", (BUTTON_2,), ("pace_pressure_fatigue_range",)),
        _contract("fighters_analytics.early_mid_late_projection", "fighters_analytics", "Early / Mid / Late Fight Projection Engine", (BUTTON_2,), ("early_mid_late_projection",)),
        _contract("fighters_analytics.stoppage_trigger", "fighters_analytics", "Stoppage Trigger Engine", (BUTTON_2,), ("stoppage_trigger",)),
        _contract("fighters_analytics.scorecard_scenario", "fighters_analytics", "Scorecard Scenario Engine", (BUTTON_2,), ("scorecard_scenario",)),
        _contract("fighters_analytics.win_method_probability", "fighters_analytics", "Win / Method Probability Engine", (BUTTON_2,), ("win_method_probability",)),
        _contract("fighters_analytics.decision_structure", "fighters_analytics", "Decision Structure Engine", (BUTTON_2,), ("decision_structure",)),
        _contract("fighters_analytics.energy_use", "fighters_analytics", "Energy Use Engine", (BUTTON_2,), ("energy_use",)),
        _contract("fighters_analytics.fatigue_failure_point", "fighters_analytics", "Fatigue Failure Point Engine", (BUTTON_2,), ("fatigue_failure_point",)),
        _contract("fighters_analytics.mental_condition", "fighters_analytics", "Mental Condition Engine", (BUTTON_2,), ("mental_condition",)),
        _contract("fighters_analytics.collapse_trigger", "fighters_analytics", "Collapse Trigger Engine", (BUTTON_2,), ("collapse_trigger",)),
        _contract("fighters_analytics.pressure_management", "fighters_analytics", "Pressure Management Engine", (BUTTON_2,), ("pressure_management",)),
        _contract("fighters_analytics.energy_waste", "fighters_analytics", "Energy Waste Engine", (BUTTON_2,), ("energy_waste",)),
        _contract("fighters_analytics.composure_under_stress", "fighters_analytics", "Composure Under Stress Engine", (BUTTON_2,), ("composure_under_stress",)),
        _contract("fighters_analytics.predictability_under_stress", "fighters_analytics", "Predictability Under Stress Engine", (BUTTON_2,), ("predictability_under_stress",)),
        _contract("fighters_analytics.late_fight_decision", "fighters_analytics", "Late-Fight Decision Engine", (BUTTON_2,), ("late_fight_decision",)),
        _contract("fighters_analytics.sparse_case_result_completion", "fighters_analytics", "Sparse-Case Result Completion Engine", (BUTTON_2,), ("winner", "confidence", "method", "round", "debug_metrics")),
    ]

    global_ledger = [
        _contract("global_ledger.fighter_database", "global_ledger", "Global Fighter Database Engine", (BUTTON_1,), ("fighter_record",), True),
        _contract("global_ledger.matchup_database", "global_ledger", "Global Matchup Database Engine", (BUTTON_1,), ("matchup_record",), True),
        _contract("global_ledger.event_card_database", "global_ledger", "Global Event Card Database Engine", (BUTTON_1,), ("event_card_record",), True),
        _contract("global_ledger.result_ledger", "global_ledger", "Global Result Ledger Engine", (BUTTON_3,), ("result_ledger_row",), True),
        _contract("global_ledger.report_ledger", "global_ledger", "Global Report Ledger Engine", (BUTTON_2, BUTTON_3), ("report_ledger_row",), True),
        _contract("global_ledger.accuracy_ledger", "global_ledger", "Global Accuracy Ledger Engine", (BUTTON_3,), ("accuracy_ledger_row",), True),
        _contract("global_ledger.calibration_ledger", "global_ledger", "Global Calibration Ledger Engine", (BUTTON_3,), ("calibration_ledger_row",), True),
        _contract("global_ledger.duplicate_conflict_resolution", "global_ledger", "Duplicate / Conflict Resolution Engine", (BUTTON_1, ADVANCED_DASHBOARD), ("conflict_resolution",), True),
        _contract("global_ledger.source_provenance", "global_ledger", "Source Provenance Engine", (BUTTON_1, BUTTON_2, BUTTON_3), ("provenance_refs",)),
    ]

    ranking = [
        _contract("ranking.fight_readiness", "ranking", "Fight Readiness Ranking Engine", (BUTTON_1, BUTTON_2), ("fight_readiness_score",)),
        _contract("ranking.report_value", "ranking", "Report Value Ranking Engine", (BUTTON_1,), ("report_value_score",)),
        _contract("ranking.customer_priority", "ranking", "Customer Priority Ranking Engine", (BUTTON_1,), ("customer_priority_score",)),
        _contract("ranking.event_card_priority", "ranking", "Event Card Priority Ranking Engine", (BUTTON_1,), ("event_card_priority_score",)),
        _contract("ranking.betting_interest", "ranking", "Betting Interest Ranking Engine", (BUTTON_1, BUTTON_2), ("betting_interest_score",)),
        _contract("ranking.commercial_sellability", "ranking", "Commercial Sellability Ranking Engine", (BUTTON_1,), ("commercial_sellability_score",)),
        _contract("ranking.analysis_confidence", "ranking", "Analysis Confidence Ranking Engine", (BUTTON_1, BUTTON_2), ("analysis_confidence_score",)),
    ]

    betting = [
        _contract("betting.odds_ingestion", "betting_market", "Odds Ingestion Engine", (BUTTON_2,), ("odds_snapshot",)),
        _contract("betting.implied_probability", "betting_market", "Implied Probability Engine", (BUTTON_2,), ("implied_probability",)),
        _contract("betting.fair_price", "betting_market", "Fair Price Engine", (BUTTON_2,), ("fair_price",)),
        _contract("betting.market_edge", "betting_market", "Market Edge Engine", (BUTTON_2,), ("market_edge",)),
        _contract("betting.prop_market", "betting_market", "Prop Market Engine", (BUTTON_2,), ("prop_market_pathways",)),
        _contract("betting.volatility_grade", "betting_market", "Volatility Grade Engine", (BUTTON_2,), ("volatility_grade",)),
        _contract("betting.round_band_path", "betting_market", "Round-Band Betting Path Engine", (BUTTON_2,), ("round_band_path",)),
        _contract("betting.pass_no_bet", "betting_market", "Pass / No-Bet Condition Engine", (BUTTON_2,), ("pass_no_bet_condition",)),
        _contract("betting.market_movement_watch", "betting_market", "Market Movement Watch Engine", (BUTTON_2, ADVANCED_DASHBOARD), ("market_movement_signal",)),
        _contract("betting.risk_disclaimer", "betting_market", "Betting Risk Disclaimer Engine", (BUTTON_2,), ("betting_risk_disclaimer",)),
    ]

    generation = [
        _contract("generation.premium_pdf", "generation", "Premium PDF Generation Engine", (BUTTON_2,), ("premium_pdf_artifact",)),
        _contract("generation.event_card_pack", "generation", "Event-Card Report Pack Generator", (BUTTON_2,), ("event_card_pack",)),
        _contract("generation.single_matchup", "generation", "Single-Matchup Report Generator", (BUTTON_2,), ("single_matchup_report",)),
        _contract("generation.fighter_profile", "generation", "Fighter Profile Generator", (BUTTON_2,), ("fighter_profile_report",)),
        _contract("generation.betting_analyst_brief", "generation", "Betting Analyst Brief Generator", (BUTTON_2,), ("betting_analyst_brief",)),
        _contract("generation.broadcast_analyst_pack", "generation", "Broadcast Analyst Pack Generator", (BUTTON_2,), ("broadcast_analyst_pack",)),
        _contract("generation.coach_gym_scouting", "generation", "Coach / Gym Scouting Report Generator", (BUTTON_2,), ("coach_gym_scouting_report",)),
        _contract("generation.promoter_manager_decision_brief", "generation", "Promoter / Manager Decision Brief Generator", (BUTTON_2,), ("promoter_manager_decision_brief",)),
        _contract("generation.visual_generation", "generation", "Visual Generation Engine", (BUTTON_2,), ("visual_bundle",)),
        _contract("generation.radar_metric", "generation", "Radar Metric Engine", (BUTTON_2,), ("radar_metric",)),
        _contract("generation.round_heat_map", "generation", "Round Heat Map Engine", (BUTTON_2,), ("round_heat_map",)),
        _contract("generation.control_shift_graph", "generation", "Control-Shift Graph Engine", (BUTTON_2,), ("control_shift_graph",)),
        _contract("generation.method_probability_chart", "generation", "Method Probability Chart Engine", (BUTTON_2,), ("method_probability_chart",)),
        _contract("generation.customer_ready_qa", "generation", "Customer-Ready QA Engine", (BUTTON_2,), ("qa_gate_decision",)),
        _contract("generation.draft_watermark", "generation", "Draft Watermark Engine", (BUTTON_2,), ("draft_watermark_applied",)),
        _contract("generation.download_export_proof", "generation", "Download / Export Proof Engine", (BUTTON_2,), ("export_proof",)),
    ]

    combat_intel = [
        _contract("combat_intelligence.fighter_architecture", "combat_intelligence", "Fighter Architecture Engine", (BUTTON_2,), ("fighter_architecture",)),
        _contract("combat_intelligence.decision_structure", "combat_intelligence", "Decision Structure Engine", (BUTTON_2,), ("decision_structure",)),
        _contract("combat_intelligence.energy_economy", "combat_intelligence", "Energy Economy Engine", (BUTTON_2,), ("energy_economy",)),
        _contract("combat_intelligence.fatigue_failure_point", "combat_intelligence", "Fatigue Failure Point Engine", (BUTTON_2,), ("fatigue_failure_point",)),
        _contract("combat_intelligence.mental_condition", "combat_intelligence", "Mental Condition Engine", (BUTTON_2,), ("mental_condition",)),
        _contract("combat_intelligence.collapse_trigger", "combat_intelligence", "Collapse Trigger Engine", (BUTTON_2,), ("collapse_trigger",)),
        _contract("combat_intelligence.deception_unpredictability", "combat_intelligence", "Deception and Unpredictability Engine", (BUTTON_2,), ("deception_unpredictability",)),
        _contract("combat_intelligence.range_geography", "combat_intelligence", "Range Geography Engine", (BUTTON_2,), ("range_geography",)),
        _contract("combat_intelligence.dominance_danger_zone", "combat_intelligence", "Dominance Zone / Danger Zone Engine", (BUTTON_2,), ("dominance_danger_zone",)),
        _contract("combat_intelligence.tactical_keys", "combat_intelligence", "Tactical Keys Engine", (BUTTON_2,), ("tactical_keys",)),
        _contract("combat_intelligence.round_band_projection", "combat_intelligence", "Round-Band Projection Engine", (BUTTON_2,), ("round_band_projection",)),
        _contract("combat_intelligence.stoppage_sensitivity", "combat_intelligence", "Stoppage Sensitivity Engine", (BUTTON_2,), ("stoppage_sensitivity",)),
        _contract("combat_intelligence.sparse_case_result_completion", "combat_intelligence", "Sparse-Case Result Completion Engine", (BUTTON_2,), ("winner", "confidence", "method", "round", "debug_metrics")),
        _contract("combat_intelligence.confidence_quality", "combat_intelligence", "Confidence Quality Engine", (BUTTON_2,), ("confidence_quality",)),
        _contract("combat_intelligence.volatility_upset_lane", "combat_intelligence", "Volatility / Upset Lane Engine", (BUTTON_2,), ("volatility_upset_lane",)),
        _contract("combat_intelligence.scorecard_scenario", "combat_intelligence", "Scorecard Scenario Engine", (BUTTON_2,), ("scorecard_scenario",)),
        _contract("combat_intelligence.method_probability", "combat_intelligence", "Method Probability Engine", (BUTTON_2,), ("method_probability",)),
        _contract("combat_intelligence.pattern_memory", "combat_intelligence", "Pattern Memory Engine", (BUTTON_2, ADVANCED_DASHBOARD), ("pattern_memory_refs",)),
        _contract("combat_intelligence.fighter_embedding_similarity", "combat_intelligence", "Fighter Embedding Similarity Engine", (BUTTON_2, ADVANCED_DASHBOARD), ("fighter_embedding_similarity",)),
        _contract("combat_intelligence.report_readiness", "combat_intelligence", "Report Readiness Engine", (BUTTON_1, BUTTON_2), ("report_readiness_score",)),
        _contract("combat_intelligence.visual_intelligence", "combat_intelligence", "Visual Intelligence Engine", (BUTTON_2,), ("visual_intelligence",)),
        _contract("combat_intelligence.audience_specific_output", "combat_intelligence", "Audience-Specific Output Engine", (BUTTON_2,), ("audience_specific_output",)),
        _contract("combat_intelligence.live_adaptation_momentum", "combat_intelligence", "Live Adaptation / Momentum Engine", (ADVANCED_DASHBOARD,), ("live_adaptation_momentum",)),
        _contract("combat_intelligence.accuracy_segment", "combat_intelligence", "Accuracy Segment Engine", (BUTTON_3,), ("accuracy_segment",)),
        _contract("combat_intelligence.calibration_recommendation", "combat_intelligence", "Calibration Recommendation Engine", (BUTTON_3,), ("calibration_recommendation",), True),
    ]

    registry = EngineRegistry()
    registry.register_many(
        fighters_analytics
        + global_ledger
        + ranking
        + betting
        + generation
        + combat_intel
    )
    return registry
