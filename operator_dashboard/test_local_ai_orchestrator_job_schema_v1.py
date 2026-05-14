"""Tests for local_ai_orchestrator_job_schema.py (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_job_schema import (
    LocalAIJob,
    LocalAIJobBlockingReason,
    LocalAIJobInputRef,
    LocalAIJobOutputPreview,
    LocalAIJobProvenance,
)


def _input_ref(key: str) -> LocalAIJobInputRef:
    return LocalAIJobInputRef(ref_type="entity", ref_key=key, snapshot_hash="snap_v1")


def test_creates_valid_button1_discovery_job():
    job = LocalAIJob(
        job_type="discovery_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("event_window_2026w20"),
    )
    assert job.job_type == "discovery_job"
    assert job.source_button == "button1_find_fights"


def test_creates_valid_button2_report_generation_job():
    job = LocalAIJob(
        job_type="report_generation_job",
        source_button="button2_generate_pdfs",
        input_ref=_input_ref("fight_ufc_001"),
    )
    assert job.job_type == "report_generation_job"
    assert job.source_button == "button2_generate_pdfs"


def test_creates_valid_button3_result_search_job():
    job = LocalAIJob(
        job_type="result_search_job",
        source_button="button3_find_results",
        input_ref=_input_ref("waiting_rows_batch_001"),
    )
    assert job.job_type == "result_search_job"
    assert job.source_button == "button3_find_results"


def test_safety_telemetry_defaults_are_locked():
    job = LocalAIJob(
        job_type="discovery_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("x"),
    )
    t = job.safety_telemetry
    assert t.preview_only is True
    assert t.operator_approval_required is True


def test_mutation_flags_default_false():
    job = LocalAIJob(
        job_type="discovery_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("x"),
    )
    t = job.safety_telemetry
    assert t.mutation_performed is False
    assert t.queue_write_performed is False
    assert t.report_export_approved is False
    assert t.durable_write_performed is False
    assert t.learning_apply_performed is False
    assert t.calibration_write_performed is False
    assert t.auto_apply_performed is False


def test_approval_required_defaults_true():
    job = LocalAIJob(
        job_type="queue_candidate_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("ranked_fights"),
    )
    assert job.approval_required.required is True


def test_invalid_job_type_fails():
    with pytest.raises(ValueError, match="invalid job_type"):
        LocalAIJob(
            job_type="bad_job",
            source_button="button1_find_fights",
            input_ref=_input_ref("x"),
        )


def test_invalid_source_button_fails():
    with pytest.raises(ValueError, match="invalid source_button"):
        LocalAIJob(
            job_type="discovery_job",
            source_button="button4_unknown",
            input_ref=_input_ref("x"),
        )


def test_job_serializes_to_dict():
    job = LocalAIJob(
        job_type="ranking_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("deduped_list"),
    )
    data = job.to_dict()
    assert isinstance(data, dict)
    assert data["job_type"] == "ranking_job"
    assert "safety_telemetry" in data


def test_job_serializes_to_json():
    job = LocalAIJob(
        job_type="result_match_job",
        source_button="button3_find_results",
        input_ref=_input_ref("candidate_rows"),
    )
    payload = job.to_json()
    parsed = json.loads(payload)
    assert parsed["job_type"] == "result_match_job"


def test_blocking_reasons_serialize():
    reason = LocalAIJobBlockingReason(
        code="source_conflict",
        message="Conflicting result sources detected",
        severity="high",
        details={"row_key": "fight_001"},
    )
    job = LocalAIJob(
        job_type="result_match_job",
        source_button="button3_find_results",
        input_ref=_input_ref("candidate_rows"),
        blocking_reasons=[reason],
    )
    data = job.to_dict()
    assert data["blocking_reasons"][0]["code"] == "source_conflict"


def test_provenance_serializes():
    provenance = LocalAIJobProvenance(
        source_urls=["https://www.ufc.com/event/ufc-300"],
        engine_version="local-ai-orchestrator-v1",
        trace={"collector": "trusted_source_fetch"},
    )
    job = LocalAIJob(
        job_type="discovery_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("event_window"),
        provenance=provenance,
    )
    data = job.to_dict()
    assert data["provenance"]["source_urls"][0].startswith("https://")


def test_permanent_action_jobs_require_approval():
    # Requirement is satisfied by schema defaults (approval_required.required=True)
    queue_job = LocalAIJob(
        job_type="queue_candidate_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("ready_to_save"),
    )
    delivery_job = LocalAIJob(
        job_type="delivery_candidate_job",
        source_button="button2_generate_pdfs",
        input_ref=_input_ref("pdf_preview_001"),
    )
    calibration_job = LocalAIJob(
        job_type="calibration_recommendation_job",
        source_button="button3_find_results",
        input_ref=_input_ref("accuracy_batch_001"),
    )
    assert queue_job.approval_required.required is True
    assert delivery_job.approval_required.required is True
    assert calibration_job.approval_required.required is True


def test_schema_creation_performs_no_writes(monkeypatch):
    opened_for_write = []

    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during schema creation")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    job = LocalAIJob(
        job_type="discovery_job",
        source_button="button1_find_fights",
        input_ref=_input_ref("event_window"),
        output_preview=LocalAIJobOutputPreview(summary={"found": 12}),
    )
    _ = job.to_dict()
    _ = job.to_json()

    assert opened_for_write == []
