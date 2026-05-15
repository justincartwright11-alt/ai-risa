"""Tests for preview-only local AI orchestrator workflow API route (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app

ROUTE = "/api/local-ai/orchestrator/workflow-preview"


def _payload(source_button: str, execute_preview: bool = False):
    return {
        "source_button": source_button,
        "input_ref": {
            "kind": "manual",
            "ref_id": "seed_001",
            "payload": {"sample": True},
        },
        "execute_preview": execute_preview,
    }


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_route_exists(client):
    resp = client.post(ROUTE, json=_payload("button1_find_fights"))
    assert resp.status_code == 200


def test_button1_workflow_preview_returns_6_jobs(client):
    resp = client.post(ROUTE, json=_payload("button1_find_fights"))
    data = resp.get_json()
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 6


def test_button2_workflow_preview_returns_4_jobs(client):
    resp = client.post(ROUTE, json=_payload("button2_generate_pdfs"))
    data = resp.get_json()
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 4


def test_button3_workflow_preview_returns_4_jobs(client):
    resp = client.post(ROUTE, json=_payload("button3_find_results"))
    data = resp.get_json()
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 4


def test_button1_maps_to_approve_save_fights_gate(client):
    resp = client.post(ROUTE, json=_payload("button1_find_fights"))
    data = resp.get_json()
    assert data["workflow"]["gate_name"] == "Approve Save Fights"


def test_button2_maps_to_approve_customer_pdf_delivery_gate(client):
    resp = client.post(ROUTE, json=_payload("button2_generate_pdfs"))
    data = resp.get_json()
    assert data["workflow"]["gate_name"] == "Approve Customer PDF Delivery"


def test_button3_maps_to_approve_result_apply_learning_review_gate(client):
    resp = client.post(ROUTE, json=_payload("button3_find_results"))
    data = resp.get_json()
    assert data["workflow"]["gate_name"] == "Approve Result Apply / Learning Review"


def test_execute_preview_false_does_not_run_jobs(client, monkeypatch):
    import operator_dashboard.app as app_module

    called = {"value": False}

    def _unexpected_run(plan):
        called["value"] = True
        return plan

    monkeypatch.setattr(app_module, "run_workflow_preview", _unexpected_run)

    resp = client.post(ROUTE, json=_payload("button1_find_fights", execute_preview=False))
    data = resp.get_json()

    assert data["ok"] is True
    assert called["value"] is False
    assert data["workflow"]["status"] == "preview_planned"
    assert all(job["status"] == "pending" for job in data["workflow"]["jobs"])


def test_execute_preview_true_runs_preview_only_jobs(client):
    resp = client.post(ROUTE, json=_payload("button1_find_fights", execute_preview=True))
    data = resp.get_json()

    assert data["ok"] is True
    assert data["workflow"]["status"] == "preview_ready"
    assert all(job["status"] == "preview_ready" for job in data["workflow"]["jobs"])


def test_invalid_source_button_returns_fail_closed(client):
    resp = client.post(ROUTE, json=_payload("button4_invalid", execute_preview=False))
    data = resp.get_json()

    assert resp.status_code == 400
    assert data["ok"] is False


def test_route_response_serializes_to_json(client):
    resp = client.post(ROUTE, json=_payload("button2_generate_pdfs"))
    assert resp.content_type.startswith("application/json")
    payload = resp.get_json()
    _ = json.dumps(payload)


def test_all_workflow_telemetry_flags_are_safe(client):
    resp = client.post(ROUTE, json=_payload("button3_find_results", execute_preview=True))
    data = resp.get_json()

    telemetry = data["telemetry"]
    assert telemetry["preview_only"] is True
    assert telemetry["mutation_performed"] is False
    assert telemetry["queue_write_performed"] is False
    assert telemetry["report_export_approved"] is False
    assert telemetry["durable_write_performed"] is False
    assert telemetry["learning_apply_performed"] is False
    assert telemetry["calibration_write_performed"] is False
    assert telemetry["auto_apply_performed"] is False

    workflow = data["workflow"]
    assert workflow["preview_only"] is True
    assert workflow["mutation_performed"] is False
    assert workflow["queue_write_performed"] is False
    assert workflow["report_export_approved"] is False
    assert workflow["durable_write_performed"] is False
    assert workflow["learning_apply_performed"] is False
    assert workflow["calibration_write_performed"] is False
    assert workflow["auto_apply_performed"] is False


def test_all_job_telemetry_flags_remain_preview_only(client):
    resp = client.post(ROUTE, json=_payload("button3_find_results", execute_preview=True))
    data = resp.get_json()

    for job in data["workflow"]["jobs"]:
        tel = job["safety_telemetry"]
        assert tel["preview_only"] is True
        assert tel["mutation_performed"] is False
        assert tel["queue_write_performed"] is False
        assert tel["report_export_approved"] is False
        assert tel["durable_write_performed"] is False
        assert tel["learning_apply_performed"] is False
        assert tel["calibration_write_performed"] is False
        assert tel["auto_apply_performed"] is False


def test_route_performs_no_filesystem_writes(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during preview route execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    resp = client.post(ROUTE, json=_payload("button1_find_fights", execute_preview=True))
    assert resp.status_code == 200
    assert opened_for_write == []
