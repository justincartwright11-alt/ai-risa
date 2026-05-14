"""
test_button3_auto_result_source_yield_live_executor_preview_v1.py

Tests for button3_auto_result_source_yield_live_executor_preview.py
Covers: basic functionality, telemetry flags, state classification,
multi-row sweep, fake result prevention, response builder, unicode handling.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from button3_auto_result_source_yield_live_executor_preview import (
    execute_live_result_discovery_for_all_waiting_rows,
    build_readonly_executor_preview_response,
    execute_source_search_tasks,
    execute_source_search_task_preview,
    EXECUTOR_VERSION,
)
from button3_improved_source_yield_engine import RESULT_SUMMARY_STATES


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_row(fight_name="Jones vs Gane", event_name="UFC 285", selected_key=None):
    return {
        "fight_name": fight_name,
        "event_name": event_name,
        "event_date": "2023-03-04",
        "promotion": "UFC",
        "selected_key": selected_key or fight_name.replace(" ", "_").lower(),
    }


class FakeProvider:
    """A fake search provider that returns predefined candidates."""
    def __init__(self, candidates=None):
        self.candidates = candidates or []

    def search_candidates(self, query, source_patterns):
        return self.candidates


# ── Basic Functionality ───────────────────────────────────────────────────────

class TestExecutorBasicFunctionality:

    def test_returns_expected_top_level_keys(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        for key in ["executor_version", "summary", "row_states", "row_details", "telemetry"]:
            assert key in result, f"Missing key: {key}"

    def test_all_five_states_present_in_summary(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        summary = result["summary"]
        for state in RESULT_SUMMARY_STATES:
            assert state in summary

    def test_all_rows_included_in_row_states(self):
        rows = [make_row(selected_key=f"fight_{i}") for i in range(5)]
        result = execute_live_result_discovery_for_all_waiting_rows(rows)
        for row in rows:
            assert row["selected_key"] in result["row_states"]

    def test_total_rows_matches_input(self):
        rows = [make_row(selected_key=f"fight_{i}") for i in range(7)]
        result = execute_live_result_discovery_for_all_waiting_rows(rows)
        assert result["summary"]["total_rows"] == 7

    def test_empty_input_returns_zeros(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        summary = result["summary"]
        for state in RESULT_SUMMARY_STATES:
            assert summary[state] == 0
        assert summary["total_rows"] == 0

    def test_executor_version_correct(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["executor_version"] == EXECUTOR_VERSION


# ── Telemetry Flags ───────────────────────────────────────────────────────────

class TestTelemetryFlags:

    def test_preview_only_is_true(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["telemetry"]["preview_only"] is True

    def test_mutation_performed_is_false(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["telemetry"]["mutation_performed"] is False

    def test_durable_write_performed_is_false(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["telemetry"]["durable_write_performed"] is False

    def test_learning_apply_performed_is_false(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["telemetry"]["learning_apply_performed"] is False

    def test_calibration_write_performed_is_false(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["telemetry"]["calibration_write_performed"] is False

    def test_queue_write_performed_is_false(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["telemetry"]["queue_write_performed"] is False

    def test_auto_apply_performed_is_false(self):
        result = execute_live_result_discovery_for_all_waiting_rows([])
        assert result["telemetry"]["auto_apply_performed"] is False


# ── State Classification ──────────────────────────────────────────────────────

class TestStateClassification:

    def test_no_candidates_gives_needs_source(self):
        rows = [make_row(selected_key="fight_a")]
        result = execute_live_result_discovery_for_all_waiting_rows(rows, provider=None)
        assert result["row_states"]["fight_a"] == "Needs Source"

    def test_with_provider_no_matches_gives_no_result_yet(self):
        candidate = {
            "fighter_a": "Random Fighter",
            "fighter_b": "Other Guy",
            "event_name": "Completely Different Event",
            "event_date": "2020-01-01",
            "promotion": "OTHER",
            "declared_winner": "",
        }
        provider = FakeProvider([candidate])
        rows = [make_row("Jones vs Gane", selected_key="fight_a")]
        result = execute_live_result_discovery_for_all_waiting_rows(rows, provider=provider)
        # No high-scoring match → "No Result Yet" or "Needs Source"
        assert result["row_states"]["fight_a"] in ["Needs Source", "No Result Yet"]

    def test_all_states_only_five_valid_values(self):
        rows = [make_row(selected_key=f"fight_{i}") for i in range(10)]
        result = execute_live_result_discovery_for_all_waiting_rows(rows, provider=None)
        for state in result["row_states"].values():
            assert state in RESULT_SUMMARY_STATES


# ── Multi-row Sweep ───────────────────────────────────────────────────────────

class TestMultiRowSweep:

    def test_large_batch_all_rows_included(self):
        rows = [make_row(selected_key=f"fight_{i}") for i in range(50)]
        result = execute_live_result_discovery_for_all_waiting_rows(rows)
        assert len(result["row_states"]) == 50

    def test_summary_counts_match_row_states(self):
        rows = [make_row(selected_key=f"fight_{i}") for i in range(20)]
        result = execute_live_result_discovery_for_all_waiting_rows(rows)
        total_from_counts = sum(
            result["summary"][s] for s in RESULT_SUMMARY_STATES
        )
        assert total_from_counts == 20


# ── Fake Result Prevention ────────────────────────────────────────────────────

class TestFakeResultPrevention:

    def test_no_fake_candidates_injected(self):
        rows = [make_row(selected_key="fight_a")]
        result = execute_live_result_discovery_for_all_waiting_rows(rows, provider=None)
        # With no provider, no candidates → Needs Source (not a fabricated result)
        assert result["row_states"]["fight_a"] == "Needs Source"


# ── Response Builder ──────────────────────────────────────────────────────────

class TestResponseBuilder:

    def test_response_builder_returns_ok_true(self):
        resp = build_readonly_executor_preview_response([])
        assert resp["ok"] is True

    def test_response_builder_preview_only_true(self):
        resp = build_readonly_executor_preview_response([])
        assert resp["preview_only"] is True

    def test_response_builder_no_row_details_by_default(self):
        resp = build_readonly_executor_preview_response([make_row()])
        assert "row_details" not in resp

    def test_response_builder_row_details_when_requested(self):
        resp = build_readonly_executor_preview_response(
            [make_row()], include_diagnostics=True
        )
        assert "row_details" in resp

    def test_response_builder_has_summary(self):
        resp = build_readonly_executor_preview_response([])
        assert "summary" in resp
        for state in RESULT_SUMMARY_STATES:
            assert state in resp["summary"]


# ── Unicode Handling ──────────────────────────────────────────────────────────

class TestUnicodeHandling:

    def test_jiri_prochazka_normalizes(self):
        from button3_improved_source_yield_engine import _normalize_token
        assert _normalize_token("Jiří Procházka") == "jiri prochazka"

    def test_jose_aldo_normalizes(self):
        from button3_improved_source_yield_engine import _normalize_token
        assert _normalize_token("José Aldo") == "jose aldo"

    def test_unicode_row_does_not_crash_executor(self):
        row = make_row(fight_name="Jiří Procházka vs Magomed Ankalaev",
                       selected_key="jiri_vs_ankalaev")
        result = execute_live_result_discovery_for_all_waiting_rows([row])
        assert "jiri_vs_ankalaev" in result["row_states"]


# ── Source Search Task Execution ──────────────────────────────────────────────

class TestSourceSearchTaskExecution:

    def test_execute_task_no_provider_returns_empty(self):
        from button3_improved_source_yield_engine import build_source_search_tasks
        row = make_row()
        tasks = build_source_search_tasks(row)
        assert len(tasks) > 0
        candidates = execute_source_search_task_preview(tasks[0], provider=None)
        assert candidates == []

    def test_execute_tasks_returns_list(self):
        row = make_row()
        candidates = execute_source_search_tasks(row, provider=None)
        assert isinstance(candidates, list)
