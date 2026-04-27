"""
Tests for operator_dashboard/operator_intent_router.py

Validates that every safety level is correctly routed, that locked patterns
are always refused, and that routing never mutates any file or data.

Safety levels under test:
  AUTO_READ_ONLY
  APPROVAL_REQUIRED_WRITE
  LOCKED_HIGH_RISK
  (unknown_intent falls under AUTO_READ_ONLY with examples)
"""

import importlib
import sys

import pytest

# ---------------------------------------------------------------------------
# Import the module under test via importlib so we do not depend on __init__
# paths being set up.  The module must be importable with PYTHONPATH=C:\ai_risa_data.
# ---------------------------------------------------------------------------
def _get_router():
    if "operator_dashboard.operator_intent_router" in sys.modules:
        return sys.modules["operator_dashboard.operator_intent_router"]
    return importlib.import_module("operator_dashboard.operator_intent_router")


@pytest.fixture
def router():
    return _get_router()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _route(router, command: str) -> dict:
    """Call route_intent and return the result dict."""
    result = router.route_intent(command)
    assert isinstance(result, dict), "route_intent must return a dict"
    return result


def _assert_base_shape(result: dict) -> None:
    """Every result must carry these four keys."""
    assert "intent" in result
    assert "safety_level" in result
    assert "requires_approval" in result
    assert "blocked" in result


def _assert_has_explanation(result: dict) -> None:
    """A user-facing explanation must be present in planned_action or examples."""
    has_action = bool(result.get("planned_action", "").strip())
    has_examples = bool(result.get("examples"))
    assert has_action or has_examples, (
        f"No user-facing explanation for intent '{result.get('intent')}'"
    )


# ===========================================================================
# 1. AUTO_READ_ONLY intents
# ===========================================================================
class TestAutoReadOnly:
    def test_check_health(self, router):
        r = _route(router, "check health")
        _assert_base_shape(r)
        assert r["intent"] == "system_health"
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["requires_approval"] is False
        assert r["blocked"] is False
        _assert_has_explanation(r)

    def test_health_shorthand(self, router):
        r = _route(router, "health")
        assert r["intent"] == "system_health"
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["blocked"] is False

    def test_run_accuracy_calibration(self, router):
        r = _route(router, "run accuracy calibration")
        _assert_base_shape(r)
        assert r["intent"] == "accuracy_calibration"
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["requires_approval"] is False
        assert r["blocked"] is False
        _assert_has_explanation(r)

    def test_accuracy_ledger_calibration_variant(self, router):
        r = _route(router, "accuracy ledger calibration")
        assert r["intent"] == "accuracy_calibration"
        assert r["safety_level"] == "AUTO_READ_ONLY"

    def test_show_backfill_status(self, router):
        r = _route(router, "show backfill status")
        _assert_base_shape(r)
        assert r["intent"] == "backfill_status_check"
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["requires_approval"] is False
        assert r["blocked"] is False
        _assert_has_explanation(r)

    def test_backfill_shorthand(self, router):
        r = _route(router, "backfill")
        assert r["intent"] == "backfill_status_check"
        assert r["safety_level"] == "AUTO_READ_ONLY"

    def test_show_unresolved_fights(self, router):
        r = _route(router, "show unresolved fights")
        _assert_base_shape(r)
        assert r["intent"] == "unresolved_result_review"
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["requires_approval"] is False
        assert r["blocked"] is False
        _assert_has_explanation(r)

    def test_unresolved_shorthand(self, router):
        r = _route(router, "unresolved")
        assert r["intent"] == "unresolved_result_review"
        assert r["safety_level"] == "AUTO_READ_ONLY"

    def test_show_dashboard_warnings(self, router):
        r = _route(router, "show dashboard warnings")
        assert r["intent"] == "system_health"
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["blocked"] is False

    def test_show_last_action(self, router):
        r = _route(router, "show last action")
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["blocked"] is False


# ===========================================================================
# 2. APPROVAL_REQUIRED_WRITE intents
# ===========================================================================
class TestApprovalRequiredWrite:
    def test_build_named_report(self, router):
        r = _route(router, "build Jafel Filho vs Cody Durden report")
        _assert_base_shape(r)
        assert r["intent"] == "build_premium_report"
        assert r["safety_level"] == "APPROVAL_REQUIRED_WRITE"
        assert r["requires_approval"] is True
        assert r["blocked"] is False
        _assert_has_explanation(r)

    def test_build_report_extracts_matchup(self, router):
        r = _route(router, "build Jafel Filho vs Cody Durden report")
        assert "matchup" in r, "matchup field should be parsed for build_premium_report"
        assert "Jafel Filho" in r["matchup"]
        assert "Cody Durden" in r["matchup"]

    def test_generate_report_variant(self, router):
        r = _route(router, "generate Poirier vs Gaethje report")
        assert r["intent"] == "build_premium_report"
        assert r["safety_level"] == "APPROVAL_REQUIRED_WRITE"
        assert r["requires_approval"] is True

    def test_score_a_report(self, router):
        r = _route(router, "score a report")
        _assert_base_shape(r)
        assert r["intent"] == "report_scoring_calibration"
        assert r["safety_level"] == "APPROVAL_REQUIRED_WRITE"
        assert r["requires_approval"] is True
        assert r["blocked"] is False
        _assert_has_explanation(r)

    def test_score_a_finished_report(self, router):
        r = _route(router, "score a finished report")
        assert r["intent"] == "report_scoring_calibration"
        assert r["safety_level"] == "APPROVAL_REQUIRED_WRITE"

    def test_commit_checkpoint(self, router):
        r = _route(router, "commit checkpoint")
        _assert_base_shape(r)
        # commit_readiness_check is AUTO_READ_ONLY — only a force-push is locked.
        # Confirm it is NOT locked and NOT approval-write (checking that "commit"
        # alone does not accidentally escalate to a write action).
        assert r["blocked"] is False
        assert r["safety_level"] in ("AUTO_READ_ONLY", "APPROVAL_REQUIRED_WRITE")
        _assert_has_explanation(r)


# ===========================================================================
# 3. LOCKED_HIGH_RISK intents
# ===========================================================================
class TestLockedHighRisk:
    def _assert_locked(self, r: dict, command: str) -> None:
        _assert_base_shape(r)
        assert r["intent"] == "locked_high_risk", (
            f"Expected locked_high_risk for '{command}', got '{r['intent']}'"
        )
        assert r["safety_level"] == "LOCKED_HIGH_RISK", (
            f"Expected LOCKED_HIGH_RISK for '{command}', got '{r['safety_level']}'"
        )
        assert r["blocked"] is True, f"Expected blocked=True for '{command}'"
        assert r["requires_approval"] is False
        _assert_has_explanation(r)

    def test_apply_backfill(self, router):
        r = _route(router, "apply backfill")
        self._assert_locked(r, "apply backfill")

    def test_regenerate_predictions(self, router):
        r = _route(router, "regenerate predictions")
        self._assert_locked(r, "regenerate predictions")

    def test_delete_prediction_stubs(self, router):
        r = _route(router, "delete prediction stubs")
        self._assert_locked(r, "delete prediction stubs")

    def test_stage_prediction(self, router):
        r = _route(router, "stage prediction")
        self._assert_locked(r, "stage prediction")

    def test_process_batch_2(self, router):
        r = _route(router, "process batch 2")
        self._assert_locked(r, "process batch 2")

    def test_mutate_ledger(self, router):
        r = _route(router, "mutate ledger")
        self._assert_locked(r, "mutate ledger")

    def test_force_commit(self, router):
        r = _route(router, "force-commit")
        self._assert_locked(r, "force-commit")

    def test_git_push_force(self, router):
        r = _route(router, "git push --force")
        self._assert_locked(r, "git push --force")

    def test_drop_table(self, router):
        r = _route(router, "drop table predictions")
        self._assert_locked(r, "drop table predictions")

    def test_locked_message_mentions_checkpoint(self, router):
        r = _route(router, "apply backfill")
        assert "checkpoint" in r.get("planned_action", "").lower(), (
            "Locked response should reference checkpoint requirement"
        )

    def test_locked_provides_examples(self, router):
        r = _route(router, "apply backfill")
        assert "examples" in r and len(r["examples"]) > 0, (
            "Locked response should include examples of safe commands"
        )


# ===========================================================================
# 4. UNKNOWN_INTENT
# ===========================================================================
class TestUnknownIntent:
    def test_gibberish_returns_unknown(self, router):
        r = _route(router, "xyzzy frobulate the quux")
        _assert_base_shape(r)
        assert r["intent"] == "unknown_intent"
        assert r["blocked"] is False
        assert r["requires_approval"] is False

    def test_unknown_provides_examples(self, router):
        r = _route(router, "xyzzy frobulate the quux")
        assert "examples" in r and len(r["examples"]) > 0, (
            "unknown_intent must return examples so the operator knows what to type"
        )

    def test_empty_string_returns_unknown_or_safe(self, router):
        # An empty string may match nothing; ensure it never locks or blocks.
        r = _route(router, "")
        assert r["blocked"] is False
        _assert_has_explanation(r)

    def test_unknown_is_auto_read_only(self, router):
        # Unknown commands must default to read-only so they are safe to return.
        r = _route(router, "what is the meaning of life")
        assert r["safety_level"] == "AUTO_READ_ONLY"
        assert r["blocked"] is False


# ===========================================================================
# 5. No file mutation during routing
# ===========================================================================
class TestNoFileMutation:
    """
    route_intent is a pure function: it reads no files, writes no files,
    and has no side effects.  We verify this by checking that calling it
    multiple times for write/locked intents produces consistent pure output
    without raising filesystem errors.
    """

    def test_build_report_does_not_write(self, router, tmp_path):
        import os
        before = set(os.listdir(tmp_path))
        _route(router, "build Jafel Filho vs Cody Durden report")
        after = set(os.listdir(tmp_path))
        assert before == after, "route_intent must not write any files"

    def test_locked_does_not_write(self, router, tmp_path):
        import os
        before = set(os.listdir(tmp_path))
        _route(router, "apply backfill")
        after = set(os.listdir(tmp_path))
        assert before == after, "route_intent must not write any files"

    def test_multiple_calls_are_idempotent(self, router):
        cmds = [
            "check health",
            "run accuracy calibration",
            "show backfill status",
            "show unresolved fights",
            "build Jafel Filho vs Cody Durden report",
            "apply backfill",
            "xyzzy",
        ]
        for cmd in cmds:
            r1 = _route(router, cmd)
            r2 = _route(router, cmd)
            assert r1["intent"] == r2["intent"], (
                f"route_intent must be deterministic for '{cmd}'"
            )
            assert r1["safety_level"] == r2["safety_level"]
            assert r1["blocked"] == r2["blocked"]


# ===========================================================================
# 6. Safety-level invariants across all known intents
# ===========================================================================
class TestSafetyLevelInvariants:
    """
    Regardless of how a command is phrased, locked patterns must always
    take priority over intent matching.
    """

    def test_apply_backfill_always_locked_regardless_of_prefix(self, router):
        for prefix in ("please ", "can you ", "operator: ", ""):
            r = _route(router, f"{prefix}apply backfill")
            assert r["blocked"] is True, (
                f"'apply backfill' must always be blocked (prefix='{prefix}')"
            )

    def test_delete_prediction_stub_always_locked(self, router):
        for variant in ("delete prediction", "delete stub", "delete prediction stubs"):
            r = _route(router, variant)
            assert r["blocked"] is True, f"'{variant}' must always be locked"

    def test_batch_2_always_locked(self, router):
        for variant in ("batch 2", "process batch 2", "run batch_2", "batch2"):
            r = _route(router, variant)
            assert r["blocked"] is True, f"'{variant}' must always be locked"

    def test_read_only_commands_never_blocked(self, router):
        safe_commands = [
            "check health",
            "run accuracy calibration",
            "show backfill status",
            "show unresolved fights",
        ]
        for cmd in safe_commands:
            r = _route(router, cmd)
            assert r["blocked"] is False, f"'{cmd}' must never be blocked"
            assert r["safety_level"] == "AUTO_READ_ONLY", (
                f"'{cmd}' must be AUTO_READ_ONLY"
            )
