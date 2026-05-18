"""End-to-end smoke proof for dashboard context_pack preview flow (v1)."""

import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app

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


def _preview(client, source_button: str, context_pack: dict, execute_preview: bool = True):
    resp = client.post(
        ROUTE,
        json={
            "source_button": source_button,
            "context_pack": context_pack,
            "execute_preview": execute_preview,
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    return data


def _assert_safe_flags(telemetry_dict):
    assert telemetry_dict["preview_only"] is True
    assert telemetry_dict["mutation_performed"] is False
    assert telemetry_dict["queue_write_performed"] is False
    assert telemetry_dict["report_export_approved"] is False
    assert telemetry_dict["durable_write_performed"] is False
    assert telemetry_dict["learning_apply_performed"] is False
    assert telemetry_dict["calibration_write_performed"] is False
    assert telemetry_dict["auto_apply_performed"] is False


def test_dashboard_has_three_buttons_three_gates_and_context_pack_wire(client):
    html = _dashboard_html(client)

    assert len(re.findall(r'class="btn-main"', html)) == 3
    assert len(re.findall(r'btn-gate', html)) == 3

    # Dashboard now uses runtime context instead of explicit context_pack builders
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_FIGHTS)" in html
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_GENERATE_PDFS)" in html
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_RESULTS)" in html
    assert "use_runtime_context: true" in html
    assert "execute_preview: true" in html


def test_button1_context_pack_flows_route_planner_runner_adapter_preview_only(client):
    data = _preview(
        client,
        "button1_find_fights",
        {
            "manual_text": "UFC card hint",
            "approved_source_refs": [],
            "event_hint": "",
            "promotion_hint": "",
            "date_window": {},
            "candidate_rows": [{"fight_name": "A vs B"}],
        },
        execute_preview=True,
    )

    workflow = data["workflow"]
    jobs = workflow["jobs"]

    assert len(jobs) == 6
    assert workflow["gate_name"] == "Approve Save Fights"
    assert jobs[0]["input_ref"]["ref_type"] == "discovery_preview"
    assert jobs[0]["input_ref"]["metadata"]["payload"]["manual_text"] == "UFC card hint"
    assert jobs[0]["output_preview"]["summary"]["discovered_count"] == 1

    _assert_safe_flags(data["telemetry"])
    _assert_safe_flags(workflow)
    for job in jobs:
        _assert_safe_flags(job["safety_telemetry"])


def test_button2_context_pack_flows_route_planner_runner_adapter_preview_only(client):
    data = _preview(
        client,
        "button2_generate_pdfs",
        {
            "selected_fights": [{"fight_key": "f1"}, {"fight_key": "f2"}],
            "queued_fight_refs": [],
            "report_status_refs": [],
            "analysis_ready_refs": [],
            "customer_ready_refs": [],
        },
        execute_preview=True,
    )

    workflow = data["workflow"]
    jobs = workflow["jobs"]

    assert len(jobs) == 4
    assert workflow["gate_name"] == "Approve Customer PDF Delivery"
    assert jobs[0]["input_ref"]["ref_type"] == "report_preview"
    assert len(jobs[0]["input_ref"]["metadata"]["payload"]["selected_fights"]) == 2
    assert jobs[0]["output_preview"]["summary"]["selected_fight_count"] == 2

    _assert_safe_flags(data["telemetry"])
    _assert_safe_flags(workflow)
    for job in jobs:
        _assert_safe_flags(job["safety_telemetry"])


def test_button3_context_pack_flows_route_planner_runner_adapter_preview_only(client):
    data = _preview(
        client,
        "button3_find_results",
        {
            "waiting_rows": [
                {"selected_key": "fight_1", "event": "event a"},
                {"selected_key": "fight_2", "event": "event b"},
            ],
            "selected_keys": [],
            "result_source_refs": [],
            "report_refs": [],
            "comparison_refs": [],
        },
        execute_preview=True,
    )

    workflow = data["workflow"]
    jobs = workflow["jobs"]

    assert len(jobs) == 4
    assert workflow["gate_name"] == "Approve Result Apply / Learning Review"
    assert jobs[0]["input_ref"]["ref_type"] == "result_review_preview"
    assert len(jobs[0]["input_ref"]["metadata"]["payload"]["waiting_rows"]) == 2
    assert jobs[0]["output_preview"]["summary"]["total_rows"] == 2

    _assert_safe_flags(data["telemetry"])
    _assert_safe_flags(workflow)
    for job in jobs:
        _assert_safe_flags(job["safety_telemetry"])


def test_plan_only_path_still_works_with_context_pack(client):
    data = _preview(
        client,
        "button1_find_fights",
        {
            "manual_text": "",
            "approved_source_refs": [],
            "event_hint": "",
            "promotion_hint": "",
            "date_window": {},
            "candidate_rows": [],
        },
        execute_preview=False,
    )

    workflow = data["workflow"]
    assert workflow["status"] == "preview_planned"
    assert all(job["status"] == "pending" for job in workflow["jobs"])


def test_no_raw_context_pack_job_or_telemetry_internals_exposed_in_normal_dashboard(client):
    html = _dashboard_html(client)

    # Normal-mode summary text remains concise and does not expose internals.
    assert "Local AI preview ready" in html
    assert "Jobs planned" in html
    assert "Jobs previewed" in html
    assert "Gate required" in html
    assert "Gate name" in html
    assert "Blocked count" in html

    assert "row_details" not in html
    assert "source_trace:" not in html
    assert "debug" not in html
    assert "raw_diagnostics" not in html
    assert '"mutation_performed":' not in html
    assert '"durable_write_performed":' not in html
    assert '"learning_apply_performed":' not in html
    assert '"calibration_write_performed":' not in html
    assert '"auto_apply_performed":' not in html


def test_no_filesystem_writes_in_end_to_end_context_pack_preview(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during context-pack end-to-end smoke")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    _ = _preview(
        client,
        "button1_find_fights",
        {
            "manual_text": "",
            "approved_source_refs": [],
            "event_hint": "",
            "promotion_hint": "",
            "date_window": {},
            "candidate_rows": [],
        },
        execute_preview=True,
    )
    _ = _preview(
        client,
        "button2_generate_pdfs",
        {
            "selected_fights": [],
            "queued_fight_refs": [],
            "report_status_refs": [],
            "analysis_ready_refs": [],
            "customer_ready_refs": [],
        },
        execute_preview=True,
    )
    _ = _preview(
        client,
        "button3_find_results",
        {
            "waiting_rows": [],
            "selected_keys": [],
            "result_source_refs": [],
            "report_refs": [],
            "comparison_refs": [],
        },
        execute_preview=True,
    )

    assert opened_for_write == []


def test_no_fake_rows_created_by_empty_context_pack(client):
    d1 = _preview(
        client,
        "button1_find_fights",
        {
            "manual_text": "",
            "approved_source_refs": [],
            "event_hint": "",
            "promotion_hint": "",
            "date_window": {},
            "candidate_rows": [],
        },
    )
    d2 = _preview(
        client,
        "button2_generate_pdfs",
        {
            "selected_fights": [],
            "queued_fight_refs": [],
            "report_status_refs": [],
            "analysis_ready_refs": [],
            "customer_ready_refs": [],
        },
    )
    d3 = _preview(
        client,
        "button3_find_results",
        {
            "waiting_rows": [],
            "selected_keys": [],
            "result_source_refs": [],
            "report_refs": [],
            "comparison_refs": [],
        },
    )

    s1 = d1["workflow"]["jobs"][0]["output_preview"]["summary"]
    s2 = d2["workflow"]["jobs"][0]["output_preview"]["summary"]
    s3 = d3["workflow"]["jobs"][0]["output_preview"]["summary"]

    assert s1["discovered_count"] == 0
    assert s1["extracted_count"] == 0
    assert s2["selected_fight_count"] == 0
    assert s2["report_ready_count"] == 0
    assert s3["total_rows"] == 0
    assert s3["Results Found"] == 0


def test_end_to_end_response_is_json_serializable(client):
    data = _preview(
        client,
        "button1_find_fights",
        {
            "manual_text": "smoke",
            "approved_source_refs": [],
            "event_hint": "",
            "promotion_hint": "",
            "date_window": {},
            "candidate_rows": [],
        },
    )
    _ = json.dumps(data)
