def _prediction_payload(prediction_record) -> dict:
    if hasattr(prediction_record, "to_json_dict"):
        payload = prediction_record.to_json_dict()
    elif hasattr(prediction_record, "model_dump"):
        payload = prediction_record.model_dump(mode="python")
    else:
        payload = dict(prediction_record)
    return _json_safe(payload)
def _peek_conf(src):
    if src is None:
        return None
    if isinstance(src, dict):
        return src.get("confidence")
    if hasattr(src, "model_dump"):
        try:
            return src.model_dump().get("confidence")
        except Exception:
            pass
    if hasattr(src, "dict"):
        try:
            return src.dict().get("confidence")
        except Exception:
            pass
    return getattr(src, "confidence", None)
from datetime import date, datetime

def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    return value

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'ai_risa_data')))
import argparse
import traceback
from ai_risa_models import run_event_card_pipeline
from ai_risa_prediction_adapter import build_prediction_record
import ai_risa_prediction_adapter
from ai_risa_v100_core import execute_risa_v40
import ai_risa_v100_core
from run_ufc_fn_adesanya_pyfer import engine_adapter
from ai_risa_prediction_ledger import append_prediction_record

def main():
    engine_output = {}
    pipeline_result = {}
    output_payload = None
    prediction_record = None
    # Try to get pipeline_result/result_dict_final from engine_output if present
    pipeline_result = engine_output.get("pipeline_result", {}) if isinstance(engine_output, dict) else {}
    result_dict_final = engine_output.get("result_dict_final", {}) if isinstance(engine_output, dict) else {}

    print(
        "[TRACE] confidence_sources "
        f"output_payload={_peek_conf(output_payload)!r} "
        f"prediction_record={_peek_conf(prediction_record)!r} "
        f"pipeline_result={_peek_conf(pipeline_result)!r} "
        f"result_dict_final={_peek_conf(result_dict_final)!r}",
        file=sys.stderr,
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--matchup", required=True)
    parser.add_argument("--sims", type=int, default=1)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sensitivity", type=float, default=1.0)
    args = parser.parse_args()

    # Load matchup file (assume JSON file or known matchup dict)
    import importlib.util
    import pathlib
    matchup_arg = args.matchup
    if pathlib.Path(matchup_arg).is_file():
        with open(matchup_arg, "r", encoding="utf-8") as f:
            raw_matchup_record = json.load(f)
    else:
        # Always look in ai_risa_data/matchups/ for the file
        matchup_path = pathlib.Path(__file__).parent.parent / "ai_risa_data" / "matchups" / f"{matchup_arg}.json"
        if not matchup_path.is_file():
            # Try absolute fallback
            matchup_path = pathlib.Path("C:/Users/jusin/ai_risa_data/matchups") / f"{matchup_arg}.json"
        if matchup_path.is_file():
            with open(matchup_path, "r", encoding="utf-8") as f:
                raw_matchup_record = json.load(f)
        else:
            raise FileNotFoundError(f"Could not find matchup file for {matchup_arg} (tried {matchup_path})")

    fight = raw_matchup_record
    model_state = {"stoppage_sensitivity": args.sensitivity}

    # Load and inject fighter profiles
    from run_ufc_fn_adesanya_pyfer import load_fighter_profile, ID_TO_NAME
    fighter_a_id = fight["fighter_a_id"]
    fighter_b_id = fight["fighter_b_id"]
    fighter_a_name = ID_TO_NAME.get(fighter_a_id, fighter_a_id)
    fighter_b_name = ID_TO_NAME.get(fighter_b_id, fighter_b_id)
    fighter_a_profile = load_fighter_profile(fighter_a_name)
    fighter_b_profile = load_fighter_profile(fighter_b_name)
    fight["fighter_a_profile"] = fighter_a_profile
    fight["fighter_b_profile"] = fighter_b_profile

    import os
    def _resolve_profile_path(path_value, fighter_id, fighters_dir):
        if isinstance(path_value, str) and path_value.strip():
            return path_value
        if isinstance(fighter_id, str) and fighter_id.strip():
            candidate = os.path.join(fighters_dir, f"{fighter_id}.json")
            if os.path.exists(candidate):
                return candidate
        raise FileNotFoundError(
            f"Missing fighter profile path for fighter_id={fighter_id!r}. "
            f"Checked explicit path={path_value!r} and derived path in {fighters_dir!r}."
        )

    fighters_dir = r"C:\Users\jusin\ai_risa_data\fighters"
    fighter_a_profile_path = _resolve_profile_path(
        fighter_a_profile.get("profile_path") if isinstance(fighter_a_profile, dict) else None,
        fighter_a_id,
        fighters_dir,
    )
    fighter_b_profile_path = _resolve_profile_path(
        fighter_b_profile.get("profile_path") if isinstance(fighter_b_profile, dict) else None,
        fighter_b_id,
        fighters_dir,
    )
    assert isinstance(fighter_a_profile_path, str) and fighter_a_profile_path.strip(), "fighter_a_profile_path must be a non-empty string"
    assert isinstance(fighter_b_profile_path, str) and fighter_b_profile_path.strip(), "fighter_b_profile_path must be a non-empty string"


    engine_output = engine_adapter(
        fight,
        requested_total_sims=args.sims,
        confidence_scale=args.sensitivity,
    )

    print(
        f"[TRACE] adapter_confidence={engine_output.get('confidence')!r} "
        f"winner={engine_output.get('predicted_winner_id')!r} "
        f"method={engine_output.get('method')!r} "
        f"round={engine_output.get('round')!r}",
        file=sys.stderr,
    )

    from datetime import datetime, timezone
    prediction_timestamp = datetime.now(timezone.utc)

    matchup_record = fight
    fighter_a_profile_path = fighter_a_profile.get("profile_path") if isinstance(fighter_a_profile, dict) else None
    fighter_b_profile_path = fighter_b_profile.get("profile_path") if isinstance(fighter_b_profile, dict) else None
    source_matchup_file = (
        getattr(args, "matchup_file", None)
        or getattr(args, "matchup", None)
        or "single_fight_cli"
    )
    stoppage_sensitivity = getattr(args, "sensitivity", 1.0)



    prediction_record = build_prediction_record(
        legacy_prediction=engine_output,
        matchup_record=matchup_record,
        workflow_type="single_fight",
        prediction_timestamp=prediction_timestamp,
        fighter_a_profile_path=fighter_a_profile_path,
        fighter_b_profile_path=fighter_b_profile_path,
        stoppage_sensitivity=stoppage_sensitivity,
        simulation_count=args.sims,
        source_matchup_file=source_matchup_file,
        calibration_version="unknown",
        fighter_prior_version="unknown",
    )

    # Write only PredictionRecord, never dict
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(prediction_record.to_json_dict(), f, ensure_ascii=False, indent=2)
    print(f"[INFO] Wrote prediction to {args.output}")

    # Append to prediction ledger (live capture)
    try:
        append_prediction_record(prediction_record, r'C:\Users\jusin\ai_risa_data\ledger\prediction_ledger.jsonl')
        print(f"[INFO] Appended prediction to prediction_ledger.jsonl")
    except Exception as e:
        print(f"[WARNING] Prediction ledger append failed: {e}")

    return prediction_record

if __name__ == "__main__":
    main()

