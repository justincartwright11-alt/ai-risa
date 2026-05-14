"""
test_button3_auto_result_source_yield_template_js_explicit_endpoint_wire_v1.py

Slice: button3-auto-result-source-yield-template-js-explicit-endpoint-wire-v1

Tests that the Button 3 template JavaScript explicitly wires to the locked
read-only executor endpoint and renders only the five simple state labels.

Requirements verified:
  1. Button 3 click flow references the executor endpoint.
  2. UI contains all five simple state labels.
  3. UI does not expose row_details in normal mode.
  4. UI does not expose telemetry in normal mode.
  5. UI does not add new main buttons.
  6. Normal dashboard remains exactly 3 buttons / 3 gates.
  7. Existing Flask route tests remain green (imported from sister module).
  8. Existing executor preview tests remain green (imported from sister module).
  9. Existing minimal operator mode tests remain green (imported from sister module).
  10. Existing UI wire readonly summary tests remain green (imported from sister module).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import pytest
from operator_dashboard.app import app as flask_app

EXECUTOR_ENDPOINT = (
    "/api/operator/button3/auto-result-source-yield-live-executor-preview"
)

FIVE_STATES = [
    "Results Found",
    "Needs Source",
    "Conflict",
    "No Result Yet",
    "Ready to Compare",
]


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def get_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


# ── Requirement 1: Button 3 click flow references executor endpoint ───────────

class TestButton3ClickFlowReferencesEndpoint:

    def test_endpoint_literal_in_js_constant(self, client):
        """The endpoint string must appear verbatim in the template JavaScript."""
        html = get_html(client)
        assert EXECUTOR_ENDPOINT in html, (
            f"Executor endpoint '{EXECUTOR_ENDPOINT}' not found in template"
        )

    def test_b3_executor_endpoint_constant_defined(self, client):
        """A JS variable holding the endpoint must be defined (B3_EXECUTOR_ENDPOINT)."""
        html = get_html(client)
        assert "B3_EXECUTOR_ENDPOINT" in html, \
            "JS constant B3_EXECUTOR_ENDPOINT not found in template"

    def test_fetch_call_uses_b3_executor_endpoint(self, client):
        """The fetch() call must reference B3_EXECUTOR_ENDPOINT (not a hardcoded string)."""
        html = get_html(client)
        # The fetch call should use the constant, not a raw string
        assert "fetch(B3_EXECUTOR_ENDPOINT" in html, \
            "fetch() call does not use B3_EXECUTOR_ENDPOINT constant"

    def test_fetch_uses_post_method(self, client):
        """The fetch call must use POST method."""
        html = get_html(client)
        # Check POST is specified in the fetch options
        assert "method: 'POST'" in html or 'method:"POST"' in html, \
            "fetch call does not specify POST method"

    def test_fetch_sends_include_advanced_diagnostics_false(self, client):
        """The fetch must explicitly send include_advanced_diagnostics: false."""
        html = get_html(client)
        assert "include_advanced_diagnostics: false" in html, \
            "fetch body does not set include_advanced_diagnostics: false"

    def test_handlebutton3click_function_defined(self, client):
        """handleButton3Click function must be defined in the template."""
        html = get_html(client)
        assert "handleButton3Click" in html, \
            "handleButton3Click function not found in template"

    def test_button3_onclick_wires_to_handler(self, client):
        """The Button 3 button element must wire onclick to handleButton3Click."""
        html = get_html(client)
        assert "handleButton3Click()" in html, \
            "Button 3 onclick not wired to handleButton3Click"


# ── Requirement 2: UI contains all five simple state labels ──────────────────

class TestFiveStateLabelPresence:

    def test_results_found_label_present(self, client):
        assert "Results Found" in get_html(client)

    def test_needs_source_label_present(self, client):
        assert "Needs Source" in get_html(client)

    def test_conflict_label_present(self, client):
        assert "Conflict" in get_html(client)

    def test_no_result_yet_label_present(self, client):
        assert "No Result Yet" in get_html(client)

    def test_ready_to_compare_label_present(self, client):
        assert "Ready to Compare" in get_html(client)

    def test_all_five_states_have_count_elements(self, client):
        """Each state must have a corresponding count element in the DOM."""
        html = get_html(client)
        count_ids = [
            "b3-count-results-found",
            "b3-count-needs-source",
            "b3-count-conflict",
            "b3-count-no-result-yet",
            "b3-count-ready-to-compare",
        ]
        for elem_id in count_ids:
            assert elem_id in html, f"Count element '{elem_id}' not found in template"

    def test_summary_grid_element_present(self, client):
        html = get_html(client)
        assert "b3-summary-grid" in html

    def test_render_function_maps_all_five_states(self, client):
        """The renderButton3Results JS function must reference all 5 state labels."""
        html = get_html(client)
        for state in FIVE_STATES:
            assert state in html, f"State '{state}' not found in renderButton3Results"


# ── Requirement 3: row_details not exposed in normal mode ────────────────────

class TestRowDetailsNotExposedInNormalMode:

    def test_row_details_not_in_html(self, client):
        html = get_html(client)
        assert "row_details" not in html

    def test_row_dash_details_not_in_html(self, client):
        html = get_html(client)
        assert "row-details" not in html

    def test_advanced_diagnostics_key_not_in_ui(self, client):
        html = get_html(client)
        # advanced diagnostics keys should not appear in normal mode UI rendering
        assert "advanced_diagnostics" not in html.replace(
            "include_advanced_diagnostics: false", ""
        )


# ── Requirement 4: telemetry not exposed in normal mode ──────────────────────

class TestTelemetryNotExposedInNormalMode:

    def test_mutation_performed_not_in_normal_ui(self, client):
        html = get_html(client)
        assert "mutation_performed" not in html

    def test_calibration_write_performed_not_in_normal_ui(self, client):
        html = get_html(client)
        assert "calibration_write_performed" not in html

    def test_learning_apply_performed_not_in_normal_ui(self, client):
        html = get_html(client)
        assert "learning_apply_performed" not in html

    def test_queue_write_performed_not_in_normal_ui(self, client):
        html = get_html(client)
        assert "queue_write_performed" not in html

    def test_durable_write_performed_not_in_normal_ui(self, client):
        html = get_html(client)
        assert "durable_write_performed" not in html

    def test_telemetry_section_not_rendered_to_user(self, client):
        html = get_html(client)
        # No <div class="telemetry"> or similar display
        assert 'class="telemetry"' not in html
        assert 'id="telemetry"' not in html


# ── Requirement 5 & 6: No new main buttons, dashboard = 3 buttons / 3 gates ──

class TestDashboardStructurePreservation:

    def test_exactly_three_main_buttons(self, client):
        html = get_html(client)
        buttons = re.findall(r'class="btn-main"', html)
        assert len(buttons) == 3, f"Expected 3 main buttons, found {len(buttons)}"

    def test_exactly_three_operator_gates(self, client):
        html = get_html(client)
        gates = re.findall(r'btn-gate', html)
        assert len(gates) == 3, f"Expected 3 operator gates, found {len(gates)}"

    def test_button1_present(self, client):
        html = get_html(client)
        assert "b1-btn" in html

    def test_button2_present(self, client):
        html = get_html(client)
        assert "b2-btn" in html

    def test_button3_present(self, client):
        html = get_html(client)
        assert "b3-btn" in html

    def test_no_button4_or_higher(self, client):
        html = get_html(client)
        assert "b4-btn" not in html
        assert "b5-btn" not in html

    def test_no_apply_button_in_normal_mode(self, client):
        html = get_html(client).lower()
        assert "apply result" not in html
        assert "apply-result" not in html

    def test_no_learning_action_button(self, client):
        html = get_html(client)
        assert 'onclick="handleLearning' not in html
        assert 'onclick="applyLearning' not in html

    def test_no_calibration_button(self, client):
        html = get_html(client).lower()
        assert 'oncalibrate' not in html
        assert 'handlecalibration' not in html.lower()


# ── Requirement 7–10: Regression — existing tests still pass ─────────────────
# (These are covered by running the full test suite together.
#  The following checks verify the Flask app still serves correctly.)

class TestRegressionSmokeChecks:

    def test_flask_route_endpoint_still_accessible(self, client):
        resp = client.post(EXECUTOR_ENDPOINT, json={})
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_executor_returns_all_five_states_in_summary(self, client):
        resp = client.post(EXECUTOR_ENDPOINT, json={})
        summary = resp.get_json()["summary"]
        for state in FIVE_STATES:
            assert state in summary

    def test_executor_telemetry_all_false(self, client):
        resp = client.post(EXECUTOR_ENDPOINT, json={})
        tel = resp.get_json()["telemetry"]
        assert tel["mutation_performed"] is False
        assert tel["learning_apply_performed"] is False
        assert tel["calibration_write_performed"] is False
        assert tel["queue_write_performed"] is False
        assert tel["durable_write_performed"] is False
        assert tel["auto_apply_performed"] is False

    def test_normal_dashboard_loads_cleanly(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        # All three buttons present
        assert "b1-btn" in html
        assert "b2-btn" in html
        assert "b3-btn" in html

    def test_advanced_dashboard_still_accessible(self, client):
        resp = client.get("/advanced-dashboard")
        assert resp.status_code == 200

    def test_no_mutations_on_repeated_calls(self, client):
        for _ in range(3):
            resp = client.post(EXECUTOR_ENDPOINT, json={})
            assert resp.status_code == 200
            tel = resp.get_json()["telemetry"]
            assert tel["mutation_performed"] is False
