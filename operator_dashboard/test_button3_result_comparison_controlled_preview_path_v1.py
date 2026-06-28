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
    resp = client.post(ENDPOINT, json=_base_payload())
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
        "operator_review_required",
    ]:
        assert field in data


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
