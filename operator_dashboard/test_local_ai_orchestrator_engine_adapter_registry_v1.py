"""Tests for preview-only engine adapter registry (v1)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_engine_adapter_registry import (
    DEFAULT_ADAPTERS,
    LocalAIOrchestratorEngineAdapterRegistry,
)
from operator_dashboard.local_ai_orchestrator_job_schema import (
    LocalAIJob,
    LocalAIJobInputRef,
)
from operator_dashboard.local_ai_orchestrator_preview_runner import run_preview_job


def _job(job_type: str, source_button: str = "button1_find_fights") -> LocalAIJob:
    return LocalAIJob(
        job_type=job_type,
        source_button=source_button,
        input_ref=LocalAIJobInputRef(ref_type="entity", ref_key="seed", snapshot_hash="snap_v1"),
    )


def test_registry_has_all_14_required_adapters():
    expected = {
        "discovery_job",
        "extraction_job",
        "normalization_job",
        "dedupe_job",
        "ranking_job",
        "queue_candidate_job",
        "report_generation_job",
        "report_quality_job",
        "pdf_preview_job",
        "delivery_candidate_job",
        "result_search_job",
        "result_match_job",
        "accuracy_comparison_job",
        "calibration_recommendation_job",
    }
    assert expected.issubset(set(DEFAULT_ADAPTERS.keys()))


def test_invalid_adapter_lookup_fails_closed():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    with pytest.raises(ValueError, match="no preview adapter registered"):
        registry.get_adapter("unknown_job")


def test_registry_run_preview_returns_summary_and_metrics():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    result = registry.run_preview(_job("discovery_job"))
    assert isinstance(result.summary, dict)
    assert isinstance(result.metrics, dict)
    assert result.summary["discovered_count"] == 0
    assert result.summary["gate_name"] == "Approve Save Fights"


def test_discovery_and_result_search_preview_paths_are_safe():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    discovery = registry.run_preview(_job("discovery_job"))
    result_search = registry.run_preview(_job("result_search_job", "button3_find_results"))
    assert discovery.metrics["live_search_executed"] is False
    assert result_search.summary["total_rows"] == 0
    assert "Results Found" in result_search.summary


def test_permanent_action_candidates_keep_approval_required_true_via_runner():
    queue_job = run_preview_job(_job("queue_candidate_job"))
    delivery_job = run_preview_job(_job("delivery_candidate_job", "button2_generate_pdfs"))
    calibration_job = run_preview_job(_job("calibration_recommendation_job", "button3_find_results"))
    assert queue_job.approval_required.required is True
    assert delivery_job.approval_required.required is True
    assert calibration_job.approval_required.required is True


def test_runner_with_registry_keeps_all_mutation_flags_false():
    out = run_preview_job(_job("report_generation_job", "button2_generate_pdfs"))
    t = out.safety_telemetry
    assert t.preview_only is True
    assert t.mutation_performed is False
    assert t.queue_write_performed is False
    assert t.report_export_approved is False
    assert t.durable_write_performed is False
    assert t.learning_apply_performed is False
    assert t.calibration_write_performed is False
    assert t.auto_apply_performed is False


def test_registry_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during adapter registry execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    registry = LocalAIOrchestratorEngineAdapterRegistry()
    _ = registry.run_preview(_job("ranking_job"))
    assert opened_for_write == []
