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


def test_structured_prediction_contract_override_and_backward_compatibility() -> None:
    payload = _base_payload()
    payload["predicted_winner"] = "Top Winner"
    payload["predicted_method"] = "Top Method"
    payload["predicted_round"] = "Top Round"
    payload["structured_prediction"] = {
        "predicted_winner": "Structured Winner",
        "predicted_method": "Structured Method",
        "predicted_round": "Structured Round",
        "confidence": None,
        "structural_reasoning": "reasoning present",
        "tactical_pathway": "",
        "evidence_notes": "notes present",
        "source": "button2_generation_context",
        "contract_version": "button2_structured_prediction_v1",
    }

    response_with_contract = _build(payload)
    assert response_with_contract["predicted_winner"] == "Structured Winner"
    assert response_with_contract["predicted_method"] == "Structured Method"
    assert response_with_contract["predicted_round"] == "Structured Round"
    assert response_with_contract["structured_prediction_context"] == {
        "source": "button2_structured_prediction_contract",
        "contract_version": "button2_structured_prediction_v1",
        "structural_reasoning_present": True,
        "tactical_pathway_present": False,
        "evidence_notes_present": True,
    }

    payload_without_contract = _base_payload()
    payload_without_contract["predicted_winner"] = "Top Winner"
    payload_without_contract["predicted_method"] = "Top Method"
    payload_without_contract["predicted_round"] = "Top Round"

    response_without_contract = _build(payload_without_contract)
    assert response_without_contract["predicted_winner"] == "Top Winner"
    assert response_without_contract["predicted_method"] == "Top Method"
    assert response_without_contract["predicted_round"] == "Top Round"
    assert response_without_contract["structured_prediction_context"] is None
    assert response_without_contract["structural_evidence_preview"] == {
        "score": 0.0,
        "state": "unavailable",
        "reason_code": "no_structured_prediction_contract",
        "non_mutating": True,
        "learning_eligibility_effect": "none",
    }
    assert response_without_contract["accuracy_preview"]["overall"] == "miss"

    payload_one_structural = _base_payload()
    payload_one_structural["structured_prediction"] = {
        "predicted_winner": "Fighter A",
        "predicted_method": "decision",
        "predicted_round": "3",
        "contract_version": "button2_structured_prediction_v1",
        "structural_reasoning": "only one",
        "tactical_pathway": "",
        "evidence_notes": "",
    }
    response_one_structural = _build(payload_one_structural)
    assert response_one_structural["structural_evidence_preview"]["score"] == 0.33
    assert response_one_structural["structural_evidence_preview"]["state"] == "weak"
    assert response_one_structural["structural_evidence_preview"]["reason_code"] == "one_structural_field_present"
    assert response_one_structural["accuracy_preview"]["overall"] == "hit"

    payload_two_structural = _base_payload()
    payload_two_structural["structured_prediction"] = {
        "predicted_winner": "Fighter A",
        "predicted_method": "decision",
        "predicted_round": "3",
        "contract_version": "button2_structured_prediction_v1",
        "structural_reasoning": "present",
        "tactical_pathway": "present",
        "evidence_notes": "",
    }
    response_two_structural = _build(payload_two_structural)
    assert response_two_structural["structural_evidence_preview"]["score"] == 0.66
    assert response_two_structural["structural_evidence_preview"]["state"] == "partial"
    assert response_two_structural["structural_evidence_preview"]["reason_code"] == "two_structural_fields_present"
    assert response_two_structural["accuracy_preview"]["overall"] == "hit"

    payload_three_structural = _base_payload()
    payload_three_structural["structured_prediction"] = {
        "predicted_winner": "Fighter A",
        "predicted_method": "decision",
        "predicted_round": "3",
        "contract_version": "button2_structured_prediction_v1",
        "structural_reasoning": "present",
        "tactical_pathway": "present",
        "evidence_notes": "present",
    }
    response_three_structural = _build(payload_three_structural)
    assert response_three_structural["structural_evidence_preview"]["score"] == 1.0
    assert response_three_structural["structural_evidence_preview"]["state"] == "supported"
    assert response_three_structural["structural_evidence_preview"]["reason_code"] == "all_structural_fields_present"
    assert response_three_structural["accuracy_preview"]["overall"] == "hit"

    assert response_with_contract["mutation_performed"] is False
    assert response_with_contract["database_write_performed"] is False
    assert response_with_contract["queue_write_performed"] is False
    assert response_with_contract["button3_mutation_performed"] is False
    assert response_with_contract["controlled_learning_candidate_eligible"] is False
    assert response_with_contract["structural_evidence_preview"]["learning_eligibility_effect"] == "none"


def test_method_round_normalization_preview_scoring_contract() -> None:
    payload = _base_payload()
    payload["predicted_method"] = "Decision"
    payload["actual_method"] = "Decision (unanimous)"
    payload["predicted_round"] = "Full Distance"
    payload["actual_round"] = "5"
    payload["scheduled_rounds"] = 5

    response = _build(payload)
    preview = response["method_round_normalization_preview"]

    # Method and round should score as matched after normalization.
    assert response["accuracy_preview"]["method"] == "hit"
    assert response["accuracy_preview"]["round"] == "hit"
    assert preview["predicted_method_normalized"] == "decision"
    assert preview["actual_method_normalized"] == "decision"
    assert preview["predicted_round_normalized"] == "5"
    assert preview["actual_round_normalized"] == "5"
    assert preview["scheduled_rounds"] == 5
    assert preview["full_distance_resolved"] is True
    assert preview["learning_eligibility_effect"] == "none"

    # Raw fields remain unchanged in the response payload.
    assert response["predicted_method"] == "Decision"
    assert response["predicted_round"] == "Full Distance"
    assert response["actual_method"] == "Decision (unanimous)"
    assert response["actual_round"] == "5"

    # Without scheduled rounds, full distance must not be forced to round 5.
    payload_without_schedule = _base_payload()
    payload_without_schedule["predicted_method"] = "Decision"
    payload_without_schedule["actual_method"] = "Decision (unanimous)"
    payload_without_schedule["predicted_round"] = "Full Distance"
    payload_without_schedule["actual_round"] = "5"
    response_without_schedule = _build(payload_without_schedule)
    preview_without_schedule = response_without_schedule["method_round_normalization_preview"]
    assert preview_without_schedule["predicted_round_normalized"] == "full_distance"
    assert preview_without_schedule["full_distance_resolved"] is False
    assert response_without_schedule["accuracy_preview"]["round"] == "miss"

    # R5 should normalize to 5.
    payload_r5 = _base_payload()
    payload_r5["predicted_round"] = "R5"
    payload_r5["actual_round"] = "5"
    response_r5 = _build(payload_r5)
    preview_r5 = response_r5["method_round_normalization_preview"]
    assert preview_r5["predicted_round_normalized"] == "5"
    assert response_r5["accuracy_preview"]["round"] == "hit"

    # Non-mutating and policy boundaries remain unchanged.
    assert response["mutation_performed"] is False
    assert response["database_write_performed"] is False
    assert response["queue_write_performed"] is False
    assert response["learning_apply_performed"] is False
    assert response["button3_mutation_performed"] is False
    assert response["controlled_learning_candidate_eligible"] is False
