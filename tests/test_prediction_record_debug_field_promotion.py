
from datetime import datetime, timezone
from ai_risa_prediction_adapter import build_prediction_record
from ai_risa_prediction_schema import PredictionRecord

def _base_matchup_record():
    return {
        "matchup_id": "fighter_israel_adesanya_vs_fighter_joe_pyfer",
        "fighter_a_id": "fighter_israel_adesanya",
        "fighter_b_id": "fighter_joe_pyfer",
    }

def test_build_prediction_record_promotes_debug_fields_with_fallback():
    legacy_prediction = {
        "predicted_winner_id": "fighter_joe_pyfer",
        "confidence": 0.5,
        "method": "Decision",
        "round": "full",
        "debug_metrics": {
            "signal_gap": 0.01740799999999998,
            "stoppage_propensity": 0.0,
            "round_finish_tendency": 0.0,
        },
    }

    record = build_prediction_record(
        legacy_prediction=legacy_prediction,
        matchup_record=_base_matchup_record(),
        workflow_type="single_fight",
        prediction_timestamp=datetime.now(timezone.utc),
        fighter_a_profile_path="C:/Users/jusin/ai_risa_data/fighters/fighter_israel_adesanya.json",
        fighter_b_profile_path="C:/Users/jusin/ai_risa_data/fighters/fighter_joe_pyfer.json",
        fighter_a_name="Israel Adesanya",
        fighter_b_name="Joe Pyfer",
        stoppage_sensitivity=1.0,
        source_matchup_file="single_fight_cli",
        simulation_count=1,
    )

    assert isinstance(record, PredictionRecord)
    assert record.signal_gap == 0.01740799999999998
    assert record.stoppage_propensity == 0.0
    assert record.round_finish_tendency == 0.0

def test_build_prediction_record_prefers_top_level_values_when_present():
    legacy_prediction = {
        "predicted_winner_id": "fighter_joe_pyfer",
        "confidence": 0.5,
        "method": "Decision",
        "round": "full",
        "signal_gap": 0.22,
        "stoppage_propensity": 0.11,
        "round_finish_tendency": 0.09,
        "debug_metrics": {
            "signal_gap": 0.01,
            "stoppage_propensity": 0.02,
            "round_finish_tendency": 0.03,
        },
    }

    record = build_prediction_record(
        legacy_prediction=legacy_prediction,
        matchup_record=_base_matchup_record(),
        workflow_type="single_fight",
        prediction_timestamp=datetime.now(timezone.utc),
        fighter_a_profile_path="C:/Users/jusin/ai_risa_data/fighters/fighter_israel_adesanya.json",
        fighter_b_profile_path="C:/Users/jusin/ai_risa_data/fighters/fighter_joe_pyfer.json",
        fighter_a_name="Israel Adesanya",
        fighter_b_name="Joe Pyfer",
        stoppage_sensitivity=1.0,
        source_matchup_file="single_fight_cli",
        simulation_count=1,
    )

    assert isinstance(record, PredictionRecord)
    assert record.signal_gap == 0.22
    assert record.stoppage_propensity == 0.11
    assert record.round_finish_tendency == 0.09
