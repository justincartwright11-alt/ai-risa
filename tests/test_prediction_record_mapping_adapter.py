import pytest
from ai_risa_prediction_adapter import build_prediction_record
from ai_risa_prediction_schema import PredictionRecord
from datetime import datetime

def minimal_matchup_record():
    return {
        "fighter_a_id": "fighter_a",
        "fighter_b_id": "fighter_b",
        "matchup_id": "test_matchup"
    }

def minimal_context():
    return dict(
        matchup_record=minimal_matchup_record(),
        workflow_type="single_fight",
        prediction_timestamp=datetime(2026, 4, 7, 0, 0, 0),
        fighter_a_profile_path="a.json",
        fighter_b_profile_path="b.json",
        fighter_a_name="A",
        fighter_b_name="B",
        stoppage_sensitivity=1.0,
        source_matchup_file="test.json",
        simulation_count=1,
    )

@pytest.mark.parametrize(
    "case_name, engine_result, result_dict, expected",
    [
        (
            "normal_full",
            {
                "predicted_winner_id": "fighter_a",
                "confidence": 0.71,
                "method": "decision",
                "round": 3,
                "signal_gap": 0.22,
                "stoppage_propensity": 0.18,
                "round_finish_tendency": 0.31,
                "debug_metrics": {"fallback_triggered": False},
            },
            {},
            {
                "predicted_winner_id": "fighter_a",
                "confidence": 0.71,
                "method": "decision",
                "round": "3",
                "signal_gap": 0.22,
                "stoppage_propensity": 0.18,
                "round_finish_tendency": 0.31,
            },
        ),
        (
            "sparse_with_fallback",
            {
                "predicted_winner_id": "fighter_b",
                "confidence": 0.64,
                "debug_metrics": {
                    "fallback_triggered": True,
                    "signal_gap": 0.11,
                    "stoppage_propensity": 0.44,
                    "round_finish_tendency": 0.57,
                },
            },
            {
                "selected_method": "ko_tko",
                "selected_round": 2,
            },
            {
                "predicted_winner_id": "fighter_b",
                "confidence": 0.64,
                "method": "ko_tko",
                "round": "2",
                "signal_gap": 0.11,
                "stoppage_propensity": 0.44,
                "round_finish_tendency": 0.57,
            },
        ),
        (
            "partial_promoted_fields",
            {
                "predicted_winner_id": "fighter_a",
                "debug_metrics": {},
            },
            {
                "confidence": 0.55,
                "selected_method": "decision",
                "selected_round": 3,
            },
            {
                "predicted_winner_id": "fighter_a",
                "confidence": 0.55,
                "method": "decision",
                "round": "3",
                "signal_gap": None,
                "stoppage_propensity": None,
                "round_finish_tendency": None,
            },
        ),
        (
            "nested_metric_fallback_only",
            {
                "predicted_winner_id": "fighter_b",
                "confidence": 0.62,
                "method": "submission",
                "round": 1,
                "debug_metrics": {
                    "signal_gap": 0.09,
                    "stoppage_propensity": 0.61,
                    "round_finish_tendency": 0.74,
                },
            },
            {},
            {
                "predicted_winner_id": "fighter_b",
                "confidence": 0.62,
                "method": "submission",
                "round": "1",
                "signal_gap": 0.09,
                "stoppage_propensity": 0.61,
                "round_finish_tendency": 0.74,
            },
        ),
    ],
)
def test_build_prediction_record_promoted_field_mapping(
    case_name, engine_result, result_dict, expected
):
    context = minimal_context()
    record = build_prediction_record(
        legacy_prediction={**engine_result, "pipeline_result": result_dict},
        **context
    )
    assert isinstance(record, PredictionRecord)
    payload = record.to_json_dict() if hasattr(record, "to_json_dict") else record.model_dump()
    assert isinstance(payload["round"], str)
    for key, value in expected.items():
        assert payload[key] == value

def test_build_prediction_record_emits_required_promoted_keys():
    context = minimal_context()
    record = build_prediction_record(
        legacy_prediction={
            "predicted_winner_id": "fighter_a",
            "confidence": 0.7,
            "method": "decision",
            "round": 3,
            "signal_gap": 0.2,
            "stoppage_propensity": 0.3,
            "round_finish_tendency": 0.4,
            "debug_metrics": {},
        },
        **context
    )
    payload = record.to_json_dict() if hasattr(record, "to_json_dict") else record.model_dump()
    for key in (
        "predicted_winner_id",
        "confidence",
        "method",
        "round",
        "signal_gap",
        "stoppage_propensity",
        "round_finish_tendency",
    ):
        assert key in payload
