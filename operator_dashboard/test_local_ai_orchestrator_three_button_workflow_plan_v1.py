"""Tests for preview-only three-button workflow planner (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import (
    build_three_button_workflow_plan,
)


def _input_ref(key: str = "seed_001") -> LocalAIJobInputRef:
    return LocalAIJobInputRef(ref_type="entity", ref_key=key, snapshot_hash="snap_v1")


def _job_types(plan):
    return [job.job_type for job in plan.jobs]


def test_button1_workflow_builds_correct_6_job_chain():
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("b1"))
    assert _job_types(plan) == [
        "discovery_job",
        "extraction_job",
        "normalization_job",
        "dedupe_job",
        "ranking_job",
        "queue_candidate_job",
    ]


def test_button2_workflow_builds_correct_4_job_chain():
    plan = build_three_button_workflow_plan("button2_generate_pdfs", _input_ref("b2"))
    assert _job_types(plan) == [
        "report_generation_job",
        "report_quality_job",
        "pdf_preview_job",
        "delivery_candidate_job",
    ]


def test_button3_workflow_builds_correct_4_job_chain():
    plan = build_three_button_workflow_plan("button3_find_results", _input_ref("b3"))
    assert _job_types(plan) == [
        "result_search_job",
        "result_match_job",
        "accuracy_comparison_job",
        "calibration_recommendation_job",
    ]


def test_button1_maps_to_approve_save_fights_gate():
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("b1"))
    assert plan.gate_name == "Approve Save Fights"


def test_button2_maps_to_approve_customer_pdf_delivery_gate():
    plan = build_three_button_workflow_plan("button2_generate_pdfs", _input_ref("b2"))
    assert plan.gate_name == "Approve Customer PDF Delivery"


def test_button3_maps_to_approve_result_apply_learning_review_gate():
    plan = build_three_button_workflow_plan("button3_find_results", _input_ref("b3"))
    assert plan.gate_name == "Approve Result Apply / Learning Review"


def test_job_order_is_deterministic():
    plan_a = build_three_button_workflow_plan("button1_find_fights", _input_ref("same"))
    plan_b = build_three_button_workflow_plan("button1_find_fights", _input_ref("same"))
    assert _job_types(plan_a) == _job_types(plan_b)


def test_workflow_ids_are_deterministic_or_safely_generated():
    plan_a = build_three_button_workflow_plan("button2_generate_pdfs", _input_ref("stable"))
    plan_b = build_three_button_workflow_plan("button2_generate_pdfs", _input_ref("stable"))
    assert plan_a.workflow_id == plan_b.workflow_id
    assert plan_a.workflow_id.startswith("workflow_")


def test_workflow_serializes_to_dict():
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("dict"))
    payload = plan.to_dict()
    assert isinstance(payload, dict)
    assert payload["source_button"] == "button1_find_fights"
    assert len(payload["jobs"]) == 6


def test_workflow_serializes_to_json():
    plan = build_three_button_workflow_plan("button3_find_results", _input_ref("json"))
    payload = plan.to_json()
    data = json.loads(payload)
    assert data["source_button"] == "button3_find_results"


def test_invalid_source_button_fails_closed():
    with pytest.raises(ValueError, match="invalid source_button"):
        build_three_button_workflow_plan("button4_invalid", _input_ref("x"))


def test_all_workflow_telemetry_flags_are_safe():
    plan = build_three_button_workflow_plan("button3_find_results", _input_ref("safe"))
    assert plan.preview_only is True
    assert plan.mutation_performed is False
    assert plan.queue_write_performed is False
    assert plan.report_export_approved is False
    assert plan.durable_write_performed is False
    assert plan.learning_apply_performed is False
    assert plan.calibration_write_performed is False
    assert plan.auto_apply_performed is False


def test_all_jobs_retain_preview_only_telemetry():
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("preview"))
    assert all(job.safety_telemetry.preview_only is True for job in plan.jobs)


def test_permanent_action_candidate_jobs_require_approval():
    b1 = build_three_button_workflow_plan("button1_find_fights", _input_ref("b1"))
    b2 = build_three_button_workflow_plan("button2_generate_pdfs", _input_ref("b2"))
    b3 = build_three_button_workflow_plan("button3_find_results", _input_ref("b3"))

    queue_job = [j for j in b1.jobs if j.job_type == "queue_candidate_job"][0]
    delivery_job = [j for j in b2.jobs if j.job_type == "delivery_candidate_job"][0]
    calibration_job = [j for j in b3.jobs if j.job_type == "calibration_recommendation_job"][0]

    assert queue_job.approval_required.required is True
    assert delivery_job.approval_required.required is True
    assert calibration_job.approval_required.required is True


def test_planner_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during workflow planning")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("no_write"))
    assert plan.status == "preview_planned"
    assert opened_for_write == []
