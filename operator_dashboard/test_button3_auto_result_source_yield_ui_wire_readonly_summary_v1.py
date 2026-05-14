"""
test_button3_auto_result_source_yield_ui_wire_readonly_summary_v1.py

Tests that the Button 3 UI (index.html) correctly wires to the executor endpoint
and that the dashboard structure is preserved (3 buttons, 3 gates, read-only summary).

This is the predecessor slice test — must remain green.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import pytest
from operator_dashboard.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def get_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


EXECUTOR_ENDPOINT = "/api/operator/button3/auto-result-source-yield-live-executor-preview"


class TestButton3UIWireReadonlySummary:

    def test_index_renders_200(self, client):
        assert client.get("/").status_code == 200

    def test_executor_endpoint_in_template(self, client):
        html = get_html(client)
        assert EXECUTOR_ENDPOINT in html, \
            f"Executor endpoint '{EXECUTOR_ENDPOINT}' not found in template"

    def test_five_state_labels_in_template(self, client):
        html = get_html(client)
        for label in ["Results Found", "Needs Source", "Conflict",
                      "No Result Yet", "Ready to Compare"]:
            assert label in html, f"State label '{label}' not found in template"

    def test_template_has_three_main_buttons(self, client):
        html = get_html(client)
        buttons = re.findall(r'class="btn-main"', html)
        assert len(buttons) == 3

    def test_template_has_b3_result_panel(self, client):
        html = get_html(client)
        assert "b3-result-panel" in html

    def test_template_does_not_expose_row_details_in_normal_mode(self, client):
        html = get_html(client)
        assert "row_details" not in html
        assert "row-details" not in html

    def test_template_does_not_expose_telemetry_labels(self, client):
        html = get_html(client)
        # Governance labels must not appear in the normal UI
        assert "mutation_performed" not in html
        assert "calibration_write_performed" not in html

    def test_template_no_new_main_buttons_beyond_three(self, client):
        html = get_html(client)
        buttons = re.findall(r'class="btn-main"', html)
        assert len(buttons) == 3

    def test_template_has_three_operator_gates(self, client):
        html = get_html(client)
        gates = re.findall(r'btn-gate', html)
        assert len(gates) == 3

    def test_template_no_apply_button_in_normal_mode(self, client):
        html = get_html(client).lower()
        assert "apply result" not in html
        assert "apply-result" not in html

    def test_template_no_learning_button(self, client):
        html = get_html(client).lower()
        assert "learning" not in html or "approve" not in html  # gate notice OK, button not
        # specifically: no standalone learning action button
        assert 'onclick="handleLearning' not in html

    def test_summary_grid_has_five_state_cards(self, client):
        html = get_html(client)
        cards = re.findall(r'class="state-card"', html)
        assert len(cards) == 5

    def test_advanced_dashboard_link_present(self, client):
        html = get_html(client)
        assert "/advanced-dashboard" in html
