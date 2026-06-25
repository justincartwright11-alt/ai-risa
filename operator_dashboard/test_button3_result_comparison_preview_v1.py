from __future__ import annotations

import copy

from operator_dashboard.button3_result_comparison_preview_v1 import (
    build_button3_result_comparison_preview,
)


def _base_payload() -> dict:
    return {
        "fight_id": "f-100",
        "event_name": "Sample Event",
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


def _build(payload: dict) -> dict:
    return build_button3_result_comparison_preview(payload)


def _blocked_statuses() -> set[str]:
    return {"needs_source", "no_result_found", "needs_manual_review", "conflict"}


def test_valid_read_only_result_comparison_produces_preview_response() -> None:
    response = _build(_base_payload())
    assert response["ok"] is True
    assert response["preview_only"] is True
    assert response["comparison_status"] == "ready_to_compare"
    assert response["operator_review_required"] is True


def test_repeating_identical_input_produces_identical_output() -> None:
    payload = _base_payload()
    first = _build(copy.deepcopy(payload))
    second = _build(copy.deepcopy(payload))
    assert first == second


def test_missing_official_result_evidence_fails_closed() -> None:
    payload = _base_payload()
    payload["actual_winner"] = ""
    response = _build(payload)
    assert response["comparison_status"] == "no_result_found"


def test_missing_provenance_fails_closed() -> None:
    payload = _base_payload()
    payload["result_source_url"] = ""
    response = _build(payload)
    assert response["comparison_status"] == "needs_source"


def test_partial_result_evidence_fails_closed() -> None:
    payload = _base_payload()
    payload["actual_method"] = ""
    payload["actual_round"] = ""
    response = _build(payload)
    assert response["comparison_status"] in _blocked_statuses()


def test_conflicting_result_evidence_fails_closed() -> None:
    payload = _base_payload()
    payload["source_conflict"] = True
    response = _build(payload)
    assert response["comparison_status"] == "conflict"


def test_unknown_result_state_fails_closed() -> None:
    payload = _base_payload()
    payload["comparison_status"] = "unknown_state"
    response = _build(payload)
    assert response["comparison_status"] in _blocked_statuses()


def test_duplicate_result_evidence_is_diagnosed_deterministically() -> None:
    payload = _base_payload()
    payload["conflicting_sources"] = [
        {
            "actual_winner": "Fighter A",
            "actual_method": "decision",
            "actual_round": "3",
        },
        {
            "actual_winner": "Fighter A",
            "actual_method": "decision",
            "actual_round": "3",
        },
    ]
    response = _build(payload)
    assert response["comparison_status"] in _blocked_statuses()


def test_stale_result_evidence_is_rejected_or_blocked() -> None:
    payload = _base_payload()
    payload["stale_result_evidence"] = True
    response = _build(payload)
    assert response["comparison_status"] in _blocked_statuses()


def test_preview_does_not_perform_database_writes() -> None:
    response = _build(_base_payload())
    assert response.get("database_write_performed", False) is False


def test_preview_does_not_perform_queue_writes() -> None:
    response = _build(_base_payload())
    assert response["queue_write_performed"] is False


def test_preview_does_not_mutate_accuracy_ledger() -> None:
    response = _build(_base_payload())
    assert response.get("accuracy_ledger_mutation_performed", False) is False


def test_preview_does_not_apply_learning() -> None:
    response = _build(_base_payload())
    assert response["learning_apply_performed"] is False


def test_preview_does_not_apply_calibration() -> None:
    response = _build(_base_payload())
    assert response["calibration_write_performed"] is False


def test_preview_does_not_generate_customer_output() -> None:
    response = _build(_base_payload())
    assert response.get("customer_report_generated", False) is False


def test_preview_does_not_authorize_button1_source_execution() -> None:
    response = _build(_base_payload())
    assert response.get("button1_source_call_authorized", False) is False


def test_preview_does_not_authorize_button2_generation() -> None:
    response = _build(_base_payload())
    assert response.get("button2_generation_authorized", False) is False


def test_preview_does_not_consume_operator_approval_as_execution_authority() -> None:
    payload = _base_payload()
    payload["operator_approved"] = True
    payload["operator_approval_token"] = "token-present-only"
    response = _build(payload)
    assert response["mutation_performed"] is False
    assert response["button3_mutation_performed"] is False


def test_mutation_write_apply_booleans_remain_false() -> None:
    response = _build(_base_payload())
    assert response["mutation_performed"] is False
    assert response["learning_apply_performed"] is False
    assert response["calibration_write_performed"] is False
    assert response["queue_write_performed"] is False
    assert response["button3_mutation_performed"] is False


def test_provenance_and_comparison_status_remain_operator_visible() -> None:
    response = _build(_base_payload())
    assert "result_source_url" in response
    assert "source_tier" in response
    assert "comparison_status" in response
    assert response["operator_review_required"] is True
