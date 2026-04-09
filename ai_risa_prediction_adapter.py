# --- Adapter mapping: build_prediction_record ---

from datetime import datetime
from ai_risa_prediction_schema import PredictionRecord, WorkflowType, InputConfig, ProfileSources, ProfileHashes

def build_prediction_record(
    legacy_prediction,
    matchup_record,
    workflow_type,
    prediction_timestamp,
    stoppage_sensitivity,
    simulation_count,
    source_matchup_file,
    fighter_a_profile_path,
    fighter_b_profile_path,
    calibration_version,
    fighter_prior_version,
):
    # If already a PredictionRecord, return as-is
    if isinstance(legacy_prediction, PredictionRecord):
        return legacy_prediction
    # If input is a dict, validate and promote
    if not isinstance(legacy_prediction, dict):
        raise TypeError("build_prediction_record expects a dict or PredictionRecord")
    # Normalize calibration_version and fighter_prior_version to sentinel if falsey
    calibration_version = calibration_version or "unknown"
    fighter_prior_version = fighter_prior_version or "unknown"
    # Normalized mapping pass (existing logic)
    engine_result = legacy_prediction
    result_dict = legacy_prediction.get("pipeline_result", {}) if isinstance(legacy_prediction.get("pipeline_result"), dict) else {}
    debug_metrics = engine_result.get("debug_metrics") or {}

    predicted_winner_id = _first_present(
        engine_result.get("predicted_winner_id"),
        result_dict.get("predicted_winner_id"),
    )
    confidence = _first_present(
        engine_result.get("confidence"),
        result_dict.get("confidence"),
    )
    method = _first_present(
        engine_result.get("method"),
        result_dict.get("selected_method"),
        result_dict.get("method"),
    )
    round_value = _first_present(
        engine_result.get("round"),
        result_dict.get("selected_round"),
        result_dict.get("round"),
    )
    signal_gap = _first_present(
        engine_result.get("signal_gap"),
        debug_metrics.get("signal_gap"),
    )
    stoppage_propensity = _first_present(
        engine_result.get("stoppage_propensity"),
        debug_metrics.get("stoppage_propensity"),
    )
    round_finish_tendency = _first_present(
        engine_result.get("round_finish_tendency"),
        debug_metrics.get("round_finish_tendency"),
    )

    matchup_id = legacy_prediction.get("matchup_id")
    if not matchup_id:
        fight_id = matchup_record.get("matchup_id") or matchup_record.get("id")
        fighter_a_id = matchup_record.get("fighter_a_id")
        fighter_b_id = matchup_record.get("fighter_b_id")
        matchup_id = fight_id or f"{fighter_a_id}_vs_{fighter_b_id}"

    model_version = legacy_prediction.get("model_version") or debug_metrics.get("model_version") or "unknown"
    calibration_version = legacy_prediction.get("calibration_version") or debug_metrics.get("calibration_version") or calibration_version
    fighter_prior_version = legacy_prediction.get("fighter_prior_version") or debug_metrics.get("fighter_prior_version") or fighter_prior_version

    prediction_family_id = legacy_prediction.get("prediction_family_id") or matchup_id
    prediction_id = legacy_prediction.get("prediction_id") or f"{prediction_family_id}__s{stoppage_sensitivity}"

    if not fighter_a_profile_path:
        fighter_a_profile_path = "unknown_profile_path"
    if not fighter_b_profile_path:
        fighter_b_profile_path = "unknown_profile_path"

    record = PredictionRecord(
        schema_version="prediction_record_v1",
        prediction_id=prediction_id,
        prediction_family_id=prediction_family_id,
        matchup_id=matchup_id,
        workflow_type=WorkflowType(workflow_type),
        prediction_timestamp=prediction_timestamp,
        fighter_a_id=matchup_record["fighter_a_id"],
        fighter_b_id=matchup_record["fighter_b_id"],
        predicted_winner_id=predicted_winner_id,
        confidence=confidence,
        method=method,
        round=str(round_value) if round_value is not None else None,
        model_version=model_version,
        calibration_version=calibration_version,
        fighter_prior_version=fighter_prior_version,
        input_config=InputConfig(
            stoppage_sensitivity=float(stoppage_sensitivity) if stoppage_sensitivity is not None else 1.0,
            simulation_count=simulation_count,
            source_matchup_file=source_matchup_file,
        ),
        debug_metrics=debug_metrics,
        profile_sources=ProfileSources(
            fighter_a_profile_path=fighter_a_profile_path,
            fighter_b_profile_path=fighter_b_profile_path,
        ),
        profile_hashes=ProfileHashes(
            fighter_a_hash=None,
            fighter_b_hash=None,
        ),
        signal_gap=signal_gap,
        stoppage_propensity=stoppage_propensity,
        round_finish_tendency=round_finish_tendency,
    )
    # Fail fast if required top-level fields are missing
    required_fields = ["signal_gap", "stoppage_propensity", "round_finish_tendency"]
    for field in required_fields:
        if getattr(record, field, None) is None:
            raise ValueError(f"Missing required signal field: {field}")
    if not getattr(record.profile_sources, "fighter_a_profile_path", None):
        raise ValueError("Missing fighter_a_profile_path in profile_sources")
    if not getattr(record.profile_sources, "fighter_b_profile_path", None):
        raise ValueError("Missing fighter_b_profile_path in profile_sources")
    return record
# Promoted field mapping contract
# final field              primary source                        fallback source                        default
# predicted_winner_id      engine_result["predicted_winner_id"]   result_dict["predicted_winner_id"]     None
# confidence               engine_result["confidence"]            result_dict["confidence"]              None
# method                   engine_result["method"]                result_dict["selected_method"]         None
# round                    engine_result["round"]                 result_dict["selected_round"]          None
# signal_gap               engine_result["signal_gap"]            debug_metrics["signal_gap"]            None
# stoppage_propensity      engine_result["stoppage_propensity"]   debug_metrics["stoppage_propensity"]   None
# round_finish_tendency    engine_result["round_finish_tendency"] debug_metrics["round_finish_tendency"] None
# debug_metrics            engine_result["debug_metrics"]         {}                                      {}

def _first_present(*values):
    for value in values:
        if value is not None:
            return value
    return None

def _mapping_trace(enabled, **fields):
    if not enabled:
        return
    print("[build_prediction_record]", fields)
# Move __future__ import to the very top
def compute_prediction_config_hash(
    *,
    model_version: str,
    calibration_version: str,
    fighter_prior_version: str,
    simulation_count: int,
    stoppage_sensitivity: float,
) -> str:
    payload = {
        "model_version": model_version,
        "calibration_version": calibration_version,
        "fighter_prior_version": fighter_prior_version,
        "simulation_count": simulation_count,
        "stoppage_sensitivity": stoppage_sensitivity,
    }
    canonical = _json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
