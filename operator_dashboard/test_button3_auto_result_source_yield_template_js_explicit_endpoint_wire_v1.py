"""Focused tests for Button 3 result-comparison preview endpoint dashboard wire."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import pytest
from operator_dashboard.app import app as flask_app

PREVIEW_ENDPOINT = "/api/button3/result-comparison/preview-v1"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def get_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


# ── Requirement 1/2: Button 3 click flow references preview endpoint ──────────

class TestButton3ClickFlowReferencesEndpoint:

    def test_endpoint_literal_in_js_constant(self, client):
        """The preview endpoint literal must exist in template JavaScript."""
        html = get_html(client)
        assert PREVIEW_ENDPOINT in html, (
            f"Preview endpoint '{PREVIEW_ENDPOINT}' not found in template"
        )

    def test_b3_preview_endpoint_constant_defined(self, client):
        html = get_html(client)
        assert "B3_RESULT_COMPARISON_PREVIEW_ENDPOINT" in html

    def test_fetch_call_uses_preview_endpoint_constant(self, client):
        html = get_html(client)
        assert "fetch(B3_RESULT_COMPARISON_PREVIEW_ENDPOINT" in html

    def test_button3_click_invokes_preview_post_helper(self, client):
        html = get_html(client)
        assert "postButton3ResultComparisonPreview({})" in html

    def test_button3_click_no_longer_uses_runtime_context_workflow_preview(self, client):
        html = get_html(client)
        assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_RESULTS)" not in html

    def test_handlebutton3click_function_defined(self, client):
        html = get_html(client)
        assert "handleButton3Click" in html

    def test_button3_onclick_wires_to_handler(self, client):
        html = get_html(client)
        assert "handleButton3Click()" in html


# ── Requirement 3/4/5/6/7/8/9/10/11/12/13/14/15/16: endpoint contract ───────

class TestResultComparisonPreviewEndpointContract:

    def _base_payload(self):
        return {
            "fight_id": "f-200",
            "event_name": "Preview Event",
            "fighter_a": "Fighter A",
            "fighter_b": "Fighter B",
            "predicted_winner": "Fighter A",
            "predicted_method": "decision",
            "predicted_round": "3",
            "actual_winner": "Fighter A",
            "actual_method": "decision",
            "actual_round": "3",
            "result_source_url": "https://example.com/result",
            "source_tier": "official",
        }

    def test_preview_response_includes_comparison_status(self, client):
        data = client.post(PREVIEW_ENDPOINT, json=self._base_payload()).get_json()
        assert "comparison_status" in data

    def test_preview_response_includes_provenance_visibility(self, client):
        data = client.post(PREVIEW_ENDPOINT, json=self._base_payload()).get_json()
        assert "result_source_url" in data
        assert "source_tier" in data

    def test_partial_evidence_remains_blocked(self, client):
        payload = self._base_payload()
        payload["actual_method"] = ""
        payload["actual_round"] = ""
        data = client.post(PREVIEW_ENDPOINT, json=payload).get_json()
        assert data["comparison_status"] == "needs_manual_review"

    def test_unknown_comparison_status_remains_blocked(self, client):
        payload = self._base_payload()
        payload["comparison_status"] = "unknown_state"
        data = client.post(PREVIEW_ENDPOINT, json=payload).get_json()
        assert data["comparison_status"] == "needs_manual_review"

    def test_duplicate_same_result_evidence_remains_blocked(self, client):
        payload = self._base_payload()
        payload["conflicting_sources"] = [
            {"actual_winner": "Fighter A", "actual_method": "decision", "actual_round": "3"},
            {"actual_winner": "Fighter A", "actual_method": "decision", "actual_round": "3"},
        ]
        data = client.post(PREVIEW_ENDPOINT, json=payload).get_json()
        assert data["comparison_status"] == "needs_manual_review"

    def test_stale_result_evidence_remains_blocked(self, client):
        payload = self._base_payload()
        payload["stale_result_evidence"] = True
        data = client.post(PREVIEW_ENDPOINT, json=payload).get_json()
        assert data["comparison_status"] == "needs_manual_review"

    def test_no_apply_endpoint_is_exposed(self):
        routes = {rule.rule for rule in flask_app.url_map.iter_rules()}
        assert "/api/button3/result-comparison/apply-v1" not in routes

    def test_no_database_or_queue_write_flags(self, client):
        data = client.post(PREVIEW_ENDPOINT, json=self._base_payload()).get_json()
        assert data.get("database_write_performed", False) is False
        assert data["queue_write_performed"] is False

    def test_no_accuracy_ledger_mutation_flag(self, client):
        data = client.post(PREVIEW_ENDPOINT, json=self._base_payload()).get_json()
        assert data.get("accuracy_ledger_mutation_performed", False) is False

    def test_no_learning_or_calibration_mutation_flags(self, client):
        data = client.post(PREVIEW_ENDPOINT, json=self._base_payload()).get_json()
        assert data["learning_apply_performed"] is False
        assert data["calibration_write_performed"] is False

    def test_no_customer_output_generated(self, client):
        data = client.post(PREVIEW_ENDPOINT, json=self._base_payload()).get_json()
        assert data.get("customer_report_generated", False) is False

    def test_button1_and_button2_authority_not_authorized(self, client):
        data = client.post(PREVIEW_ENDPOINT, json=self._base_payload()).get_json()
        assert data.get("button1_source_call_authorized", False) is False
        assert data.get("button2_generation_authorized", False) is False

    def test_operator_approval_not_consumed_as_execution_authority(self, client):
        payload = self._base_payload()
        payload["operator_approved"] = True
        payload["operator_approval_token"] = "display-only"
        data = client.post(PREVIEW_ENDPOINT, json=payload).get_json()
        assert data["mutation_performed"] is False
        assert data["button3_mutation_performed"] is False


# ── Dashboard structure still constrained to 3-button normal mode ────────────

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
