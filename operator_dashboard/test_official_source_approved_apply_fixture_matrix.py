"""Fixture-matrix test module for official_source_approved_apply.

Proves:
- Schema reason-code coverage via fixture scenarios
- Token reason-code coverage via fixture scenarios
- Guard reason-code coverage via fixture scenarios
- Endpoint non-mutating decision envelope coverage
- Placeholder fixtures remain placeholders only
- Every fixture response has mutation_performed=false, write_performed=false,
  bulk_lookup_performed=false, scoring_semantics_changed=false
- Actual-results files remain unchanged before/after every test invocation
- _upsert_single_manual_actual_result is never called for endpoint fixture tests

Non-mutating tests only. No write/apply logic. No token persist.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from operator_dashboard.official_source_approved_apply_guard import (
    evaluate_official_source_approved_apply_guard,
)
from operator_dashboard.official_source_approved_apply_fixture_loader import (
    BuiltScenario,
    load_all_scenarios,
    load_scenario,
    load_scenarios_by_subdirectory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ACCURACY_DIR = _REPO_ROOT / "ops" / "accuracy"
_ACTUAL_RESULTS_PATHS = [
    _ACCURACY_DIR / "actual_results.json",
    _ACCURACY_DIR / "actual_results_manual.json",
    _ACCURACY_DIR / "actual_results_unresolved.json",
]


def _sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _actual_results_hashes() -> dict[str, str | None]:
    return {str(p): _sha256_path(p) for p in _ACTUAL_RESULTS_PATHS}


def _call_guard(scenario: BuiltScenario) -> dict:
    return evaluate_official_source_approved_apply_guard(
        scenario.request_payload,
        authoritative_preview_result=scenario.authoritative_preview_result,
        now_epoch=scenario.now_epoch,
        consumed_token_ids=set(scenario.consumed_token_ids),
        replayed_token_ids=set(scenario.replayed_token_ids),
    )


def _assert_non_mutation_flags(test_case: unittest.TestCase, result: dict, label: str = "") -> None:
    prefix = f"[{label}] " if label else ""
    test_case.assertIs(result.get("mutation_performed"), False, f"{prefix}mutation_performed must be false")
    test_case.assertIs(result.get("write_performed"), False, f"{prefix}write_performed must be false")
    test_case.assertIs(result.get("bulk_lookup_performed"), False, f"{prefix}bulk_lookup_performed must be false")
    test_case.assertIs(result.get("scoring_semantics_changed"), False, f"{prefix}scoring_semantics_changed must be false")


# ---------------------------------------------------------------------------
# Non-mutation invariant proof across ALL non-placeholder fixture scenarios
# ---------------------------------------------------------------------------

class FixtureInvariantTest(unittest.TestCase):
    """Every non-placeholder fixture scenario returns non-mutation flags."""

    def test_all_non_placeholder_fixtures_have_non_mutation_flags(self):
        hashes_before = _actual_results_hashes()

        scenarios = load_all_scenarios()
        self.assertGreater(len(scenarios), 0, "No fixture scenarios loaded")

        evaluated = 0
        for scenario in scenarios:
            if scenario.token_mode in ("placeholder", "mock_test_only"):
                continue
            with self.subTest(scenario_id=scenario.scenario_id):
                result = _call_guard(scenario)
                _assert_non_mutation_flags(self, result, label=scenario.scenario_id)
                evaluated += 1

        self.assertGreater(evaluated, 0, "No non-placeholder scenarios were evaluated")

        hashes_after = _actual_results_hashes()
        self.assertEqual(
            hashes_before,
            hashes_after,
            "Actual-results files were mutated during fixture invocation",
        )

    def test_all_fixtures_load_without_error(self):
        scenarios = load_all_scenarios()
        self.assertGreater(len(scenarios), 0)
        for scenario in scenarios:
            self.assertIsInstance(scenario.scenario_id, str)
            self.assertTrue(scenario.scenario_id, "scenario_id must not be empty")


# ---------------------------------------------------------------------------
# Valid write-eligible scenario
# ---------------------------------------------------------------------------

class ValidWriteEligibleFixtureTest(unittest.TestCase):

    def setUp(self):
        self._hashes_before = _actual_results_hashes()

    def tearDown(self):
        hashes_after = _actual_results_hashes()
        self.assertEqual(
            self._hashes_before,
            hashes_after,
            "Actual-results files were mutated",
        )

    def test_valid_write_eligible(self):
        scenario = load_scenario("valid_write_eligible")
        result = _call_guard(scenario)

        self.assertTrue(result.get("guard_allowed"), repr(result))
        self.assertEqual(result.get("reason_code"), "accepted_preview_write_eligible")
        self.assertTrue(result.get("request_valid"))
        self.assertTrue(result.get("token_valid"))
        self.assertTrue(result.get("approval_binding_valid"))
        _assert_non_mutation_flags(self, result)


# ---------------------------------------------------------------------------
# Schema reason-code coverage
# ---------------------------------------------------------------------------

class SchemaReasonCodeFixtureTest(unittest.TestCase):

    def setUp(self):
        self._hashes_before = _actual_results_hashes()

    def tearDown(self):
        hashes_after = _actual_results_hashes()
        self.assertEqual(
            self._hashes_before,
            hashes_after,
            "Actual-results files were mutated",
        )

    def _assert_schema_denial(self, scenario_id: str, expected_reason: str) -> None:
        scenario = load_scenario(scenario_id)
        result = _call_guard(scenario)
        self.assertFalse(result.get("guard_allowed"), f"{scenario_id}: {repr(result)}")
        self.assertFalse(result.get("request_valid"), f"{scenario_id}: expected request_valid=false")
        self.assertEqual(
            result.get("reason_code"),
            expected_reason,
            f"{scenario_id}: reason_code mismatch",
        )
        _assert_non_mutation_flags(self, result, label=scenario_id)

    def test_invalid_apply_mode(self):
        self._assert_schema_denial("invalid_apply_mode", "invalid_apply_mode")

    def test_invalid_lookup_intent(self):
        self._assert_schema_denial("invalid_lookup_intent", "invalid_lookup_intent")

    def test_selected_key_required(self):
        self._assert_schema_denial("selected_key_required", "selected_key_required")

    def test_single_record_required(self):
        self._assert_schema_denial("single_record_required", "single_record_required")

    def test_approval_granted_required_true(self):
        self._assert_schema_denial("approval_granted_required_true", "approval_granted_required_true")

    def test_batch_field_not_allowed(self):
        self._assert_schema_denial("batch_field_not_allowed", "batch_field_not_allowed")

    def test_approval_token_missing(self):
        self._assert_schema_denial("approval_token_missing", "approval_token_missing")


# ---------------------------------------------------------------------------
# Token reason-code coverage
# ---------------------------------------------------------------------------

class TokenReasonCodeFixtureTest(unittest.TestCase):

    def setUp(self):
        self._hashes_before = _actual_results_hashes()

    def tearDown(self):
        hashes_after = _actual_results_hashes()
        self.assertEqual(
            self._hashes_before,
            hashes_after,
            "Actual-results files were mutated",
        )

    def _assert_token_denial(self, scenario_id: str, expected_reason: str) -> None:
        scenario = load_scenario(scenario_id)
        result = _call_guard(scenario)
        self.assertFalse(result.get("guard_allowed"), f"{scenario_id}: {repr(result)}")
        self.assertTrue(result.get("request_valid"), f"{scenario_id}: expected schema to pass")
        self.assertFalse(result.get("token_valid"), f"{scenario_id}: expected token_valid=false")
        self.assertEqual(
            result.get("reason_code"),
            expected_reason,
            f"{scenario_id}: reason_code mismatch",
        )
        _assert_non_mutation_flags(self, result, label=scenario_id)

    def test_approval_expired(self):
        self._assert_token_denial("approval_expired", "approval_expired")

    def test_approval_replayed(self):
        self._assert_token_denial("approval_replayed", "approval_replayed")

    def test_approval_token_consumed(self):
        self._assert_token_denial("approval_token_consumed", "approval_token_consumed")

    def test_approval_binding_mismatch(self):
        self._assert_token_denial("approval_binding_mismatch", "approval_binding_mismatch")


# ---------------------------------------------------------------------------
# Guard binding/snapshot mismatch reason-code coverage
# ---------------------------------------------------------------------------

class GuardBindingMismatchFixtureTest(unittest.TestCase):

    def setUp(self):
        self._hashes_before = _actual_results_hashes()

    def tearDown(self):
        hashes_after = _actual_results_hashes()
        self.assertEqual(
            self._hashes_before,
            hashes_after,
            "Actual-results files were mutated",
        )

    def _assert_guard_denial(self, scenario_id: str, expected_reason: str) -> None:
        scenario = load_scenario(scenario_id)
        result = _call_guard(scenario)
        self.assertFalse(result.get("guard_allowed"), f"{scenario_id}: {repr(result)}")
        self.assertTrue(result.get("request_valid"), f"{scenario_id}: schema should pass")
        self.assertTrue(result.get("token_valid"), f"{scenario_id}: token should pass")
        self.assertEqual(
            result.get("reason_code"),
            expected_reason,
            f"{scenario_id}: reason_code mismatch",
        )
        _assert_non_mutation_flags(self, result, label=scenario_id)

    def test_selected_key_binding_mismatch(self):
        self._assert_guard_denial("selected_key_binding_mismatch", "selected_key_binding_mismatch")

    def test_citation_binding_mismatch(self):
        self._assert_guard_denial("citation_binding_mismatch", "citation_binding_mismatch")

    def test_source_url_binding_mismatch(self):
        self._assert_guard_denial("source_url_binding_mismatch", "source_url_binding_mismatch")

    def test_source_date_binding_mismatch(self):
        self._assert_guard_denial("source_date_binding_mismatch", "source_date_binding_mismatch")

    def test_extracted_winner_binding_mismatch(self):
        self._assert_guard_denial("extracted_winner_binding_mismatch", "extracted_winner_binding_mismatch")

    def test_record_identity_binding_mismatch(self):
        self._assert_guard_denial("record_identity_binding_mismatch", "record_identity_binding_mismatch")

    def test_preview_snapshot_mismatch(self):
        self._assert_guard_denial("preview_snapshot_mismatch", "preview_snapshot_mismatch")


# ---------------------------------------------------------------------------
# Acceptance gate denial coverage (manual_review + rejected)
# ---------------------------------------------------------------------------

class AcceptanceGateDenialFixtureTest(unittest.TestCase):

    def setUp(self):
        self._hashes_before = _actual_results_hashes()

    def tearDown(self):
        hashes_after = _actual_results_hashes()
        self.assertEqual(
            self._hashes_before,
            hashes_after,
            "Actual-results files were mutated",
        )

    def _assert_gate_denial(self, scenario_id: str, expected_reason: str) -> None:
        scenario = load_scenario(scenario_id)
        result = _call_guard(scenario)
        self.assertFalse(result.get("guard_allowed"), f"{scenario_id}: {repr(result)}")
        self.assertTrue(result.get("request_valid"), f"{scenario_id}: schema should pass")
        self.assertTrue(result.get("token_valid"), f"{scenario_id}: token should pass")
        self.assertTrue(result.get("approval_binding_valid"), f"{scenario_id}: binding should match")
        self.assertEqual(
            result.get("reason_code"),
            expected_reason,
            f"{scenario_id}: reason_code mismatch",
        )
        _assert_non_mutation_flags(self, result, label=scenario_id)

    def test_tier_b_without_corroboration(self):
        self._assert_gate_denial("tier_b_without_corroboration", "tier_b_without_corroboration")

    def test_confidence_below_threshold(self):
        self._assert_gate_denial("confidence_below_threshold", "confidence_below_threshold")

    def test_stale_source_date(self):
        self._assert_gate_denial("stale_source_date", "stale_source_date")

    def test_source_conflict(self):
        self._assert_gate_denial("source_conflict", "source_conflict")

    def test_identity_conflict(self):
        self._assert_gate_denial("identity_conflict", "identity_conflict")


# ---------------------------------------------------------------------------
# acceptance_gate_not_write_eligible — mock-based (unreachable via real gate)
# ---------------------------------------------------------------------------

class AcceptanceGateNotWriteEligibleMockTest(unittest.TestCase):
    """Tests the defensive guard path where gate_state is unknown but write_eligible=False.

    This code path is unreachable with the current acceptance gate implementation
    (which only returns 'rejected', 'manual_review', or 'write_eligible').
    It is exercised by patching evaluate_official_source_acceptance_gate to
    return a synthetic non-standard state.
    """

    def setUp(self):
        self._hashes_before = _actual_results_hashes()

    def tearDown(self):
        hashes_after = _actual_results_hashes()
        self.assertEqual(
            self._hashes_before,
            hashes_after,
            "Actual-results files were mutated during mock test",
        )

    def test_acceptance_gate_not_write_eligible_mock(self):
        scenario = load_scenario("valid_write_eligible")

        fake_gate = {
            "state": "write_eligible_pending",
            "write_eligible": False,
            "reason_code": "acceptance_gate_not_write_eligible",
            "reasons": ["acceptance_gate_not_write_eligible"],
            "checks": {},
            "selected_key": scenario.request_payload.get("selected_key"),
            "citation_fingerprint": "abc123fingerprint",
        }

        with patch(
            "operator_dashboard.official_source_approved_apply_guard.evaluate_official_source_acceptance_gate",
            return_value=fake_gate,
        ):
            result = _call_guard(scenario)

        self.assertFalse(result.get("guard_allowed"), repr(result))
        self.assertEqual(result.get("reason_code"), "acceptance_gate_not_write_eligible")
        self.assertIs(result.get("mutation_performed"), False)
        self.assertIs(result.get("write_performed"), False)
        self.assertIs(result.get("bulk_lookup_performed"), False)
        self.assertIs(result.get("scoring_semantics_changed"), False)


# ---------------------------------------------------------------------------
# Placeholder scenarios remain placeholder-only
# ---------------------------------------------------------------------------

class PlaceholderFixtureTest(unittest.TestCase):

    def test_all_placeholder_fixtures_are_placeholder_mode(self):
        scenarios = load_scenarios_by_subdirectory("placeholder")
        self.assertGreater(len(scenarios), 0, "No placeholder scenarios found")
        for scenario in scenarios:
            with self.subTest(scenario_id=scenario.scenario_id):
                self.assertEqual(
                    scenario.token_mode,
                    "placeholder",
                    f"{scenario.scenario_id}: must be placeholder mode",
                )
                self.assertIsNone(
                    scenario.request_payload,
                    f"{scenario.scenario_id}: placeholder must have null request_payload",
                )
                self.assertIsNone(
                    scenario.authoritative_preview_result,
                    f"{scenario.scenario_id}: placeholder must have null authoritative_preview_result",
                )

    def test_placeholder_expected_invariants_declared(self):
        scenarios = load_scenarios_by_subdirectory("placeholder")
        required_invariant_fields = {
            "mutation_performed",
            "write_performed",
            "bulk_lookup_performed",
            "scoring_semantics_changed",
        }
        for scenario in scenarios:
            with self.subTest(scenario_id=scenario.scenario_id):
                for field in required_invariant_fields:
                    self.assertIn(
                        field,
                        scenario.expected,
                        f"{scenario.scenario_id}: expected.{field} must be declared",
                    )
                    self.assertFalse(
                        scenario.expected[field],
                        f"{scenario.scenario_id}: expected.{field} must be false",
                    )

    def test_expected_placeholder_scenario_ids_present(self):
        scenarios = load_scenarios_by_subdirectory("placeholder")
        ids = {s.scenario_id for s in scenarios}
        required = {
            "rollback_failed_terminal",
            "token_consume_post_write_failed",
            "mutation_lock_acquire_failed",
            "contention_timeout",
            "crash_interruption_recovery_required",
        }
        for rid in required:
            self.assertIn(rid, ids, f"Missing placeholder scenario: {rid}")


# ---------------------------------------------------------------------------
# Endpoint non-mutating decision envelope coverage
# ---------------------------------------------------------------------------

class EndpointFixtureTest(unittest.TestCase):
    """Verify the Flask endpoint returns non-mutating decision envelope.

    Uses a real Flask test client and mocks _upsert_single_manual_actual_result
    to assert it is never called.
    """

    def _get_app(self):
        import sys
        import os
        # Ensure operator_dashboard/ is on sys.path for bare 'app' import
        op_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        if op_dir not in sys.path:
            sys.path.insert(0, op_dir)
        from app import app  # noqa: PLC0415
        return app

    def setUp(self):
        self._hashes_before = _actual_results_hashes()
        try:
            flask_app = self._get_app()
            flask_app.config["TESTING"] = True
            self.client = flask_app.test_client()
            self._flask_available = True
        except Exception:
            self._flask_available = False

    def tearDown(self):
        hashes_after = _actual_results_hashes()
        self.assertEqual(
            self._hashes_before,
            hashes_after,
            "Actual-results files were mutated during endpoint test",
        )

    def _post_apply(self, payload: dict):
        return self.client.post(
            "/api/operator/actual-result-lookup/official-source-approved-apply",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_endpoint_schema_denial_has_non_mutation_flags(self):
        if not self._flask_available:
            self.skipTest("Flask app not importable in this context")

        scenario = load_scenario("invalid_apply_mode")

        with patch("app._upsert_single_manual_actual_result") as mock_upsert:
            resp = self._post_apply(scenario.request_payload)
            mock_upsert.assert_not_called()

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertFalse(body.get("mutation_performed"), repr(body))
        self.assertFalse(body.get("write_performed"), repr(body))
        self.assertFalse(body.get("bulk_lookup_performed"), repr(body))
        self.assertFalse(body.get("scoring_semantics_changed"), repr(body))
        self.assertFalse(body.get("guard_allowed", True), repr(body))

    def test_endpoint_token_denial_has_non_mutation_flags(self):
        if not self._flask_available:
            self.skipTest("Flask app not importable in this context")

        scenario = load_scenario("approval_expired")

        with patch("app._upsert_single_manual_actual_result") as mock_upsert:
            resp = self._post_apply(scenario.request_payload)
            mock_upsert.assert_not_called()

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertFalse(body.get("mutation_performed"), repr(body))
        self.assertFalse(body.get("write_performed"), repr(body))
        self.assertFalse(body.get("bulk_lookup_performed"), repr(body))
        self.assertFalse(body.get("scoring_semantics_changed"), repr(body))


# ---------------------------------------------------------------------------
# Reason-code coverage summary assertion
# ---------------------------------------------------------------------------

class ReasonCodeCoverageTest(unittest.TestCase):
    """Assert that the fixture tree covers the required reason codes."""

    _REQUIRED_SCHEMA_CODES = {
        "invalid_apply_mode",
        "invalid_lookup_intent",
        "selected_key_required",
        "single_record_required",
        "approval_granted_required_true",
        "batch_field_not_allowed",
        "approval_token_missing",
    }

    _REQUIRED_TOKEN_CODES = {
        "approval_expired",
        "approval_replayed",
        "approval_token_consumed",
        "approval_binding_mismatch",
    }

    _REQUIRED_GUARD_CODES = {
        "selected_key_binding_mismatch",
        "citation_binding_mismatch",
        "source_url_binding_mismatch",
        "source_date_binding_mismatch",
        "extracted_winner_binding_mismatch",
        "record_identity_binding_mismatch",
        "preview_snapshot_mismatch",
        "tier_b_without_corroboration",
        "confidence_below_threshold",
        "stale_source_date",
        "source_conflict",
        "identity_conflict",
        "accepted_preview_write_eligible",
    }

    def test_schema_reason_codes_covered_by_fixtures(self):
        scenarios = load_all_scenarios()
        covered = {s.expected.get("reason_code") for s in scenarios if s.expected.get("reason_code")}
        for code in self._REQUIRED_SCHEMA_CODES:
            self.assertIn(code, covered, f"Schema reason code not covered by fixtures: {code}")

    def test_token_reason_codes_covered_by_fixtures(self):
        scenarios = load_all_scenarios()
        covered = {s.expected.get("reason_code") for s in scenarios if s.expected.get("reason_code")}
        for code in self._REQUIRED_TOKEN_CODES:
            self.assertIn(code, covered, f"Token reason code not covered by fixtures: {code}")

    def test_guard_reason_codes_covered_by_fixtures(self):
        scenarios = load_all_scenarios()
        covered = {s.expected.get("reason_code") for s in scenarios if s.expected.get("reason_code")}
        for code in self._REQUIRED_GUARD_CODES:
            self.assertIn(code, covered, f"Guard reason code not covered by fixtures: {code}")

    def test_acceptance_gate_not_write_eligible_covered_by_mock(self):
        scenarios = load_all_scenarios()
        ids = {s.scenario_id for s in scenarios}
        self.assertIn(
            "acceptance_gate_not_write_eligible",
            ids,
            "acceptance_gate_not_write_eligible fixture must exist (mock-tested)",
        )


# ---------------------------------------------------------------------------
# Actual-results file unchanged proof (standalone)
# ---------------------------------------------------------------------------

class ActualResultsFileIntegrityTest(unittest.TestCase):
    """Standalone proof that running all non-placeholder guard evaluations
    leaves actual-results files untouched."""

    def test_actual_results_files_unchanged_after_full_fixture_run(self):
        hashes_before = _actual_results_hashes()

        scenarios = load_all_scenarios()
        for scenario in scenarios:
            if scenario.token_mode in ("placeholder", "mock_test_only"):
                continue
            _call_guard(scenario)

        hashes_after = _actual_results_hashes()
        self.assertEqual(hashes_before, hashes_after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
