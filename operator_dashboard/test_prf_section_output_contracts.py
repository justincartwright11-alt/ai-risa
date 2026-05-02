import unittest

from operator_dashboard.prf_section_output_contracts import (
    PREMIUM_REPORT_SECTION_NAMES,
    build_combat_intelligence_section_output_contracts,
    evaluate_required_section_engine_outputs,
    list_sections_missing_required_outputs,
)


class TestPrfSectionOutputContracts(unittest.TestCase):
    def test_contracts_cover_all_14_premium_sections(self):
        contracts = build_combat_intelligence_section_output_contracts()
        self.assertEqual(set(contracts.keys()), set(PREMIUM_REPORT_SECTION_NAMES))
        self.assertEqual(len(contracts), 14)

    def test_key_sections_have_expected_required_engine_contracts(self):
        contracts = build_combat_intelligence_section_output_contracts()

        headline = contracts["headline_prediction"]
        self.assertIn("fighters_analytics.win_method_probability", headline.required_engine_ids)
        self.assertIn("combat_intelligence.method_probability", headline.required_engine_ids)
        self.assertEqual(headline.required_output_keys, ("winner", "confidence", "method"))

        decision = contracts["decision_structure"]
        self.assertIn("fighters_analytics.decision_structure", decision.required_engine_ids)
        self.assertIn("combat_intelligence.decision_structure", decision.required_engine_ids)

    def test_readiness_flags_missing_required_engines(self):
        contracts = build_combat_intelligence_section_output_contracts()
        readiness = evaluate_required_section_engine_outputs(contracts, {})

        self.assertFalse(readiness["headline_prediction"]["ready"])
        self.assertIn(
            "fighters_analytics.win_method_probability",
            readiness["headline_prediction"]["missing_required_engines"],
        )
        self.assertFalse(readiness["decision_structure"]["ready"])

    def test_readiness_passes_with_minimum_required_outputs(self):
        contracts = build_combat_intelligence_section_output_contracts()
        engine_output_keys_by_engine = {
            "fighters_analytics.win_method_probability": {"winner", "confidence", "method"},
            "combat_intelligence.method_probability": {"method_probability"},
            "fighters_analytics.tactical_keys": {"summary_core"},
            "combat_intelligence.fighter_architecture": {"summary_core"},
            "fighters_analytics.pace_pressure_fatigue_range": {"matchup_snapshot"},
            "combat_intelligence.range_geography": {"matchup_snapshot"},
            "fighters_analytics.decision_structure": {"decision_structure"},
            "combat_intelligence.decision_structure": {"decision_structure"},
            "fighters_analytics.energy_use": {"energy_profile"},
            "combat_intelligence.energy_economy": {"energy_profile"},
            "fighters_analytics.fatigue_failure_point": {"fatigue_failure_points"},
            "combat_intelligence.fatigue_failure_point": {"fatigue_failure_points"},
            "fighters_analytics.mental_condition": {"mental_condition"},
            "combat_intelligence.mental_condition": {"mental_condition"},
            "fighters_analytics.collapse_trigger": {"collapse_triggers"},
            "combat_intelligence.collapse_trigger": {"collapse_triggers"},
            "combat_intelligence.deception_unpredictability": {"deception_unpredictability"},
            "fighters_analytics.early_mid_late_projection": {"round_control_projection"},
            "combat_intelligence.round_band_projection": {"round_control_projection"},
            "fighters_analytics.scorecard_scenario": {"scenario_tree"},
            "combat_intelligence.scorecard_scenario": {"scenario_tree"},
            "combat_intelligence.confidence_quality": {"risk_warnings"},
        }

        readiness = evaluate_required_section_engine_outputs(
            contracts,
            engine_output_keys_by_engine,
        )
        missing_sections = list_sections_missing_required_outputs(
            contracts,
            engine_output_keys_by_engine,
        )

        self.assertTrue(readiness["headline_prediction"]["ready"])
        self.assertTrue(readiness["scenario_tree"]["ready"])
        self.assertEqual(missing_sections, [])

    def test_missing_required_output_key_blocks_section(self):
        contracts = build_combat_intelligence_section_output_contracts()
        engine_output_keys_by_engine = {
            "fighters_analytics.win_method_probability": {"winner", "confidence"},
            "combat_intelligence.method_probability": {"method_probability"},
        }

        readiness = evaluate_required_section_engine_outputs(
            contracts,
            engine_output_keys_by_engine,
        )
        self.assertFalse(readiness["headline_prediction"]["ready"])
        self.assertIn("method", readiness["headline_prediction"]["missing_required_output_keys"])


if __name__ == "__main__":
    unittest.main()
