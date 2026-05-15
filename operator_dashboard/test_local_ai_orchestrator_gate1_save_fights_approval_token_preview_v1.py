"""Gate 1 save-fights approval-token preview contract smoke (v1)."""

import json
import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import operator_dashboard.app as app_module
from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan

ROUTE = "/api/local-ai/orchestrator/workflow-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _runtime_payload(source_button: str, execute_preview: bool = False):
    return {
        "source_button": source_button,
        "use_runtime_context": True,
        "execute_preview": execute_preview,
    }


def _input_ref(key: str = "seed_001") -> LocalAIJobInputRef:
    return LocalAIJobInputRef(ref_type="entity", ref_key=key, snapshot_hash="snap_v1")


def _token_fields(token_preview):
    return {
        "contract_name",
        "token",
        "source_button",
        "gate_name",
        "candidate_action",
        "approval_required",
        "preview_only",
        "write_authorized",
        "queue_write_performed",
        "database_write_performed",
    }


def test_button1_plan_contains_gate1_save_fights_approval_token_preview_contract():
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("b1"))
    token_preview = plan.gate_approval_token_preview

    assert isinstance(token_preview, dict)
    assert _token_fields(token_preview).issubset(set(token_preview.keys()))
    assert token_preview["contract_name"] == "gate1_save_fights_approval_token_preview_v1"
    assert token_preview["source_button"] == "button1_find_fights"
    assert token_preview["gate_name"] == "Approve Save Fights"
    assert token_preview["candidate_action"] == "save_fights"


def test_button1_gate1_token_preview_is_preview_only_and_write_blocked():
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("b1"))
    token_preview = plan.gate_approval_token_preview

    assert token_preview["approval_required"] is True
    assert token_preview["preview_only"] is True
    assert token_preview["write_authorized"] is False
    assert token_preview["queue_write_performed"] is False
    assert token_preview["database_write_performed"] is False


def test_button1_gate1_token_preview_is_deterministic_for_same_input():
    plan_a = build_three_button_workflow_plan("button1_find_fights", _input_ref("same"))
    plan_b = build_three_button_workflow_plan("button1_find_fights", _input_ref("same"))

    assert plan_a.gate_approval_token_preview["token"] == plan_b.gate_approval_token_preview["token"]


def test_button1_gate1_token_preview_changes_when_input_changes():
    plan_a = build_three_button_workflow_plan("button1_find_fights", _input_ref("a"))
    plan_b = build_three_button_workflow_plan("button1_find_fights", _input_ref("b"))

    assert plan_a.gate_approval_token_preview["token"] != plan_b.gate_approval_token_preview["token"]


def test_button2_plan_does_not_expose_gate1_token_preview():
    plan = build_three_button_workflow_plan("button2_generate_pdfs", _input_ref("b2"))
    assert plan.gate_approval_token_preview == {}


def test_button3_plan_does_not_expose_gate1_token_preview():
    plan = build_three_button_workflow_plan("button3_find_results", _input_ref("b3"))
    assert plan.gate_approval_token_preview == {}


def test_route_button1_runtime_context_includes_gate1_token_preview(client):
    resp = client.post(ROUTE, json=_runtime_payload("button1_find_fights", execute_preview=False))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    token_preview = data["workflow"]["gate_approval_token_preview"]
    assert _token_fields(token_preview).issubset(set(token_preview.keys()))
    assert token_preview["preview_only"] is True
    assert token_preview["write_authorized"] is False


def test_route_button1_runtime_context_keeps_gate1_token_preview_on_execute_preview_true(client):
    resp = client.post(ROUTE, json=_runtime_payload("button1_find_fights", execute_preview=True))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    token_preview = data["workflow"]["gate_approval_token_preview"]
    assert token_preview["contract_name"] == "gate1_save_fights_approval_token_preview_v1"
    assert token_preview["write_authorized"] is False


def test_route_button2_runtime_context_has_empty_gate1_token_preview(client):
    resp = client.post(ROUTE, json=_runtime_payload("button2_generate_pdfs", execute_preview=True))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["workflow"]["gate_approval_token_preview"] == {}


def test_route_button3_runtime_context_has_empty_gate1_token_preview(client):
    resp = client.post(ROUTE, json=_runtime_payload("button3_find_results", execute_preview=True))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["workflow"]["gate_approval_token_preview"] == {}


def test_gate1_token_preview_contract_is_json_serializable(client):
    resp = client.post(ROUTE, json=_runtime_payload("button1_find_fights", execute_preview=True))
    data = resp.get_json()

    _ = json.dumps(data["workflow"]["gate_approval_token_preview"])


def test_gate1_token_preview_no_filesystem_writes(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during gate1 token preview execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    resp = client.post(ROUTE, json=_runtime_payload("button1_find_fights", execute_preview=True))
    assert resp.status_code == 200
    assert opened_for_write == []


def test_gate1_token_preview_no_live_network_calls(client, monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    resp = client.post(ROUTE, json=_runtime_payload("button1_find_fights", execute_preview=False))
    assert resp.status_code == 200


def test_gate1_token_preview_does_not_create_fake_fights(client, monkeypatch, tmp_path):
    from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
        build_runtime_context_pack as real_build_runtime_context_pack,
    )

    monkeypatch.setattr(
        app_module,
        "build_runtime_context_pack",
        lambda source_button: real_build_runtime_context_pack(source_button, runtime_state_override={}, workspace_root=str(tmp_path)),
    )

    resp = client.post(ROUTE, json=_runtime_payload("button1_find_fights", execute_preview=True))
    data = resp.get_json()

    summary = data["workflow"]["jobs"][0]["output_preview"]["summary"]
    assert summary["discovered_count"] == 0
    assert summary["extracted_count"] == 0
    token_preview = data["workflow"]["gate_approval_token_preview"]
    assert token_preview["write_authorized"] is False
