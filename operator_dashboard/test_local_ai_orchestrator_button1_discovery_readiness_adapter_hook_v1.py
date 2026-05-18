"""Tests for Button 1 discovery/readiness adapter hooks (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_engine_adapter_registry import (
    DEFAULT_ADAPTERS,
    LocalAIOrchestratorEngineAdapterRegistry,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJob, LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_preview_runner import run_preview_job


BUTTON1_JOB_TYPES = [
    "discovery_job",
    "extraction_job",
    "normalization_job",
    "dedupe_job",
    "ranking_job",
    "queue_candidate_job",
]


def _button1_job(job_type: str, payload=None):
    return LocalAIJob(
        job_type=job_type,
        source_button="button1_find_fights",
        input_ref=LocalAIJobInputRef(
            ref_type="manual",
            ref_key="b1_seed",
            snapshot_hash="snap_v1",
            metadata={"payload": payload or {}},
        ),
    )


def _assert_simple_button1_summary(summary):
    expected = {
        "discovered_count",
        "extracted_count",
        "ready_for_report_count",
        "needs_fixture_data_count",
        "draft_only_count",
        "blocked_on_missing_fighter_count",
        "duplicate_or_conflict_count",
        "approval_required",
        "gate_name",
    }
    assert set(summary.keys()) == expected


def test_button1_discovery_job_adapter_is_registered():
    assert "discovery_job" in DEFAULT_ADAPTERS


def test_button1_extraction_job_adapter_is_registered():
    assert "extraction_job" in DEFAULT_ADAPTERS


def test_button1_normalization_job_adapter_is_registered():
    assert "normalization_job" in DEFAULT_ADAPTERS


def test_button1_dedupe_job_adapter_is_registered():
    assert "dedupe_job" in DEFAULT_ADAPTERS


def test_button1_ranking_job_adapter_is_registered():
    assert "ranking_job" in DEFAULT_ADAPTERS


def test_button1_queue_candidate_job_adapter_is_registered():
    assert "queue_candidate_job" in DEFAULT_ADAPTERS


def test_discovery_adapter_returns_safe_preview_summary():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button1_job("discovery_job"))
    _assert_simple_button1_summary(out.summary)
    assert out.summary["approval_required"] is True
    assert out.summary["gate_name"] == "Approve Save Fights"


def test_extraction_adapter_returns_safe_preview_summary():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button1_job("extraction_job"))
    _assert_simple_button1_summary(out.summary)


def test_ranking_adapter_returns_readiness_summary_fields():
    payload = {
        "discovered_count": 10,
        "extracted_count": 9,
        "ready_for_report_count": 5,
        "needs_fixture_data_count": 2,
        "draft_only_count": 1,
        "blocked_on_missing_fighter_count": 1,
        "duplicate_or_conflict_count": 1,
    }
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button1_job("ranking_job", payload=payload))
    _assert_simple_button1_summary(out.summary)
    assert out.summary["ready_for_report_count"] == 5
    assert out.summary["needs_fixture_data_count"] == 2


def test_queue_candidate_adapter_requires_approval():
    out = run_preview_job(_button1_job("queue_candidate_job"))
    assert out.status == "preview_ready"
    assert out.approval_required.required is True
    assert out.output_preview.summary["approval_required"] is True


def test_no_input_path_does_not_create_fake_fights():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button1_job("discovery_job", payload={}))
    assert out.summary["discovered_count"] == 0
    assert out.summary["extracted_count"] == 0
    assert out.summary["ready_for_report_count"] == 0


def test_candidate_rows_drive_discovered_and_extracted_fallback_counts():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    payload = {
        "candidate_rows": [
            {"fight_name": "A vs B"},
            {"fight_name": "C vs D"},
        ]
    }
    out = registry.run_preview(_button1_job("discovery_job", payload=payload))
    assert out.summary["discovered_count"] == 2
    assert out.summary["extracted_count"] == 2


def test_source_backed_candidate_rows_drive_ready_count_fallback():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    payload = {
        "candidate_rows": [
            {"fight_name": "A vs B", "source_url": "https://www.ufc.com/event/ufc-300"},
            {"fight_name": "C vs D"},
        ]
    }
    out = registry.run_preview(_button1_job("discovery_job", payload=payload))
    assert out.summary["discovered_count"] == 2
    assert out.summary["ready_for_report_count"] == 1
    assert out.summary["draft_only_count"] == 1


def test_adapter_output_is_json_serializable():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button1_job("extraction_job"))
    payload = json.dumps({"summary": out.summary, "metrics": out.metrics})
    assert isinstance(payload, str)


def test_adapter_does_not_expose_advanced_diagnostics_by_default():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button1_job("discovery_job"))
    summary = out.summary
    assert "row_details" not in summary
    assert "source_trace" not in summary
    assert "debug" not in summary
    assert "telemetry" not in summary


def test_all_mutation_flags_remain_false():
    out = run_preview_job(_button1_job("ranking_job"))
    t = out.safety_telemetry
    assert t.mutation_performed is False
    assert t.durable_write_performed is False
    assert t.auto_apply_performed is False


def test_queue_database_write_flags_remain_false():
    out = run_preview_job(_button1_job("queue_candidate_job"))
    t = out.safety_telemetry
    assert t.queue_write_performed is False
    assert t.durable_write_performed is False


def test_report_result_learning_calibration_flags_remain_false():
    out = run_preview_job(_button1_job("discovery_job"))
    t = out.safety_telemetry
    assert t.report_export_approved is False
    assert t.learning_apply_performed is False
    assert t.calibration_write_performed is False


def test_adapter_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during Button 1 adapter execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    registry = LocalAIOrchestratorEngineAdapterRegistry()
    _ = registry.run_preview(_button1_job("ranking_job"))
    assert opened_for_write == []
