"""
test_operator_dashboard_button3_idiot_proof_review_results_flow_v1.py

Tests for the Button 3 idiot-proof operator flow:
  - Click → preview-only scan → show 5 simple states → operator gate before any write.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pytest
from operator_dashboard.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

ENDPOINT = "/api/operator/button3/auto-result-source-yield-live-executor-preview"


class TestButton3IdiotProofFlow:

    def test_endpoint_exists(self, client):
        resp = client.post(ENDPOINT, json={})
        assert resp.status_code == 200

    def test_endpoint_returns_ok_true(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert data["ok"] is True

    def test_endpoint_preview_only_flag(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert data["preview_only"] is True

    def test_endpoint_returns_summary_with_five_states(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        summary = data.get("summary", {})
        for state in ["Results Found", "Needs Source", "Conflict", "No Result Yet", "Ready to Compare"]:
            assert state in summary, f"Missing state: {state}"

    def test_endpoint_telemetry_no_mutations(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        tel = data.get("telemetry", {})
        assert tel.get("mutation_performed") is False
        assert tel.get("durable_write_performed") is False
        assert tel.get("learning_apply_performed") is False
        assert tel.get("calibration_write_performed") is False
        assert tel.get("queue_write_performed") is False
        assert tel.get("auto_apply_performed") is False

    def test_apply_result_endpoint_requires_operator_approval(self, client):
        resp = client.post("/api/operator/button3/apply-result",
                           json={"operator_approved": False})
        assert resp.status_code == 403

    def test_apply_result_gate_blocks_unapproved(self, client):
        resp = client.post("/api/operator/button3/apply-result", json={})
        data = resp.get_json()
        assert resp.status_code == 403
        assert "operator_approval_required" in data.get("error", "")

    def test_apply_result_gate_passes_with_approval(self, client):
        resp = client.post("/api/operator/button3/apply-result",
                           json={"operator_approved": True})
        data = resp.get_json()
        assert data["ok"] is True

    def test_endpoint_no_row_details_by_default(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        # row_details must not appear in default response
        assert "row_details" not in data

    def test_endpoint_row_details_present_when_requested(self, client):
        resp = client.post(ENDPOINT, json={"include_advanced_diagnostics": True})
        data = resp.get_json()
        assert "row_details" in data

    def test_endpoint_accepts_limit_parameter(self, client):
        resp = client.post(ENDPOINT, json={"limit": 10})
        assert resp.status_code == 200

    def test_endpoint_accepts_selected_keys(self, client):
        resp = client.post(ENDPOINT, json={"selected_keys": ["fight_001"]})
        assert resp.status_code == 200

    def test_endpoint_rejects_non_list_selected_keys(self, client):
        resp = client.post(ENDPOINT, json={"selected_keys": "not_a_list"})
        assert resp.status_code == 400
