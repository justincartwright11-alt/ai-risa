import json

from check_prediction_contract import check_files, validate_prediction_record


def _valid_record():
    return {
        "predicted_winner_id": "fighter_a",
        "confidence": 0.66,
        "method": "decision",
        "round": "3",
        "debug_metrics": {},
        "signal_gap": 0.2,
        "stoppage_propensity": 0.3,
        "round_finish_tendency": 0.4,
        "key_tactical_edges": ["edge"],
        "risk_factors": ["risk"],
        "confidence_explanation": "explanation",
        "what_could_flip_the_fight": ["flip"],
    }


def test_validate_prediction_record_passes_for_canonical_12_field_shape():
    errors = validate_prediction_record(_valid_record())
    assert errors == []


def test_validate_prediction_record_fails_when_canonical_field_missing_even_with_legacy_aliases():
    record = _valid_record()
    record.pop("key_tactical_edges")
    record["tactical_edges"] = ["legacy edge"]
    record.pop("what_could_flip_the_fight")
    record["what_could_flip"] = ["legacy flip"]

    errors = validate_prediction_record(record)
    assert "missing field: key_tactical_edges" in errors
    assert "missing field: what_could_flip_the_fight" in errors


def test_validate_prediction_record_fails_on_null_fields():
    record = _valid_record()
    record["signal_gap"] = None

    errors = validate_prediction_record(record)
    assert "null field: signal_gap" in errors


def test_validate_prediction_record_enforces_narrative_types():
    record = _valid_record()
    record["key_tactical_edges"] = "edge"
    record["risk_factors"] = "risk"
    record["confidence_explanation"] = ["wrong"]
    record["what_could_flip_the_fight"] = "flip"

    errors = validate_prediction_record(record)
    assert "type mismatch: key_tactical_edges must be list" in errors
    assert "type mismatch: risk_factors must be list" in errors
    assert "type mismatch: confidence_explanation must be str" in errors
    assert "type mismatch: what_could_flip_the_fight must be list" in errors


def test_check_files_reports_field_failures(tmp_path):
    invalid_path = tmp_path / "invalid.json"
    record = _valid_record()
    record.pop("risk_factors")
    invalid_path.write_text(json.dumps(record), encoding="utf-8")

    failures = check_files([str(invalid_path)])
    assert len(failures) == 1
    assert failures[0][0] == str(invalid_path)
    assert "missing field: risk_factors" in failures[0][1]