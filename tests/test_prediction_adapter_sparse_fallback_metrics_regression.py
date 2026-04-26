from datetime import datetime

from ai_risa_prediction_adapter import build_prediction_record


def _context():
    return {
        "matchup_record": {
            "fighter_a_id": "fighter_a",
            "fighter_b_id": "fighter_b",
            "matchup_id": "test_matchup",
        },
        "workflow_type": "single_fight",
        "prediction_timestamp": datetime(2026, 4, 7, 0, 0, 0),
        "fighter_a_profile_path": "a.json",
        "fighter_b_profile_path": "b.json",
        "stoppage_sensitivity": 1.0,
        "source_matchup_file": "test.json",
        "simulation_count": 1,
        "calibration_version": "unknown",
        "fighter_prior_version": "unknown",
    }


def test_sparse_fallback_debug_metrics_contract():
    record = build_prediction_record(
        legacy_prediction={"debug_metrics": {}},
        **_context(),
    )
    payload = record.to_json_dict() if hasattr(record, "to_json_dict") else record.model_dump()

    assert payload["debug_metrics"]["completion_mode"] == "sparse_fallback"
    assert payload["debug_metrics"]["winner_source"] == "fallback_matchup_fighter_a_id"
    assert payload["debug_metrics"]["fallback_fields"] == [
        "predicted_winner_id",
        "confidence",
        "method",
        "round",
        "signal_gap",
        "stoppage_propensity",
        "round_finish_tendency",
    ]


def test_pass_through_debug_metrics_contract():
    record = build_prediction_record(
        legacy_prediction={
            "predicted_winner_id": "fighter_b",
            "confidence": 0.74,
            "method": "decision",
            "round": 3,
            "signal_gap": 0.15,
            "stoppage_propensity": 0.22,
            "round_finish_tendency": 0.41,
            "debug_metrics": {},
        },
        **_context(),
    )
    payload = record.to_json_dict() if hasattr(record, "to_json_dict") else record.model_dump()

    assert payload["debug_metrics"]["completion_mode"] == "pass_through"
    assert payload["debug_metrics"]["fallback_fields"] == []
