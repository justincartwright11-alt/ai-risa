"""Tests for Button 2 report-readiness adapter hooks (v1)."""

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


BUTTON2_JOB_TYPES = [
    "report_generation_job",
    "report_quality_job",
    "pdf_preview_job",
    "delivery_candidate_job",
]


def _button2_job(job_type: str, payload=None):
    return LocalAIJob(
        job_type=job_type,
        source_button="button2_generate_pdfs",
        input_ref=LocalAIJobInputRef(
            ref_type="queue",
            ref_key="b2_seed",
            snapshot_hash="snap_v1",
            metadata={"payload": payload or {}},
        ),
    )


def _assert_simple_button2_summary(summary):
    expected = {
        "selected_fight_count",
        "report_ready_count",
        "draft_only_count",
        "missing_analysis_count",
        "qa_pass_count",
        "qa_blocked_count",
        "pdf_preview_available_count",
        "delivery_candidate_count",
        "approval_required",
        "gate_name",
    }
    assert set(summary.keys()) == expected


def test_button2_report_generation_job_adapter_is_registered():
    assert "report_generation_job" in DEFAULT_ADAPTERS


def test_button2_report_quality_job_adapter_is_registered():
    assert "report_quality_job" in DEFAULT_ADAPTERS


def test_button2_pdf_preview_job_adapter_is_registered():
    assert "pdf_preview_job" in DEFAULT_ADAPTERS


def test_button2_delivery_candidate_job_adapter_is_registered():
    assert "delivery_candidate_job" in DEFAULT_ADAPTERS


def test_report_generation_adapter_returns_safe_preview_summary():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button2_job("report_generation_job"))
    _assert_simple_button2_summary(out.summary)
    assert out.summary["approval_required"] is True
    assert out.summary["gate_name"] == "Approve Customer PDF Delivery"


def test_report_quality_adapter_returns_qa_summary_fields():
    payload = {
        "selected_fight_count": 3,
        "report_ready_count": 2,
        "draft_only_count": 1,
        "missing_analysis_count": 1,
        "qa_pass_count": 2,
        "qa_blocked_count": 1,
        "pdf_preview_available_count": 2,
        "delivery_candidate_count": 1,
    }
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button2_job("report_quality_job", payload=payload))
    _assert_simple_button2_summary(out.summary)
    assert out.summary["qa_pass_count"] == 2
    assert out.summary["qa_blocked_count"] == 1


def test_pdf_preview_adapter_does_not_export_files():
    out = run_preview_job(_button2_job("pdf_preview_job"))
    assert out.status == "preview_ready"
    assert out.safety_telemetry.report_export_approved is False
    assert out.safety_telemetry.mutation_performed is False


def test_delivery_candidate_adapter_requires_approval():
    out = run_preview_job(_button2_job("delivery_candidate_job"))
    assert out.status == "preview_ready"
    assert out.approval_required.required is True
    assert out.output_preview.summary["approval_required"] is True


def test_no_input_path_does_not_create_fake_reports():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button2_job("report_generation_job", payload={}))
    assert out.summary["selected_fight_count"] == 0
    assert out.summary["report_ready_count"] == 0
    assert out.summary["pdf_preview_available_count"] == 0


def test_adapter_output_is_json_serializable():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button2_job("report_quality_job"))
    payload = json.dumps({"summary": out.summary, "metrics": out.metrics})
    assert isinstance(payload, str)


def test_adapter_does_not_expose_advanced_diagnostics_by_default():
    registry = LocalAIOrchestratorEngineAdapterRegistry()
    out = registry.run_preview(_button2_job("report_quality_job"))
    summary = out.summary
    assert "report_text" not in summary
    assert "raw_diagnostics" not in summary
    assert "telemetry" not in summary
    assert "debug" not in summary
    assert "qa_trace" not in summary


def test_all_mutation_flags_remain_false():
    out = run_preview_job(_button2_job("report_generation_job"))
    t = out.safety_telemetry
    assert t.mutation_performed is False
    assert t.durable_write_performed is False
    assert t.auto_apply_performed is False


def test_queue_database_write_flags_remain_false():
    out = run_preview_job(_button2_job("delivery_candidate_job"))
    t = out.safety_telemetry
    assert t.queue_write_performed is False
    assert t.durable_write_performed is False


def test_report_export_customer_delivery_flags_remain_false():
    out = run_preview_job(_button2_job("pdf_preview_job"))
    t = out.safety_telemetry
    assert t.report_export_approved is False
    assert t.mutation_performed is False


def test_result_learning_calibration_flags_remain_false():
    out = run_preview_job(_button2_job("report_quality_job"))
    t = out.safety_telemetry
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
            raise AssertionError("Unexpected write during Button 2 adapter execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    registry = LocalAIOrchestratorEngineAdapterRegistry()
    _ = registry.run_preview(_button2_job("report_generation_job"))
    assert opened_for_write == []
