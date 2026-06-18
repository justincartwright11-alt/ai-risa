import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.button2_customer_flow_dry_run_contract_preview_v1 import (
    run_button2_customer_flow_dry_run_contract_preview,
)
import operator_dashboard.button2_customer_flow_dry_run_contract_preview_v1 as dry_run_module


ROUTE = "/api/operator/button2/customer-flow/dry-run-contract-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _payload(operator_approved=True, fight_id="hardening_fight_id", ingest_payload=None, render_gate_ready=True):
    if ingest_payload is None:
        ingest_payload = {"destination_marker": "button2_report_generation_preview"}
    return {
        "operator_approved": operator_approved,
        "fight_id": fight_id,
        "ingest_payload": ingest_payload,
        "render_gate_ready": render_gate_ready,
    }


def test_route_blocks_malformed_request_body_and_stays_decision_only(client, monkeypatch):
    generation_called = []

    def blocked_generation(*args, **kwargs):
        generation_called.append((args, kwargs))
        raise AssertionError("Dry-run contract must not call customer generation")

    monkeypatch.setattr("operator_dashboard.app.generate_button2_report_render_gate_integration", blocked_generation)

    resp = client.post(ROUTE, json="not-json")
    data = resp.get_json()

    assert resp.status_code == 400
    assert data["ok"] is False
    assert data["dry_run"] is True
    assert data["customer_generation_permitted"] is False
    assert "request body must be an object" in data["blocking_reasons"]
    assert generation_called == []


def test_helper_blocks_when_output_root_is_not_ready(monkeypatch):
    def raise_unconfigured():
        raise dry_run_module.OutputRootNotConfiguredError("BUTTON2_PDF_OUTPUT_ROOT missing")

    monkeypatch.setattr(dry_run_module, "get_pdf_output_root", raise_unconfigured)

    result = run_button2_customer_flow_dry_run_contract_preview(_payload())
    data = result.to_dict()

    assert data["ok"] is True
    assert data["decision"] == "blocked"
    assert data["customer_generation_permitted"] is False
    assert data["readiness_snapshot"]["output_root_ready"] is False
    assert "customer_generation_not_authorized" in data["blocking_reasons"]
