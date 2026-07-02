import pytest
from unittest.mock import Mock, patch

from operator_dashboard.app import app as flask_app


ENDPOINT = "/api/button3/result-comparison/preview-v1"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _base_payload():
    return {
        "fight_id": "anthony_joshua_vs_daniel_dubois",
        "event_name": "Joshua vs Dubois",
        "fighter_a": "Anthony Joshua",
        "fighter_b": "Daniel Dubois",
        "predicted_winner": "Anthony Joshua",
        "predicted_method": "KO",
        "predicted_round": 7,
        "actual_winner": "Anthony Joshua",
        "actual_method": "KO",
        "actual_round": 7,
        "result_source_url": "https://www.example.com/result",
        "source_tier": "tier_a",
    }


def _with_apply_authorization_context(payload):
    data = dict(payload)
    data.update({
        "predicted_time": "04:12",
        "actual_time": "04:12",
        "structural_evidence_score": 0.92,
        "operator_id": "op_001",
        "approval_action": "apply_official_result",
        "operation_id": "operation_001",
        "approval_state": "approved",
        "upstream_states": {
            "source_trust_passed": True,
            "identity_match_passed": True,
            "scope_match": True,
            "conflict_detected": False,
            "stale_context": False,
            "unknown_state_detected": False,
        },
        "contract_gates": {
            "source_trust_gate_passed": True,
            "identity_match_gate_passed": True,
            "apply_authorization_gate_passed": True,
            "accuracy_ledger_contract_gate_passed": True,
        },
    })
    return data


def test_matched_winner_comparison_returns_hit_classification(client):
    resp = client.post(ENDPOINT, json=_base_payload())
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["comparison_status"] == "ready_to_compare"
    assert data["accuracy_preview"]["winner"] == "hit"
    assert data["accuracy_preview"]["overall"] == "hit"


def test_wrong_winner_comparison_returns_miss_classification(client):
    payload = _base_payload()
    payload["actual_winner"] = "Daniel Dubois"
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert data["accuracy_preview"]["winner"] == "miss"
    assert data["accuracy_preview"]["overall"] == "miss"


def test_method_mismatch_is_captured(client):
    payload = _base_payload()
    payload["actual_method"] = "Decision"
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert data["accuracy_preview"]["method"] == "miss"
    assert data["accuracy_preview"]["method_mismatch"] is True


def test_round_mismatch_is_captured(client):
    payload = _base_payload()
    payload["actual_round"] = 5
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert data["accuracy_preview"]["round"] == "miss"
    assert data["accuracy_preview"]["round_mismatch"] is True


def test_no_result_returns_no_result_found(client):
    payload = _base_payload()
    payload["actual_winner"] = ""
    payload["actual_method"] = ""
    payload["actual_round"] = ""
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert data["comparison_status"] == "no_result_found"


def test_conflicting_source_returns_conflict(client):
    payload = _base_payload()
    payload["conflicting_sources"] = [
        {"actual_winner": "Anthony Joshua", "actual_method": "KO", "actual_round": 7},
        {"actual_winner": "Daniel Dubois", "actual_method": "Decision", "actual_round": 10},
    ]
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert data["comparison_status"] == "conflict"


def test_missing_source_returns_needs_source(client):
    payload = _base_payload()
    payload["result_source_url"] = ""
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert data["comparison_status"] == "needs_source"


def test_manual_review_candidate_returns_needs_manual_review(client):
    payload = _base_payload()
    payload["manual_review_candidate"] = True
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert data["comparison_status"] == "needs_manual_review"


def test_all_mutation_flags_remain_false(client):
    resp = client.post(ENDPOINT, json=_base_payload())
    data = resp.get_json()
    assert data["mutation_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_learning_and_calibration_flags_remain_false(client):
    resp = client.post(ENDPOINT, json=_base_payload())
    data = resp.get_json()
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False


def test_route_returns_preview_only_payload(client):
    resp = client.post(ENDPOINT, json=_base_payload())
    data = resp.get_json()
    assert data["ok"] is True
    assert data["preview_only"] is True
    assert data["operator_approval_gate_required_for_apply"] is True


def test_dashboard_text_includes_preview_only_language(client):
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert "Preview-only comparison path" in html
    assert "no apply, no learning, no calibration" in html


def test_no_apply_endpoint_opened_for_result_comparison_path():
    routes = {rule.rule for rule in flask_app.url_map.iter_rules()}
    assert "/api/button3/result-comparison/apply-v1" not in routes


def test_required_fields_present_in_preview_payload(client):
    resp = client.post(ENDPOINT, json=_with_apply_authorization_context(_base_payload()))
    data = resp.get_json()
    for field in [
        "fight_id",
        "event_name",
        "fighter_a",
        "fighter_b",
        "predicted_winner",
        "predicted_method",
        "predicted_round",
        "actual_winner",
        "actual_method",
        "actual_round",
        "result_source_url",
        "source_tier",
        "comparison_status",
        "accuracy_preview",
        "authorization_state",
        "authorized",
        "authorization_reason_code",
        "authorization_reason_detail",
        "authorization_operator_id",
        "authorization_approval_action",
        "authorization_operation_id",
        "authorization_evaluated_at_utc",
        "apply_authorization",
        "operator_review_required",
    ]:
        assert field in data


def test_apply_authorization_defaults_to_deny_without_context(client):
    resp = client.post(ENDPOINT, json=_base_payload())
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["authorization_state"] == "denied"
    assert data["authorized"] is False
    assert data["authorization_reason_code"] == "missing_operator_id"


def test_apply_authorization_allows_only_when_all_preconditions_pass(client):
    payload = _with_apply_authorization_context(_base_payload())
    resp = client.post(ENDPOINT, json=payload)
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["comparison_status"] == "ready_to_compare"
    assert data["authorization_state"] == "eligible"
    assert data["authorized"] is True
    assert data["authorization_reason_code"] == "eligible"
    assert data["accuracy_ledger_state"] == "eligible"
    assert data["accuracy_ledger_eligible"] is True


def test_accuracy_dimension_separation_fields_present(client):
    payload = _with_apply_authorization_context(_base_payload())
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["outcome_accuracy_state"] == "hit"
    assert data["method_accuracy_state"] == "hit"
    assert data["timing_accuracy_state"] == "hit"
    assert data["structural_accuracy_state"] == "pass"


def test_accuracy_dimension_method_miss_does_not_change_outcome_state(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload["actual_method"] = "Decision"
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["outcome_accuracy_state"] == "hit"
    assert data["method_accuracy_state"] == "miss"


def test_accuracy_dimension_timing_miss_does_not_change_outcome_state(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload["actual_round"] = "1"
    payload["actual_time"] = "00:22"
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["outcome_accuracy_state"] == "hit"
    assert data["timing_accuracy_state"] == "miss"


def test_winner_only_signal_is_denied(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload["comparison_status"] = "ready_to_compare"
    payload["actual_method"] = ""
    payload["actual_round"] = ""
    payload["actual_time"] = ""
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["accuracy_ledger_state"] == "denied"
    assert data["accuracy_ledger_reason_code"] == "winner_only_signal"
    assert data["winner_only_reinforcement_blocked"] is True


def test_lucky_prediction_signal_is_denied(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload["lucky_prediction_signal"] = True
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["accuracy_ledger_state"] == "denied"
    assert data["accuracy_ledger_reason_code"] == "lucky_prediction_signal"
    assert data["lucky_prediction_reinforcement_blocked"] is True


def test_missing_contract_gates_is_denied_for_accuracy_ledger(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload.pop("contract_gates", None)
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["accuracy_ledger_state"] == "denied"
    assert data["accuracy_ledger_reason_code"] == "missing_contract_gates"


def test_prerequisite_gate_failures_are_denied_for_accuracy_ledger(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload["contract_gates"]["apply_authorization_gate_passed"] = False
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["accuracy_ledger_state"] == "denied"
    assert data["accuracy_ledger_reason_code"] == "apply_authorization_gate_not_passed"


def test_no_ledger_write_execution_even_when_eligible(client):
    payload = _with_apply_authorization_context(_base_payload())
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["accuracy_ledger_eligible"] is True
    assert data["accuracy_ledger_write_performed"] is False
    assert data["accuracy_ledger_mutation_performed"] is False


def test_missing_operator_id_is_denied(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload.pop("operator_id", None)
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == "missing_operator_id"


def test_missing_approval_action_is_denied(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload.pop("approval_action", None)
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == "missing_approval_action"


def test_missing_operation_id_and_request_id_is_denied(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload.pop("operation_id", None)
    payload.pop("request_id", None)
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == "missing_operation_id"


def test_missing_upstream_states_is_denied(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload.pop("upstream_states", None)
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == "missing_upstream_states"


def test_malformed_upstream_states_is_denied(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload["upstream_states"] = ["bad"]
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == "malformed_upstream_states"


@pytest.mark.parametrize(
    "approval_state,reason_code",
    [
        ("expired", "approval_expired"),
        ("revoked", "approval_revoked"),
        ("replayed", "approval_replayed"),
    ],
)
def test_non_approved_approval_state_is_denied(client, approval_state, reason_code):
    payload = _with_apply_authorization_context(_base_payload())
    payload["approval_state"] = approval_state
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == reason_code


@pytest.mark.parametrize(
    "state_key,reason_code,state_value",
    [
        ("source_trust_passed", "source_trust_not_passed", False),
        ("identity_match_passed", "identity_match_not_passed", False),
        ("scope_match", "scope_mismatch", False),
        ("conflict_detected", "conflict_detected", True),
        ("stale_context", "stale_context", True),
        ("unknown_state_detected", "unknown_state", True),
    ],
)
def test_fail_closed_upstream_preconditions_are_denied(client, state_key, reason_code, state_value):
    payload = _with_apply_authorization_context(_base_payload())
    payload["upstream_states"][state_key] = state_value
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == reason_code


def test_unknown_comparison_state_maps_to_deny(client):
    payload = _with_apply_authorization_context(_base_payload())
    payload["comparison_status"] = "weird_future_state"
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["comparison_status"] == "needs_manual_review"
    assert data["authorization_state"] == "denied"
    assert data["authorization_reason_code"] == "comparison_status_not_eligible"


def test_authorization_response_includes_reason_and_identifiers(client):
    payload = _with_apply_authorization_context(_base_payload())
    data = client.post(ENDPOINT, json=payload).get_json()
    assert isinstance(data.get("authorization_reason_code", ""), str)
    assert isinstance(data.get("authorization_reason_detail", ""), str)
    assert data["authorization_operator_id"] == payload["operator_id"]
    assert data["authorization_approval_action"] == payload["approval_action"]
    assert data["authorization_operation_id"] == payload["operation_id"]
    assert isinstance(data.get("authorization_evaluated_at_utc", ""), str)
    assert data.get("authorization_evaluated_at_utc", "")


def test_no_mutation_surfaces_even_when_authorized_eligible(client):
    payload = _with_apply_authorization_context(_base_payload())
    data = client.post(ENDPOINT, json=payload).get_json()
    assert data["authorized"] is True
    assert data["save_performed"] is False
    assert data["database_write_performed"] is False
    assert data["accuracy_ledger_mutation_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["gcid_write_performed"] is False
    assert data["customer_output_changed"] is False
    assert data["customer_report_generated"] is False
    assert data["queue_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_preview_endpoint_invokes_hardened_preview_module(client):
    fake_builder = Mock(return_value={
        "ok": True,
        "preview_only": True,
        "comparison_status": "needs_manual_review",
        "result_source_url": "",
        "source_tier": "unknown",
        "operator_review_required": True,
        "operator_approval_gate_required_for_apply": True,
        "mutation_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "queue_write_performed": False,
        "button3_mutation_performed": False,
    })

    with patch("operator_dashboard.app._lazy_button3_result_comparison_preview", return_value=fake_builder):
        payload = _base_payload()
        resp = client.post(ENDPOINT, json=payload)
        data = resp.get_json()

    assert resp.status_code == 200
    fake_builder.assert_called_once()
    called_payload = fake_builder.call_args[0][0]
    assert called_payload["fight_id"] == payload["fight_id"]
    assert data["preview_only"] is True
