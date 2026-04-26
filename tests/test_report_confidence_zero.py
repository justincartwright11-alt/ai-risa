from ai_risa_report_output_adapter import map_engine_output_to_report


def _base_payload():
    return {
        "predicted_winner_id": "fighter_a",
        "confidence": 0.65,
        "method": "decision",
        "round": 3,
        "event_date": "2026-04-26",
        "promotion": "UFC",
        "sport": "MMA",
        "fight_id": "fighter_a_vs_fighter_b",
        "fighter_a_id": "fighter_a",
        "fighter_b_id": "fighter_b",
        "fighter_a_profile": {"name": "Fighter A"},
        "fighter_b_profile": {"name": "Fighter B"},
        "debug_metrics": {},
    }


def test_confidence_zero_is_valid():
    payload = _base_payload()
    payload["confidence"] = 0.0
    report = map_engine_output_to_report(payload)
    assert report is not None
    assert report["headline"]["confidence"] == 0.0
