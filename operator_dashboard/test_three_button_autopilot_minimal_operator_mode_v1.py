"""
test_three_button_autopilot_minimal_operator_mode_v1.py

Tests that the normal operator dashboard maintains exactly 3 buttons and 3 gates,
and that no advanced diagnostics, apply, or learning controls are exposed in normal mode.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from operator_dashboard.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def get_dashboard_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


class TestThreeButtonMinimalOperatorMode:

    def test_dashboard_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_dashboard_has_exactly_three_main_buttons(self, client):
        html = get_dashboard_html(client)
        # Count btn-main buttons
        import re
        buttons = re.findall(r'class="btn-main"', html)
        assert len(buttons) == 3, f"Expected 3 main buttons, found {len(buttons)}"

    def test_dashboard_has_three_operator_gates(self, client):
        html = get_dashboard_html(client)
        import re
        gates = re.findall(r'btn-gate', html)
        assert len(gates) == 3, f"Expected 3 operator gates, found {len(gates)}"

    def test_normal_dashboard_no_advanced_diagnostics_panel(self, client):
        html = get_dashboard_html(client)
        # row_details and telemetry must not be rendered in the normal dashboard
        assert "row_details" not in html
        assert "row-details" not in html

    def test_normal_dashboard_no_apply_button(self, client):
        html = get_dashboard_html(client)
        # No apply / learning / calibration buttons in normal mode
        lower = html.lower()
        assert "apply result" not in lower
        assert "apply-result" not in lower
