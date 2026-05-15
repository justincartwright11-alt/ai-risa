"""Tests for preview-only local AI orchestrator runner (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import operator_dashboard.local_ai_orchestrator_job_schema as schema
from operator_dashboard.local_ai_orchestrator_job_schema import (
    LocalAIJob,
    LocalAIJobInputRef,
)
from operator_dashboard.local_ai_orchestrator_preview_runner import run_preview_job


def _job(job_type: str, source_button: str, ref_key: str = "ref_001") -> LocalAIJob:
    return LocalAIJob(
        job_type=job_type,
        source_button=source_button,
        input_ref=LocalAIJobInputRef(ref_type="entity", ref_key=ref_key, snapshot_hash="snap_v1"),
    )


def _assert_flags_locked(job: LocalAIJob) -> None:
    t = job.safety_telemetry
    assert t.preview_only is True
    assert t.mutation_performed is False
    assert t.queue_write_performed is False
    assert t.report_export_approved is False
    assert t.durable_write_performed is False
    assert t.learning_apply_performed is False
    assert t.calibration_write_performed is False
    assert t.auto_apply_performed is False


def test_runner_accepts_valid_local_ai_job():
    out = run_preview_job(_job("discovery_job", "button1_find_fights"))
    assert isinstance(out, LocalAIJob)


def test_discovery_job_returns_preview_ready():
    out = run_preview_job(_job("discovery_job", "button1_find_fights"))
    assert out.status == "preview_ready"


def test_extraction_job_returns_preview_ready():
    out = run_preview_job(_job("extraction_job", "button1_find_fights"))
    assert out.status == "preview_ready"


def test_ranking_job_returns_preview_ready():
    out = run_preview_job(_job("ranking_job", "button1_find_fights"))
    assert out.status == "preview_ready"


def test_queue_candidate_job_requires_approval():
    out = run_preview_job(_job("queue_candidate_job", "button1_find_fights"))
    assert out.status == "preview_ready"
    assert out.approval_required.required is True


def test_report_generation_job_returns_preview_ready():
    out = run_preview_job(_job("report_generation_job", "button2_generate_pdfs"))
    assert out.status == "preview_ready"


def test_report_quality_job_returns_preview_ready():
    out = run_preview_job(_job("report_quality_job", "button2_generate_pdfs"))
    assert out.status == "preview_ready"


def test_pdf_preview_job_requires_approval_before_export():
    out = run_preview_job(_job("pdf_preview_job", "button2_generate_pdfs"))
    assert out.status == "preview_ready"
    assert out.approval_required.required is True
    assert out.safety_telemetry.report_export_approved is False


def test_delivery_candidate_job_requires_approval():
    out = run_preview_job(_job("delivery_candidate_job", "button2_generate_pdfs"))
    assert out.status == "preview_ready"
    assert out.approval_required.required is True


def test_result_search_job_returns_preview_ready():
    out = run_preview_job(_job("result_search_job", "button3_find_results"))
    assert out.status == "preview_ready"


def test_result_match_job_returns_preview_ready():
    out = run_preview_job(_job("result_match_job", "button3_find_results"))
    assert out.status == "preview_ready"


def test_accuracy_comparison_job_returns_preview_ready():
    out = run_preview_job(_job("accuracy_comparison_job", "button3_find_results"))
    assert out.status == "preview_ready"


def test_calibration_recommendation_job_requires_approval():
    out = run_preview_job(_job("calibration_recommendation_job", "button3_find_results"))
    assert out.status == "preview_ready"
    assert out.approval_required.required is True


def test_missing_required_input_creates_blocked_status():
    job = _job("discovery_job", "button1_find_fights", ref_key="")
    out = run_preview_job(job)
    assert out.status == "blocked"
    assert len(out.blocking_reasons) >= 1
    assert out.blocking_reasons[0].code == "missing_required_input"


def test_invalid_job_type_fails_closed(monkeypatch):
    job = _job("discovery_job", "button1_find_fights")
    # Mutate allowed job types set to force fail-closed validate path.
    monkeypatch.setattr(schema, "ALLOWED_JOB_TYPES", set())
    with pytest.raises(ValueError, match="invalid job_type"):
        run_preview_job(job)


def test_safety_telemetry_remains_preview_only_true():
    out = run_preview_job(_job("result_search_job", "button3_find_results"))
    assert out.safety_telemetry.preview_only is True


def test_all_mutation_flags_remain_false():
    out = run_preview_job(_job("report_generation_job", "button2_generate_pdfs"))
    _assert_flags_locked(out)


def test_runner_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during runner execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    out = run_preview_job(_job("ranking_job", "button1_find_fights"))
    assert out.status == "preview_ready"
    assert opened_for_write == []


def test_runner_output_preview_serializes_json():
    out = run_preview_job(_job("discovery_job", "button1_find_fights"))
    payload = json.dumps(out.to_dict())
    assert isinstance(payload, str)
