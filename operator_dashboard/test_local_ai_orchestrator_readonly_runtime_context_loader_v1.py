"""Tests for read-only runtime context loader (v1)."""

import json
import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    build_button1_runtime_context,
    build_button2_runtime_context,
    build_button3_runtime_context,
    build_runtime_context_pack,
    build_runtime_context_payload,
)

ROUTE = "/api/local-ai/orchestrator/workflow-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _assert_safe_flags(pack_dict):
    assert pack_dict["preview_only"] is True
    assert pack_dict["mutation_performed"] is False
    assert pack_dict["queue_write_performed"] is False
    assert pack_dict["report_export_approved"] is False
    assert pack_dict["durable_write_performed"] is False
    assert pack_dict["learning_apply_performed"] is False
    assert pack_dict["calibration_write_performed"] is False
    assert pack_dict["auto_apply_performed"] is False


def test_button1_loader_returns_discovery_preview_context(tmp_path):
    pack = build_button1_runtime_context(workspace_root=str(tmp_path))
    data = pack.to_dict()
    assert data["source_button"] == "button1_find_fights"
    assert data["input_ref"]["kind"] == "discovery_preview"


def test_button2_loader_returns_report_preview_context(tmp_path):
    pack = build_button2_runtime_context(workspace_root=str(tmp_path))
    data = pack.to_dict()
    assert data["source_button"] == "button2_generate_pdfs"
    assert data["input_ref"]["kind"] == "report_preview"


def test_button3_loader_returns_result_review_preview_context(tmp_path):
    pack = build_button3_runtime_context(workspace_root=str(tmp_path))
    data = pack.to_dict()
    assert data["source_button"] == "button3_find_results"
    assert data["input_ref"]["kind"] == "result_review_preview"


def test_empty_runtime_state_does_not_create_fake_fights(tmp_path):
    pack = build_button1_runtime_context(runtime_state_override={}, workspace_root=str(tmp_path))
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["candidate_rows"] == []


def test_empty_runtime_state_does_not_create_fake_reports(tmp_path):
    pack = build_button2_runtime_context(runtime_state_override={}, workspace_root=str(tmp_path))
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["selected_fights"] == []


def test_empty_runtime_state_does_not_create_fake_results(tmp_path):
    pack = build_button3_runtime_context(runtime_state_override={}, workspace_root=str(tmp_path))
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["waiting_rows"] == []


def test_in_memory_button1_state_maps_into_candidate_rows_safely(tmp_path):
    pack = build_button1_runtime_context(
        runtime_state_override={
            "manual_intake_text": "UFC 300",
            "discovered_candidate_rows": [{"fight_name": "A vs B"}],
            "local_candidate_rows": [{"fight_name": "C vs D"}],
        },
        workspace_root=str(tmp_path),
    )
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["manual_text"] == "UFC 300"
    assert len(payload["candidate_rows"]) == 2


def test_button1_runtime_context_includes_advanced_projection_records(tmp_path):
    pack = build_button1_runtime_context(
        runtime_state_override={
            "approved_historical_records": [{"projection": {"known_record": {"fighter_id": "ah-1"}}}],
            "report_history_records": [{"projection": {"known_record": {"fighter_id": "rh-1"}}}],
            "result_ledger_records": [{"projection": {"known_record": {"fighter_id": "rl-1"}}}],
            "global_read_projection_records": [{"projection": {"known_record": {"fighter_id": "gr-1"}}}],
        },
        workspace_root=str(tmp_path),
    )
    payload = pack.to_dict()["input_ref"]["payload"]
    assert len(payload["approved_historical_records"]) == 1
    assert len(payload["report_history_records"]) == 1
    assert len(payload["result_ledger_records"]) == 1
    assert len(payload["global_read_projection_records"]) == 1


def test_in_memory_button2_state_maps_into_selected_fights_and_report_refs_safely(tmp_path):
    pack = build_button2_runtime_context(
        runtime_state_override={
            "selected_fights": [{"fight_key": "f1"}],
            "report_status_refs": ["r1"],
            "analysis_ready_refs": ["a1"],
            "customer_ready_refs": ["c1"],
        },
        workspace_root=str(tmp_path),
    )
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["selected_fights"] == [{"fight_key": "f1"}]
    assert payload["report_status_refs"] == ["r1"]


def test_in_memory_button3_state_maps_into_waiting_rows_safely(tmp_path):
    pack = build_button3_runtime_context(
        runtime_state_override={
            "waiting_result_rows": [{"selected_key": "k1"}],
            "selected_result_keys": ["k1"],
        },
        workspace_root=str(tmp_path),
    )
    payload = pack.to_dict()["input_ref"]["payload"]
    assert payload["waiting_rows"] == [{"selected_key": "k1"}]
    assert payload["selected_keys"] == ["k1"]


def test_invalid_source_button_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="invalid source_button"):
        build_runtime_context_pack("button4_invalid", workspace_root=str(tmp_path))


def test_loader_output_serializes_to_dict(tmp_path):
    pack = build_runtime_context_pack("button1_find_fights", workspace_root=str(tmp_path))
    data = pack.to_dict()
    assert isinstance(data, dict)


def test_loader_output_serializes_to_json(tmp_path):
    pack = build_runtime_context_pack("button2_generate_pdfs", workspace_root=str(tmp_path))
    payload = pack.to_json()
    data = json.loads(payload)
    assert data["source_button"] == "button2_generate_pdfs"


def test_loader_output_can_be_passed_into_workflow_preview_route_as_context_pack(client, tmp_path):
    context_pack = build_runtime_context_payload(
        "button3_find_results",
        runtime_state_override={"waiting_result_rows": [{"selected_key": "r1"}]},
        workspace_root=str(tmp_path),
    )

    resp = client.post(
        ROUTE,
        json={
            "source_button": "button3_find_results",
            "context_pack": context_pack,
            "execute_preview": True,
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["workflow"]["jobs"][0]["input_ref"]["ref_type"] == "result_review_preview"


def test_button1_runtime_context_projection_records_flow_through_workflow_preview(client, tmp_path):
    context_pack = build_runtime_context_payload(
        "button1_find_fights",
        runtime_state_override={
            "approved_historical_records": [{"projection": {"known_record": {"fighter_id": "ah-1"}}}],
            "report_history_records": [{"projection": {"known_record": {"fighter_id": "rh-1"}}}],
            "result_ledger_records": [{"projection": {"known_record": {"fighter_id": "rl-1"}}}],
            "global_read_projection_records": [{"projection": {"known_record": {"fighter_id": "gr-1"}}}],
        },
        workspace_root=str(tmp_path),
    )

    resp = client.post(
        ROUTE,
        json={
            "source_button": "button1_find_fights",
            "context_pack": context_pack,
            "execute_preview": True,
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True

    payload = data["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    assert len(payload["approved_historical_records"]) == 1
    assert len(payload["report_history_records"]) == 1
    assert len(payload["result_ledger_records"]) == 1
    assert len(payload["global_read_projection_records"]) == 1


def test_loader_performs_no_filesystem_writes(tmp_path, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during runtime context load")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    _ = build_runtime_context_pack("button1_find_fights", workspace_root=str(tmp_path))
    _ = build_runtime_context_pack("button2_generate_pdfs", workspace_root=str(tmp_path))
    _ = build_runtime_context_pack("button3_find_results", workspace_root=str(tmp_path))
    assert opened_for_write == []


def test_loader_does_not_call_live_web(tmp_path, monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    _ = build_runtime_context_pack(
        "button1_find_fights",
        runtime_state_override={"manual_intake_text": "local only"},
        workspace_root=str(tmp_path),
    )


def test_all_safety_flags_remain_false_for_mutations_and_apply_paths(tmp_path):
    p1 = build_runtime_context_pack("button1_find_fights", workspace_root=str(tmp_path)).to_dict()
    p2 = build_runtime_context_pack("button2_generate_pdfs", workspace_root=str(tmp_path)).to_dict()
    p3 = build_runtime_context_pack("button3_find_results", workspace_root=str(tmp_path)).to_dict()

    _assert_safe_flags(p1)
    _assert_safe_flags(p2)
    _assert_safe_flags(p3)
