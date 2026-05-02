import unittest

from operator_dashboard.prf_global_ledger_scaffold import (
    DUPLICATE_CONFLICT_RESOLUTION,
    GLOBAL_EVENT_CARD_DATABASE,
    GLOBAL_FIGHTER_DATABASE,
    GLOBAL_LEDGER_ENGINE_IDS,
    GLOBAL_MATCHUP_DATABASE,
    GLOBAL_REPORT_LEDGER,
    SOURCE_PROVENANCE,
    build_global_ledger_contracts,
    evaluate_global_ledger_gate,
    validate_global_ledger_outputs,
)


class TestPrfGlobalLedgerScaffold(unittest.TestCase):
    def test_contracts_cover_all_requested_global_ledger_engines(self):
        contracts = build_global_ledger_contracts()
        self.assertEqual(set(contracts.keys()), set(GLOBAL_LEDGER_ENGINE_IDS))
        self.assertEqual(len(contracts), 9)

    def test_validation_detects_missing_required_engines(self):
        validation = validate_global_ledger_outputs({}, operator_approval=True)
        self.assertFalse(validation["ok"])
        self.assertIn(GLOBAL_FIGHTER_DATABASE, validation["missing_required_engines"])
        self.assertIn(SOURCE_PROVENANCE, validation["missing_required_engines"])

    def test_validation_detects_approval_gate_violations(self):
        outputs = {
            GLOBAL_FIGHTER_DATABASE: {"fighter_record": {"fighter_id": "f1"}},
            GLOBAL_MATCHUP_DATABASE: {"matchup_record": {"matchup_id": "m1"}},
            GLOBAL_EVENT_CARD_DATABASE: {"event_card_record": {"event_id": "e1"}},
            GLOBAL_REPORT_LEDGER: {"report_ledger_row": {"report_id": "r1"}},
            DUPLICATE_CONFLICT_RESOLUTION: {"conflict_resolution": {"status": "clear"}},
            SOURCE_PROVENANCE: {"provenance_refs": ["src1"]},
        }
        validation = validate_global_ledger_outputs(outputs, operator_approval=False)
        self.assertFalse(validation["ok"])
        self.assertIn(GLOBAL_FIGHTER_DATABASE, validation["approval_gate_violations"])
        self.assertNotIn(SOURCE_PROVENANCE, validation["approval_gate_violations"])

    def test_validation_passes_with_minimum_required_payload_and_approval(self):
        outputs = {
            GLOBAL_FIGHTER_DATABASE: {"fighter_record": {"fighter_id": "f1"}},
            GLOBAL_MATCHUP_DATABASE: {"matchup_record": {"matchup_id": "m1"}},
            GLOBAL_EVENT_CARD_DATABASE: {"event_card_record": {"event_id": "e1"}},
            GLOBAL_REPORT_LEDGER: {"report_ledger_row": {"report_id": "r1"}},
            DUPLICATE_CONFLICT_RESOLUTION: {"conflict_resolution": {"status": "clear"}},
            SOURCE_PROVENANCE: {"provenance_refs": ["src1"]},
        }
        validation = validate_global_ledger_outputs(outputs, operator_approval=True)
        self.assertTrue(validation["ok"])

    def test_gate_reason_codes(self):
        outputs = {
            SOURCE_PROVENANCE: {"provenance_refs": ["src1"]},
        }
        gate = evaluate_global_ledger_gate(outputs, operator_approval=False)
        self.assertFalse(gate["global_ledger_gate_ready"])
        self.assertEqual(gate["reason_code"], "operator_approval_required")

        gate_missing = evaluate_global_ledger_gate({}, operator_approval=True)
        self.assertFalse(gate_missing["global_ledger_gate_ready"])
        self.assertEqual(gate_missing["reason_code"], "missing_required_global_ledger_contract_outputs")


if __name__ == "__main__":
    unittest.main()
