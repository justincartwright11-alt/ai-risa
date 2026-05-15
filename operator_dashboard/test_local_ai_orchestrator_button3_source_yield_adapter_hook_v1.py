"""Tests for Button 3 result_search adapter source-yield preview hook (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import operator_dashboard.local_ai_orchestrator_engine_adapter_registry as registry_module
from operator_dashboard.local_ai_orchestrator_engine_adapter_registry import (
    DEFAULT_ADAPTERS,
    LocalAIOrchestratorEngineAdapterRegistry,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJob, LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_preview_runner import run_preview_job


def _job_with_waiting_rows(waiting_rows):
    return LocalAIJob(
        job_type="result_search_job",
        source_button="button3_find_results",
        input_ref=LocalAIJobInputRef(
            ref_type="result_review",
            ref_key="b3_rows",
            snapshot_hash="snap_v1",
            metadata={"payload": {"waiting_rows": waiting_rows}},
        ),
    )


def test_result_search_job_adapter_is_registered():
    assert "result_search_job" in DEFAULT_ADAPTERS
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    assert registry.has_adapter("result_search_job")


def test_result_search_adapter_uses_executor_preview_when_waiting_rows_supplied(monkeypatch):
    calls = {"count": 0, "include_diagnostics": None}

    def fake_preview_builder(waiting_rows, provider=None, include_diagnostics=False):
        calls["count"] += 1
        calls["include_diagnostics"] = include_diagnostics
        return {
            "ok": True,
            "summary": {
                "Results Found": 1,
                "Needs Source": 0,
                "Conflict": 0,
                "No Result Yet": 0,
                "Ready to Compare": 1,
                "total_rows": 2,
            },
            "row_states": {"r1": "Results Found", "r2": "Ready to Compare"},
            "telemetry": {"preview_only": True},
        }

    monkeypatch.setattr(
        registry_module,
        "_button3_build_readonly_executor_preview_response",
        fake_preview_builder,
    )

    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_job_with_waiting_rows([{"selected_key": "r1"}, {"selected_key": "r2"}]))

    assert calls["count"] == 1
    assert calls["include_diagnostics"] is False
    assert out.metrics["used_executor_preview"] is True


def test_adapter_returns_only_simple_five_state_summary_counts():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_job_with_waiting_rows([]))

    expected_keys = {
        "Results Found",
        "Needs Source",
        "Conflict",
        "No Result Yet",
        "Ready to Compare",
        "total_rows",
    }
    assert set(out.summary.keys()) == expected_keys


def test_adapter_returns_safe_no_input_preview_when_no_waiting_rows_supplied():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_job_with_waiting_rows([]))

    assert out.summary["total_rows"] == 0
    assert out.summary["Results Found"] == 0
    assert out.metrics["used_executor_preview"] is False


def test_adapter_does_not_create_fake_results_when_no_input():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_job_with_waiting_rows([]))

    assert out.summary["Results Found"] == 0
    assert out.summary["Ready to Compare"] == 0


def test_adapter_does_not_expose_row_details_by_default(monkeypatch):
    def fake_preview_builder(waiting_rows, provider=None, include_diagnostics=False):
        return {
            "ok": True,
            "summary": {
                "Results Found": 0,
                "Needs Source": 1,
                "Conflict": 0,
                "No Result Yet": 0,
                "Ready to Compare": 0,
                "total_rows": 1,
            },
            "row_details": {"r1": {"debug": "x"}},
            "row_states": {"r1": "Needs Source"},
        }

    monkeypatch.setattr(
        registry_module,
        "_button3_build_readonly_executor_preview_response",
        fake_preview_builder,
    )

    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_job_with_waiting_rows([{"selected_key": "r1"}]))
    assert "row_details" not in out.summary


def test_adapter_does_not_expose_raw_diagnostics_by_default(monkeypatch):
    def fake_preview_builder(waiting_rows, provider=None, include_diagnostics=False):
        return {
            "ok": True,
            "summary": {
                "Results Found": 0,
                "Needs Source": 1,
                "Conflict": 0,
                "No Result Yet": 0,
                "Ready to Compare": 0,
                "total_rows": 1,
            },
            "telemetry": {"raw_debug": True},
            "executor_version": "x",
        }

    monkeypatch.setattr(
        registry_module,
        "_button3_build_readonly_executor_preview_response",
        fake_preview_builder,
    )

    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_job_with_waiting_rows([{"selected_key": "r1"}]))
    assert "telemetry" not in out.summary
    assert "executor_version" not in out.summary


def test_adapter_output_is_json_serializable():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_job_with_waiting_rows([]))
    payload = json.dumps({"summary": out.summary, "metrics": out.metrics})
    assert isinstance(payload, str)


def test_all_mutation_flags_remain_false():
    out = run_preview_job(_job_with_waiting_rows([]))
    t = out.safety_telemetry
    assert t.mutation_performed is False
    assert t.queue_write_performed is False
    assert t.report_export_approved is False
    assert t.durable_write_performed is False


def test_learning_calibration_flags_remain_false():
    out = run_preview_job(_job_with_waiting_rows([]))
    t = out.safety_telemetry
    assert t.learning_apply_performed is False
    assert t.calibration_write_performed is False


def test_queue_report_result_mutation_flags_remain_false():
    out = run_preview_job(_job_with_waiting_rows([]))
    t = out.safety_telemetry
    assert t.queue_write_performed is False
    assert t.report_export_approved is False
    assert t.mutation_performed is False


def test_adapter_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during result_search adapter execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    registry = LocalAIOrchestratorEngineAdapterRegistry()
    _ = registry.run_preview(_job_with_waiting_rows([]))
    assert opened_for_write == []
