"""Unified read-only smoke proof across all three normal dashboard buttons (v1)."""

import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app

ROUTE = "/api/local-ai/orchestrator/workflow-preview"


def _payload(source_button: str, execute_preview: bool = True):
    return {
        "source_button": source_button,
        "input_ref": {
            "kind": "empty",
            "ref_id": "smoke",
            "payload": {},
        },
        "execute_preview": execute_preview,
    }


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _dashboard_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


def _preview(client, source_button: str, execute_preview: bool = True):
    resp = client.post(ROUTE, json=_payload(source_button, execute_preview=execute_preview))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    return data


def _assert_mutation_flags_false(telemetry_dict):
    assert telemetry_dict["preview_only"] is True
    assert telemetry_dict["mutation_performed"] is False
    assert telemetry_dict["queue_write_performed"] is False
    assert telemetry_dict["report_export_approved"] is False
    assert telemetry_dict["durable_write_performed"] is False
    assert telemetry_dict["learning_apply_performed"] is False
    assert telemetry_dict["calibration_write_performed"] is False
    assert telemetry_dict["auto_apply_performed"] is False


def test_find_fights_button_maps_to_button1_find_fights(client):
    html = _dashboard_html(client)
    assert "button1_find_fights" in html


def test_generate_pdfs_button_maps_to_button2_generate_pdfs(client):
    html = _dashboard_html(client)
    assert "button2_generate_pdfs" in html


def test_find_results_button_maps_to_button3_find_results(client):
    html = _dashboard_html(client)
    assert "button3_find_results" in html


def test_button1_workflow_returns_six_planned_jobs(client):
    data = _preview(client, "button1_find_fights", execute_preview=False)
    assert len(data["workflow"]["jobs"]) == 6


def test_button2_workflow_returns_four_planned_jobs(client):
    data = _preview(client, "button2_generate_pdfs", execute_preview=False)
    assert len(data["workflow"]["jobs"]) == 4


def test_button3_workflow_returns_four_planned_jobs(client):
    data = _preview(client, "button3_find_results", execute_preview=False)
    assert len(data["workflow"]["jobs"]) == 4


def test_button1_preview_execution_returns_safe_discovery_readiness_summary_fields(client):
    data = _preview(client, "button1_find_fights", execute_preview=True)
    first_summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]

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
    assert set(first_summary.keys()) == expected


def test_button2_preview_execution_returns_safe_report_readiness_summary_fields(client):
    data = _preview(client, "button2_generate_pdfs", execute_preview=True)
    first_summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]

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
    assert set(first_summary.keys()) == expected


def test_button3_preview_execution_returns_safe_result_source_yield_summary_fields(client):
    data = _preview(client, "button3_find_results", execute_preview=True)
    first_summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]

    expected = {
        "Results Found",
        "Needs Source",
        "Conflict",
        "No Result Yet",
        "Ready to Compare",
        "total_rows",
    }
    assert set(first_summary.keys()) == expected


def test_gate1_remains_approve_save_fights(client):
    data = _preview(client, "button1_find_fights")
    assert data["workflow"]["gate_name"] == "Approve Save Fights"


def test_gate2_remains_approve_customer_pdf_delivery(client):
    data = _preview(client, "button2_generate_pdfs")
    assert data["workflow"]["gate_name"] == "Approve Customer PDF Delivery"


def test_gate3_remains_approve_result_apply_learning_review(client):
    data = _preview(client, "button3_find_results")
    assert data["workflow"]["gate_name"] == "Approve Result Apply / Learning Review"


def test_no_raw_advanced_diagnostics_exposed_in_normal_mode_summaries(client):
    d1 = _preview(client, "button1_find_fights")
    d2 = _preview(client, "button2_generate_pdfs")
    d3 = _preview(client, "button3_find_results")

    summaries = [
        d1["workflow"]["jobs"][0]["output_preview"]["summary"],
        d2["workflow"]["jobs"][0]["output_preview"]["summary"],
        d3["workflow"]["jobs"][0]["output_preview"]["summary"],
    ]

    for summary in summaries:
        assert "row_details" not in summary
        assert "source_trace" not in summary
        assert "debug" not in summary
        assert "raw_diagnostics" not in summary
        assert "qa_trace" not in summary


def test_no_telemetry_internals_exposed_in_normal_mode_summaries(client):
    d1 = _preview(client, "button1_find_fights")
    d2 = _preview(client, "button2_generate_pdfs")
    d3 = _preview(client, "button3_find_results")

    for data in [d1, d2, d3]:
        for job in data["workflow"]["jobs"]:
            summary = job["output_preview"]["summary"]
            assert "telemetry" not in summary
            assert "mutation_performed" not in summary
            assert "learning_apply_performed" not in summary


def test_all_preview_responses_are_json_serializable(client):
    d1 = _preview(client, "button1_find_fights")
    d2 = _preview(client, "button2_generate_pdfs")
    d3 = _preview(client, "button3_find_results")

    _ = json.dumps(d1)
    _ = json.dumps(d2)
    _ = json.dumps(d3)


def test_all_mutation_flags_remain_false(client):
    d1 = _preview(client, "button1_find_fights")
    d2 = _preview(client, "button2_generate_pdfs")
    d3 = _preview(client, "button3_find_results")

    for data in [d1, d2, d3]:
        _assert_mutation_flags_false(data["telemetry"])
        _assert_mutation_flags_false(data["workflow"])
        for job in data["workflow"]["jobs"]:
            _assert_mutation_flags_false(job["safety_telemetry"])


def test_no_filesystem_writes_occur(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during unified preview smoke")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    _preview(client, "button1_find_fights")
    _preview(client, "button2_generate_pdfs")
    _preview(client, "button3_find_results")
    assert opened_for_write == []


def test_no_fake_fights_are_created(client):
    data = _preview(client, "button1_find_fights")
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    assert summary["discovered_count"] == 0
    assert summary["extracted_count"] == 0


def test_no_fake_reports_are_created(client):
    data = _preview(client, "button2_generate_pdfs")
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    assert summary["selected_fight_count"] == 0
    assert summary["report_ready_count"] == 0


def test_no_fake_results_are_created(client):
    data = _preview(client, "button3_find_results")
    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    assert summary["total_rows"] == 0
    assert summary["Results Found"] == 0


def test_normal_dashboard_remains_exactly_3_buttons_3_gates(client):
    html = _dashboard_html(client)
    buttons = re.findall(r'class="btn-main"', html)
    gates = re.findall(r'btn-gate', html)
    assert len(buttons) == 3
    assert len(gates) == 3
