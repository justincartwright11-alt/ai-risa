"""Tests for runtime-context API binding on local AI workflow preview route (v1)."""

import json
import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import operator_dashboard.app as app_module
from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_input_context_pack import build_context_pack
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    build_runtime_context_pack as real_build_runtime_context_pack,
)

ROUTE = "/api/local-ai/orchestrator/workflow-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _payload_with_runtime(source_button: str, execute_preview: bool = False):
    return {
        "source_button": source_button,
        "use_runtime_context": True,
        "execute_preview": execute_preview,
    }


def _payload_with_input_ref(source_button: str, execute_preview: bool = False):
    return {
        "source_button": source_button,
        "input_ref": {
            "kind": "manual",
            "ref_id": "seed_001",
            "payload": {"sample": True},
        },
        "execute_preview": execute_preview,
    }


def test_route_accepts_use_runtime_context_true_for_button1(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(
            source_button,
            runtime_state_override={"discovered_candidate_rows": [{"fight_name": "A vs B"}]},
            workspace_root=str(tmp_path),
        ),
    )

    resp = client.post(ROUTE, json=_payload_with_runtime("button1_find_fights"))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 6


def test_route_accepts_use_runtime_context_true_for_button2(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(
            source_button,
            runtime_state_override={"selected_fights": [{"fight_key": "f1"}]},
            workspace_root=str(tmp_path),
        ),
    )

    resp = client.post(ROUTE, json=_payload_with_runtime("button2_generate_pdfs"))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 4


def test_route_accepts_use_runtime_context_true_for_button3(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(
            source_button,
            runtime_state_override={"waiting_result_rows": [{"selected_key": "r1"}]},
            workspace_root=str(tmp_path),
        ),
    )

    resp = client.post(ROUTE, json=_payload_with_runtime("button3_find_results"))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 4


def test_button1_runtime_route_path_maps_to_discovery_preview(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button1_find_fights"))
    data = resp.get_json()

    assert data["workflow"]["jobs"][0]["input_ref"]["ref_type"] == "discovery_preview"


def test_button2_runtime_route_path_maps_to_report_preview(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button2_generate_pdfs"))
    data = resp.get_json()

    assert data["workflow"]["jobs"][0]["input_ref"]["ref_type"] == "report_preview"


def test_button3_runtime_route_path_maps_to_result_review_preview(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button3_find_results"))
    data = resp.get_json()

    assert data["workflow"]["jobs"][0]["input_ref"]["ref_type"] == "result_review_preview"


def test_explicit_context_pack_takes_precedence_over_runtime_context(client, monkeypatch):
    def _unexpected_runtime_call(_source_button):
        raise AssertionError("Runtime context should not be used when context_pack is explicit")

    monkeypatch.setattr(app_module, "build_runtime_context_pack", _unexpected_runtime_call)

    resp = client.post(
        ROUTE,
        json={
            "source_button": "button1_find_fights",
            "use_runtime_context": True,
            "context_pack": {"manual_text": "explicit", "candidate_rows": []},
            "execute_preview": False,
        },
    )
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    payload = data["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    assert payload["manual_text"] == "explicit"


def test_existing_input_ref_behavior_unchanged_when_runtime_context_absent(client):
    resp = client.post(ROUTE, json=_payload_with_input_ref("button1_find_fights"))
    data = resp.get_json()

    ref = data["workflow"]["jobs"][0]["input_ref"]
    assert ref["ref_type"] == "manual"
    assert ref["ref_key"] == "seed_001"
    assert ref["metadata"]["payload"] == {"sample": True}


def test_empty_runtime_state_does_not_create_fake_fights(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button1_find_fights"))
    data = resp.get_json()

    payload = data["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    assert payload["candidate_rows"] == []


def test_empty_runtime_state_does_not_create_fake_reports(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button2_generate_pdfs"))
    data = resp.get_json()

    payload = data["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    assert payload["selected_fights"] == []


def test_empty_runtime_state_does_not_create_fake_results(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button3_find_results"))
    data = resp.get_json()

    payload = data["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    assert payload["waiting_rows"] == []


def test_invalid_source_button_fails_closed(client):
    resp = client.post(ROUTE, json=_payload_with_runtime("button4_invalid"))
    data = resp.get_json()

    assert resp.status_code == 400
    assert data["ok"] is False


def test_malformed_runtime_context_request_fails_closed(client):
    resp = client.post(
        ROUTE,
        json={
            "source_button": "button1_find_fights",
            "use_runtime_context": "yes",
            "execute_preview": False,
        },
    )
    data = resp.get_json()

    assert resp.status_code == 400
    assert data["ok"] is False


def test_execute_preview_false_remains_plan_only(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button1_find_fights", execute_preview=False))
    data = resp.get_json()

    assert data["ok"] is True
    assert data["workflow"]["status"] == "preview_planned"
    assert all(job["status"] == "pending" for job in data["workflow"]["jobs"])


def test_execute_preview_true_remains_preview_only(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button1_find_fights", execute_preview=True))
    data = resp.get_json()

    assert data["ok"] is True
    assert data["workflow"]["preview_only"] is True
    assert data["workflow"]["mutation_performed"] is False
    assert data["workflow"]["queue_write_performed"] is False
    assert data["workflow"]["report_export_approved"] is False
    assert data["workflow"]["durable_write_performed"] is False
    assert data["workflow"]["learning_apply_performed"] is False
    assert data["workflow"]["calibration_write_performed"] is False
    assert data["workflow"]["auto_apply_performed"] is False


def test_all_route_telemetry_flags_remain_safe(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button3_find_results", execute_preview=True))
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


def test_route_performs_no_filesystem_writes(client, monkeypatch, tmp_path):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during runtime-context route execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )

    resp = client.post(ROUTE, json=_payload_with_runtime("button1_find_fights", execute_preview=True))
    assert resp.status_code == 200
    assert opened_for_write == []


def test_route_performs_no_live_web_calls(client, monkeypatch, tmp_path):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )

    resp = client.post(ROUTE, json=_payload_with_runtime("button2_generate_pdfs", execute_preview=False))
    assert resp.status_code == 200


def test_runtime_context_route_response_serializes_to_json(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )
    resp = client.post(ROUTE, json=_payload_with_runtime("button2_generate_pdfs"))
    assert resp.content_type.startswith("application/json")
    _ = json.dumps(resp.get_json())
