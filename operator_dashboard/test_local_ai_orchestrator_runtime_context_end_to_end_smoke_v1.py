"""Runtime-context end-to-end smoke proof across normal three-button dashboard (v1)."""

import json
import os
import re
import socket
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import operator_dashboard.app as app_module
from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    build_runtime_context_pack as real_build_runtime_context_pack,
)

ROUTE = "/api/local-ai/orchestrator/workflow-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _dashboard_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


def _runtime_payload(source_button: str, execute_preview: bool = True):
    return {
        "source_button": source_button,
        "use_runtime_context": True,
        "execute_preview": execute_preview,
    }


def _preview(client, source_button: str, execute_preview: bool = True):
    resp = client.post(ROUTE, json=_runtime_payload(source_button, execute_preview=execute_preview))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    return data


def _assert_mutation_flags_false(flags):
    assert flags["preview_only"] is True
    assert flags["mutation_performed"] is False
    assert flags["queue_write_performed"] is False
    assert flags["report_export_approved"] is False
    assert flags["durable_write_performed"] is False
    assert flags["learning_apply_performed"] is False
    assert flags["calibration_write_performed"] is False
    assert flags["auto_apply_performed"] is False


# 1

def test_find_fights_dashboard_request_sends_use_runtime_context_true(client):
    html = _dashboard_html(client)
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_FIGHTS)" in html
    assert "use_runtime_context: true" in html


# 2

def test_generate_pdfs_dashboard_request_sends_use_runtime_context_true(client):
    html = _dashboard_html(client)
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_GENERATE_PDFS)" in html
    assert "use_runtime_context: true" in html


# 3

def test_find_results_dashboard_request_sends_use_runtime_context_true(client):
    html = _dashboard_html(client)
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_RESULTS)" in html
    assert "use_runtime_context: true" in html


# 4

def test_button1_runtime_context_route_path_maps_to_discovery_preview(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(
            source_button,
            runtime_state_override={},
            workspace_root=str(tmp_path),
        ),
    )

    data = _preview(client, "button1_find_fights", execute_preview=False)
    assert data["workflow"]["jobs"][0]["input_ref"]["ref_type"] == "discovery_preview"


# 5

def test_button2_runtime_context_route_path_maps_to_report_preview(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(
            source_button,
            runtime_state_override={},
            workspace_root=str(tmp_path),
        ),
    )

    data = _preview(client, "button2_generate_pdfs", execute_preview=False)
    assert data["workflow"]["jobs"][0]["input_ref"]["ref_type"] == "report_preview"


# 6

def test_button3_runtime_context_route_path_maps_to_result_review_preview(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(
            source_button,
            runtime_state_override={},
            workspace_root=str(tmp_path),
        ),
    )

    data = _preview(client, "button3_find_results", execute_preview=False)
    assert data["workflow"]["jobs"][0]["input_ref"]["ref_type"] == "result_review_preview"


# 7

def test_button1_runtime_context_can_execute_preview_only_workflow(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    data = _preview(client, "button1_find_fights", execute_preview=True)

    assert data["execute_preview"] is True
    assert data["workflow"]["preview_only"] is True
    assert len(data["workflow"]["jobs"]) == 6


# 8

def test_button2_runtime_context_can_execute_preview_only_workflow(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    data = _preview(client, "button2_generate_pdfs", execute_preview=True)

    assert data["execute_preview"] is True
    assert data["workflow"]["preview_only"] is True
    assert len(data["workflow"]["jobs"]) == 4


# 9

def test_button3_runtime_context_can_execute_preview_only_workflow(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    data = _preview(client, "button3_find_results", execute_preview=True)

    assert data["execute_preview"] is True
    assert data["workflow"]["preview_only"] is True
    assert len(data["workflow"]["jobs"]) == 4


# 10

def test_button1_summary_remains_simple_and_safe(client):
    data = _preview(client, "button1_find_fights", execute_preview=True)
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
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


# 11

def test_button2_summary_remains_simple_and_safe(client):
    data = _preview(client, "button2_generate_pdfs", execute_preview=True)
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
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


# 12

def test_button3_summary_remains_simple_and_safe(client):
    data = _preview(client, "button3_find_results", execute_preview=True)
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    expected = {
        "Results Found",
        "Needs Source",
        "Conflict",
        "No Result Yet",
        "Ready to Compare",
        "total_rows",
    }
    assert set(summary.keys()) == expected


# 13

def test_legacy_input_ref_fallback_remains_present(client):
    html = _dashboard_html(client)
    assert "input_ref" in html
    assert "kind: 'empty'" in html


# 14

def test_no_raw_runtime_context_is_rendered_in_normal_mode(client):
    html = _dashboard_html(client)
    assert "runtime_state_override" not in html
    assert "load_readonly_runtime_state" not in html
    assert "workspace_root" not in html


# 15

def test_no_raw_job_internals_are_rendered_in_normal_mode(client):
    html = _dashboard_html(client)
    assert "safety_telemetry" not in html
    assert "snapshot_hash" not in html
    assert "input_ref.metadata" not in html


# 16

def test_no_telemetry_internals_are_rendered_in_normal_mode(client):
    html = _dashboard_html(client)
    assert "mutation_performed" not in html
    assert "queue_write_performed" not in html
    assert "learning_apply_performed" not in html
    assert "calibration_write_performed" not in html


# 17

def test_no_advanced_diagnostics_are_rendered_in_normal_mode(client):
    html = _dashboard_html(client)
    assert "raw_diagnostics" not in html
    assert "source_trace" not in html
    assert "qa_trace" not in html
    assert "row_details" not in html
    assert "debug" not in html


# 18

def test_all_outputs_are_json_serializable(client):
    d1 = _preview(client, "button1_find_fights")
    d2 = _preview(client, "button2_generate_pdfs")
    d3 = _preview(client, "button3_find_results")

    _ = json.dumps(d1)
    _ = json.dumps(d2)
    _ = json.dumps(d3)


# 19

def test_all_mutation_flags_remain_false(client):
    d1 = _preview(client, "button1_find_fights")
    d2 = _preview(client, "button2_generate_pdfs")
    d3 = _preview(client, "button3_find_results")

    for data in [d1, d2, d3]:
        _assert_mutation_flags_false(data["telemetry"])
        _assert_mutation_flags_false(data["workflow"])
        for job in data["workflow"]["jobs"]:
            _assert_mutation_flags_false(job["safety_telemetry"])


# 20

def test_no_filesystem_writes_occur(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during runtime-context end-to-end smoke")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    _preview(client, "button1_find_fights")
    _preview(client, "button2_generate_pdfs")
    _preview(client, "button3_find_results")
    assert opened_for_write == []


# 21

def test_no_live_network_calls_occur(client, monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    _preview(client, "button1_find_fights")
    _preview(client, "button2_generate_pdfs")
    _preview(client, "button3_find_results")


# 22

def test_no_fake_fights_are_created(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )

    data = _preview(client, "button1_find_fights")
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    assert summary["discovered_count"] == 0
    assert summary["extracted_count"] == 0


# 23

def test_no_fake_reports_are_created(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )

    data = _preview(client, "button2_generate_pdfs")
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    assert summary["selected_fight_count"] == 0
    assert summary["report_ready_count"] == 0


# 24

def test_no_fake_results_are_created(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )

    data = _preview(client, "button3_find_results")
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    assert summary["total_rows"] == 0
    assert summary["Results Found"] == 0


# 25

def test_normal_dashboard_remains_exactly_three_buttons_three_gates(client):
    html = _dashboard_html(client)
    buttons = re.findall(r'class="btn-main"', html)
    gates = re.findall(r'btn-gate', html)
    assert len(buttons) == 3
    assert len(gates) == 3
