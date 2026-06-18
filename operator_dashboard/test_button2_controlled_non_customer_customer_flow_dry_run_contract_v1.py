import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.button2_customer_flow_dry_run_contract_preview_v1 import (
    run_button2_customer_flow_dry_run_contract_preview,
)


ROUTE = "/api/operator/button2/customer-flow/dry-run-contract-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _payload(operator_approved=True, fight_id="test_fight_id", ingest_payload=None, render_gate_ready=True):
    if ingest_payload is None:
        ingest_payload = {"destination_marker": "button2_report_generation_preview"}
    return {
        "operator_approved": operator_approved,
        "fight_id": fight_id,
        "ingest_payload": ingest_payload,
        "render_gate_ready": render_gate_ready,
    }


def test_dry_run_contract_returns_decision_only_payload(client, monkeypatch, tmp_path):
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["dry_run"] is True
    assert data["customer_generation_permitted"] is False
    assert data["render_execution_performed"] is False
    assert data["pdf_file_write_performed"] is False
    assert data["delivery_performed"] is False
    assert data["queue_database_write_performed"] is False
    assert data["button1_changed"] is False
    assert data["button3_changed"] is False
    assert data["decision"] == "preconditions_validated_readonly"
    assert data["readiness_snapshot"]["output_root_ready"] is True
    assert data["readiness_snapshot"]["render_gate_ready"] is True
    assert "dry_run_only" in data["blocking_reasons"]
    assert "customer_generation_not_authorized" in data["blocking_reasons"]


def test_dry_run_contract_blocks_missing_operator_gate(client, monkeypatch, tmp_path):
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    resp = client.post(ROUTE, json=_payload(operator_approved=False))
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["decision"] == "blocked"
    assert data["customer_generation_permitted"] is False
    assert "operator_gate_required" in data["blocking_reasons"]


def test_dry_run_contract_does_not_call_generation_render_write_or_network(client, monkeypatch, tmp_path):
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during Button 2 dry-run contract execution")
        return real_open(*args, **kwargs)

    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    def blocked_generation(*args, **kwargs):
        raise AssertionError("Customer generation route must not be called from dry-run contract")

    monkeypatch.setattr("builtins.open", guarded_open)
    monkeypatch.setattr(socket, "create_connection", blocked_connect)
    monkeypatch.setattr("operator_dashboard.app.generate_button2_report_render_gate_integration", blocked_generation)

    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()

    assert resp.status_code == 200
    assert opened_for_write == []
    assert data["render_execution_performed"] is False
    assert data["pdf_file_write_performed"] is False
    assert data["delivery_performed"] is False
    assert data["queue_database_write_performed"] is False


def test_helper_returns_readonly_blocked_payload_without_generation(monkeypatch, tmp_path):
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    result = run_button2_customer_flow_dry_run_contract_preview(_payload())
    data = result.to_dict()

    assert data["ok"] is True
    assert data["dry_run"] is True
    assert data["customer_generation_permitted"] is False
    assert data["button1_changed"] is False
    assert data["button3_changed"] is False
    assert data["readiness_snapshot"]["fight_id_present"] is True