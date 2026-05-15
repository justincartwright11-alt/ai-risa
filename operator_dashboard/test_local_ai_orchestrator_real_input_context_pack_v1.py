"""Tests for real input context pack builders (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_input_context_pack import (
    build_button1_find_fights_context,
    build_button2_generate_pdfs_context,
    build_button3_find_results_context,
    build_context_pack,
)
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan


def _assert_flags_false(pack_dict):
    assert pack_dict["preview_only"] is True
    assert pack_dict["mutation_performed"] is False
    assert pack_dict["queue_write_performed"] is False
    assert pack_dict["report_export_approved"] is False
    assert pack_dict["durable_write_performed"] is False
    assert pack_dict["learning_apply_performed"] is False
    assert pack_dict["calibration_write_performed"] is False
    assert pack_dict["auto_apply_performed"] is False


def test_button1_context_pack_builds_valid_discovery_preview_input_ref():
    pack = build_button1_find_fights_context({
        "manual_text": "UFC 300",
        "approved_source_refs": ["ufc.com"],
        "candidate_rows": [{"fight_name": "A vs B"}],
    })
    data = pack.to_dict()
    assert data["source_button"] == "button1_find_fights"
    assert data["input_ref"]["kind"] == "discovery_preview"


def test_button2_context_pack_builds_valid_report_preview_input_ref():
    pack = build_button2_generate_pdfs_context({
        "selected_fights": [{"fight_key": "f1"}],
        "queued_fight_refs": ["f1"],
    })
    data = pack.to_dict()
    assert data["source_button"] == "button2_generate_pdfs"
    assert data["input_ref"]["kind"] == "report_preview"


def test_button3_context_pack_builds_valid_result_review_preview_input_ref():
    pack = build_button3_find_results_context({
        "waiting_rows": [{"selected_key": "r1"}],
        "selected_keys": ["r1"],
    })
    data = pack.to_dict()
    assert data["source_button"] == "button3_find_results"
    assert data["input_ref"]["kind"] == "result_review_preview"


def test_empty_button1_input_does_not_create_fake_fights():
    pack = build_button1_find_fights_context({})
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["candidate_rows"] == []


def test_empty_button2_input_does_not_create_fake_reports():
    pack = build_button2_generate_pdfs_context({})
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["selected_fights"] == []
    assert payload["customer_ready_refs"] == []


def test_empty_button3_input_does_not_create_fake_results():
    pack = build_button3_find_results_context({})
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["waiting_rows"] == []


def test_invalid_source_button_fails_closed():
    with pytest.raises(ValueError, match="invalid source_button"):
        build_context_pack("button4_invalid", {})


def test_context_pack_serializes_to_dict():
    pack = build_button1_find_fights_context({})
    data = pack.to_dict()
    assert isinstance(data, dict)
    assert "input_ref" in data


def test_context_pack_serializes_to_json():
    pack = build_button2_generate_pdfs_context({})
    payload = pack.to_json()
    data = json.loads(payload)
    assert data["source_button"] == "button2_generate_pdfs"


def test_all_safety_flags_remain_false():
    p1 = build_button1_find_fights_context({}).to_dict()
    p2 = build_button2_generate_pdfs_context({}).to_dict()
    p3 = build_button3_find_results_context({}).to_dict()
    _assert_flags_false(p1)
    _assert_flags_false(p2)
    _assert_flags_false(p3)


def test_context_pack_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during context-pack build")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    _ = build_button1_find_fights_context({})
    _ = build_button2_generate_pdfs_context({})
    _ = build_button3_find_results_context({})
    assert opened_for_write == []


def test_context_pack_can_be_passed_into_workflow_preview_planner():
    p1 = build_button1_find_fights_context({"candidate_rows": [{"fight_name": "A vs B"}]})
    p2 = build_button2_generate_pdfs_context({"selected_fights": [{"fight_key": "f1"}]})
    p3 = build_button3_find_results_context({"waiting_rows": [{"selected_key": "r1"}]})

    w1 = build_three_button_workflow_plan("button1_find_fights", p1.to_job_input_ref())
    w2 = build_three_button_workflow_plan("button2_generate_pdfs", p2.to_job_input_ref())
    w3 = build_three_button_workflow_plan("button3_find_results", p3.to_job_input_ref())

    assert len(w1.jobs) == 6
    assert len(w2.jobs) == 4
    assert len(w3.jobs) == 4
