import unittest

from operator_dashboard.prf_engine_registry import (
    BUTTON_1,
    BUTTON_2,
    BUTTON_3,
    ADVANCED_DASHBOARD,
    EngineContract,
    EngineRegistry,
    build_global_engine_pack_registry,
)


class TestPrfEngineRegistry(unittest.TestCase):
    def test_default_registry_has_expected_groups(self):
        registry = build_global_engine_pack_registry()
        self.assertEqual(
            registry.groups(),
            [
                "betting_market",
                "combat_intelligence",
                "fighters_analytics",
                "generation",
                "global_ledger",
                "ranking",
            ],
        )

    def test_default_registry_contract_count_is_stable(self):
        registry = build_global_engine_pack_registry()
        self.assertEqual(registry.count(), 85)

    def test_known_contract_contains_expected_fields(self):
        registry = build_global_engine_pack_registry()
        contract = registry.get("fighters_analytics.sparse_case_result_completion")
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract.engine_group, "fighters_analytics")
        self.assertEqual(
            contract.required_outputs,
            ("winner", "confidence", "method", "round", "debug_metrics"),
        )
        self.assertEqual(contract.buttons, (BUTTON_2,))

    def test_registry_rejects_duplicate_engine_id(self):
        registry = EngineRegistry()
        contract = EngineContract(
            engine_id="test.engine",
            engine_group="test_group",
            display_name="Test Engine",
            buttons=(BUTTON_1,),
            required_inputs=("workflow_context",),
            required_outputs=("out",),
        )
        registry.register(contract)
        with self.assertRaises(ValueError):
            registry.register(contract)

    def test_registry_rejects_unknown_button(self):
        registry = EngineRegistry()
        contract = EngineContract(
            engine_id="test.engine",
            engine_group="test_group",
            display_name="Test Engine",
            buttons=("button_9",),
            required_inputs=("workflow_context",),
            required_outputs=("out",),
        )
        with self.assertRaises(ValueError):
            registry.register(contract)

    def test_button_filters_return_expected_examples(self):
        registry = build_global_engine_pack_registry()

        button_1_ids = {c.engine_id for c in registry.list_by_button(BUTTON_1)}
        self.assertIn("ranking.fight_readiness", button_1_ids)
        self.assertIn("global_ledger.fighter_database", button_1_ids)

        button_3_ids = {c.engine_id for c in registry.list_by_button(BUTTON_3)}
        self.assertIn("global_ledger.accuracy_ledger", button_3_ids)
        self.assertIn("combat_intelligence.calibration_recommendation", button_3_ids)

        advanced_ids = {c.engine_id for c in registry.list_by_button(ADVANCED_DASHBOARD)}
        self.assertIn("combat_intelligence.live_adaptation_momentum", advanced_ids)


if __name__ == "__main__":
    unittest.main()
