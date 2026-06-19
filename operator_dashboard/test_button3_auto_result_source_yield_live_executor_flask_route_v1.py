"""
test_button3_auto_result_source_yield_live_executor_flask_route_v1.py

Tests for the Flask route:
  POST /api/operator/button3/auto-result-source-yield-live-executor-preview

Covers: basic functionality, response structure, telemetry flags,
request parameter handling, diagnostics visibility, no mutations, error handling.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pytest
from operator_dashboard.app import app as flask_app

ENDPOINT = "/api/operator/button3/auto-result-source-yield-live-executor-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── Endpoint Basic Functionality ──────────────────────────────────────────────

class TestEndpointBasicFunctionality:

    def test_endpoint_exists_returns_200(self, client):
        resp = client.post(ENDPOINT, json={})
        assert resp.status_code == 200

    def test_endpoint_returns_json(self, client):
        resp = client.post(ENDPOINT, json={})
        assert resp.content_type.startswith("application/json")

    def test_endpoint_ok_true(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert data["ok"] is True

    def test_endpoint_preview_only_true(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert data["preview_only"] is True

    def test_endpoint_accessible_without_body(self, client):
        resp = client.post(ENDPOINT)
        assert resp.status_code == 200


# ── Response Structure ────────────────────────────────────────────────────────

class TestResponseStructure:

    def test_has_summary_field(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert "summary" in data

    def test_has_row_states_field(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert "row_states" in data

    def test_has_telemetry_field(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert "telemetry" in data

    def test_summary_has_all_five_states(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        summary = data["summary"]
        for state in ["Results Found", "Needs Source", "Conflict",
                      "No Result Yet", "Ready to Compare"]:
            assert state in summary, f"Missing state: {state}"

    def test_summary_has_total_rows(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert "total_rows" in data["summary"]

    def test_executor_version_present(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert "executor_version" in data


# ── Telemetry Flags ───────────────────────────────────────────────────────────

class TestTelemetryFlagsViaRoute:

    def test_mutation_performed_false(self, client):
        resp = client.post(ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["mutation_performed"] is False

    def test_durable_write_performed_false(self, client):
        resp = client.post(ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["durable_write_performed"] is False

    def test_learning_apply_performed_false(self, client):
        resp = client.post(ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["learning_apply_performed"] is False

    def test_calibration_write_performed_false(self, client):
        resp = client.post(ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["calibration_write_performed"] is False

    def test_queue_write_performed_false(self, client):
        resp = client.post(ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["queue_write_performed"] is False

    def test_auto_apply_performed_false(self, client):
        resp = client.post(ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["auto_apply_performed"] is False

    def test_preview_only_true_in_telemetry(self, client):
        resp = client.post(ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["preview_only"] is True


# ── Request Parameter Handling ────────────────────────────────────────────────

class TestRequestParameterHandling:

    def test_limit_parameter_accepted(self, client):
        resp = client.post(ENDPOINT, json={"limit": 10})
        assert resp.status_code == 200

    def test_limit_clipped_to_max(self, client):
        resp = client.post(ENDPOINT, json={"limit": 9999})
        assert resp.status_code == 200

    def test_limit_clipped_to_min(self, client):
        resp = client.post(ENDPOINT, json={"limit": 0})
        assert resp.status_code == 200

    def test_selected_keys_accepted(self, client):
        resp = client.post(ENDPOINT, json={"selected_keys": ["fight_a"]})
        assert resp.status_code == 200

    def test_include_advanced_diagnostics_false_default(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        assert "row_details" not in data

    def test_include_advanced_diagnostics_true_shows_row_details(self, client):
        resp = client.post(ENDPOINT,
                           json={"include_advanced_diagnostics": True})
        data = resp.get_json()
        assert "row_details" in data


# ── Diagnostics Visibility ────────────────────────────────────────────────────

class TestDiagnosticsVisibility:

    def test_row_details_hidden_by_default(self, client):
        resp = client.post(ENDPOINT, json={})
        assert "row_details" not in resp.get_json()

    def test_telemetry_field_present_but_not_advanced(self, client):
        resp = client.post(ENDPOINT, json={})
        data = resp.get_json()
        # telemetry is always present, but advanced diagnostics (row_details) are not
        assert "telemetry" in data
        assert "row_details" not in data


# ── No Mutations ──────────────────────────────────────────────────────────────

class TestNoMutationsViaRoute:

    def test_repeated_calls_produce_consistent_results(self, client):
        resp1 = client.post(ENDPOINT, json={})
        resp2 = client.post(ENDPOINT, json={})
        d1 = resp1.get_json()
        d2 = resp2.get_json()
        assert d1["summary"] == d2["summary"]
        assert d1["ok"] == d2["ok"]


# ── Error Handling ────────────────────────────────────────────────────────────

class TestErrorHandling:

    def test_non_json_body_still_returns_200(self, client):
        # Empty POST without Content-Type: should gracefully handle
        resp = client.post(ENDPOINT)
        assert resp.status_code == 200

    def test_invalid_selected_keys_type_returns_400(self, client):
        resp = client.post(ENDPOINT, json={"selected_keys": "not_a_list"})
        assert resp.status_code == 400

    def test_400_response_includes_telemetry(self, client):
        resp = client.post(ENDPOINT, json={"selected_keys": "bad"})
        data = resp.get_json()
        assert "telemetry" in data
        assert data["telemetry"]["mutation_performed"] is False


# ── Dashboard Preservation ────────────────────────────────────────────────────

class TestDashboardPreservationViaRoute:

    def test_normal_dashboard_still_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_advanced_dashboard_still_returns_200(self, client):
        resp = client.get("/advanced-dashboard")
        assert resp.status_code == 200
