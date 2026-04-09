import pytest
from ai_risa_prediction_adapter import build_prediction_record
from ai_risa_prediction_schema import PredictionRecord
from datetime import datetime, timezone

def minimal_matchup_record():
    return {
        "matchup_id": "test_matchup",
        "fighter_a_id": "fighter_a",
        "fighter_b_id": "fighter_b",
    }

def minimal_context(calibration_version=None, fighter_prior_version=None):
    return dict(
        matchup_record=minimal_matchup_record(),
        workflow_type="single_fight",
        prediction_timestamp=datetime.now(timezone.utc),
        fighter_a_profile_path="a.json",
        fighter_b_profile_path="b.json",
        stoppage_sensitivity=1.0,
        source_matchup_file="test.json",
        simulation_count=1,
        calibration_version=calibration_version,
        fighter_prior_version=fighter_prior_version,
    )

def test_build_prediction_record_rejects_unsupported_kwargs():
    legacy_prediction = {"predicted_winner_id": "fighter_a"}
    context = minimal_context(calibration_version="unknown", fighter_prior_version="unknown")
    # Add an unsupported kwarg
    context["unsupported_field"] = "should_fail"
    with pytest.raises(TypeError):
        build_prediction_record(legacy_prediction=legacy_prediction, **context)

def test_build_prediction_record_normalizes_version_strings():
    legacy_prediction = {
        "predicted_winner_id": "fighter_a",
        "confidence": 0.7,
        "method": "decision",
        "round": "3",
        "signal_gap": 0.2,
        "stoppage_propensity": 0.3,
        "round_finish_tendency": 0.4,
        "debug_metrics": {},
    }
    # Pass falsey values for version fields
    context = minimal_context(calibration_version=None, fighter_prior_version=None)
    record = build_prediction_record(legacy_prediction=legacy_prediction, **context)
    assert isinstance(record, PredictionRecord)
    assert isinstance(record.calibration_version, str)
    assert isinstance(record.fighter_prior_version, str)
    assert record.calibration_version == "unknown"
    assert record.fighter_prior_version == "unknown"

def test_sparse_case_outputs_have_required_signal_fields():
    # Simulate a sparse-case output
    legacy_prediction = {
        "predicted_winner_id": "fighter_a",
        "confidence": 0.7,
        "method": "decision",
        "round": 3,
        "signal_gap": 0.2,
        "stoppage_propensity": 0.3,
        "round_finish_tendency": 0.4,
        "debug_metrics": {},
    }
    context = minimal_context(calibration_version="unknown", fighter_prior_version="unknown")
    record = build_prediction_record(legacy_prediction=legacy_prediction, **context)
    payload = record.to_json_dict() if hasattr(record, "to_json_dict") else record.model_dump()
    for key in ("signal_gap", "stoppage_propensity", "round_finish_tendency"):
        assert key in payload
        assert payload[key] is not None
