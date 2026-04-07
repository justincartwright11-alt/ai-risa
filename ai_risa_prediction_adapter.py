from __future__ import annotations

import hashlib
import json as _json
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
ADAPTER_VERSION = "adapter_gate_fix_v2"

import unicodedata
from datetime import datetime
from typing import Any
from ai_risa_prediction_schema import PredictionRecord, WorkflowType, InputConfig, ProfileSources, ProfileHashes
import sys


import re

def _normalize_fighter_ref(value: str | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    s = s.replace("\\", "/").split("/")[-1]
    if s.endswith(".json"):
        s = s[:-5]
    if s.startswith("fighter_"):
        s = s[len("fighter_"):]
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or None

def normalize_winner_id(
    winner_raw: str,
    fighter_a_id: str,
    fighter_b_id: str,
    fighter_a_name: str,
    fighter_b_name: str,
) -> str:
    """Map winner_raw (ID or display name) to canonical fighter ID."""
    pred_raw = winner_raw
    a_raw = fighter_a_id
    b_raw = fighter_b_id

    pred_norm = _normalize_fighter_ref(pred_raw)
    a_norm = _normalize_fighter_ref(a_raw)
    b_norm = _normalize_fighter_ref(b_raw)

    if pred_norm == a_norm:
        return fighter_a_id
    elif pred_norm == b_norm:
        return fighter_b_id
    else:
        raise ValueError(
            f"Could not map predicted_winner_id {pred_raw!r} "
            f"to fighter_a_id/fighter_b_id (a: {fighter_a_id}, b: {fighter_b_id})"
        )


def build_prediction_record(
    legacy_prediction: dict,
    matchup_record: dict,
    workflow_type: str,
    prediction_timestamp: datetime,
    fighter_a_profile_path: str,
    fighter_b_profile_path: str,
    fighter_a_name: str,
    fighter_b_name: str,
    stoppage_sensitivity: float,
    source_matchup_file: str,
    simulation_count: int = 1000,
    calibration_version: str = "calibration_v1.0.0",
    fighter_prior_version: str = "fighter_priors_v1.0.0",
) -> PredictionRecord:
    """Build a canonical PredictionRecord from legacy dict and workflow context."""
    predicted_winner_id = normalize_winner_id(
        legacy_prediction.get("predicted_winner_id"),
        matchup_record["fighter_a_id"],
        matchup_record["fighter_b_id"],
        fighter_a_name,
        fighter_b_name,
    )

    # Patch: Set simulation_count from sim-count lineage
    existing_simulation_count = simulation_count
    simulation_count = (
        legacy_prediction.get("requested_total_sims")
        or legacy_prediction.get("executed_sims")
        or legacy_prediction.get("counted_total")
        or existing_simulation_count
    )

    # Ensure profile paths are valid strings for ProfileSources
    if not fighter_a_profile_path:
        fighter_a_profile_path = "unknown_profile_path"
    if not fighter_b_profile_path:
        fighter_b_profile_path = "unknown_profile_path"
    # --- Winner probability extraction ---
    # Try to extract win shares from legacy_prediction (from simulation summary)

    debug_metrics = dict(legacy_prediction.get("debug_metrics", {}))
    signal_gap = legacy_prediction.get("signal_gap", debug_metrics.get("signal_gap"))
    stoppage_propensity = legacy_prediction.get("stoppage_propensity", debug_metrics.get("stoppage_propensity"))
    round_finish_tendency = legacy_prediction.get("round_finish_tendency", debug_metrics.get("round_finish_tendency"))

    # Reconstruct IDs if not already defined
    matchup_id = legacy_prediction.get("matchup_id")
    if not matchup_id:
        fight_id = matchup_record.get("matchup_id") or matchup_record.get("id")
        fighter_a_id = matchup_record.get("fighter_a_id")
        fighter_b_id = matchup_record.get("fighter_b_id")
        matchup_id = fight_id or f"{fighter_a_id}_vs_{fighter_b_id}"

    # Ensure required metadata variables are set for PredictionRecord
    model_version = legacy_prediction.get("model_version")
    if model_version is None:
        model_version = debug_metrics.get("model_version")
    if model_version is None:
        model_version = "unknown"

    calibration_version = legacy_prediction.get("calibration_version")
    if calibration_version is None:
        calibration_version = debug_metrics.get("calibration_version")
    if calibration_version is None:
        calibration_version = "unknown"

    fighter_prior_version = legacy_prediction.get("fighter_prior_version")
    if fighter_prior_version is None:
        fighter_prior_version = debug_metrics.get("fighter_prior_version")
    if fighter_prior_version is None:
        fighter_prior_version = "unknown"

    prediction_family_id = legacy_prediction.get("prediction_family_id")
    if not prediction_family_id:
        prediction_family_id = matchup_id

    prediction_id = legacy_prediction.get("prediction_id")
    if not prediction_id:
        prediction_id = f"{prediction_family_id}__s{stoppage_sensitivity}"

    # --- Winner probability handoff logic ---
    win_share_a = legacy_prediction.get("win_share_a")
    win_share_b = legacy_prediction.get("win_share_b")

    if win_share_a is None:
        win_share_a = legacy_prediction.get("fighter_a_win_probability")
    if win_share_b is None:
        win_share_b = legacy_prediction.get("fighter_b_win_probability")

    if win_share_a is None and win_share_b is None:
        winner_prob = legacy_prediction.get("winner_prob")
        if winner_prob is None:
            winner_prob = debug_metrics.get("winner_prob", 0.5)
        winner_prob = float(winner_prob)
        win_share_a = winner_prob
        win_share_b = 1.0 - winner_prob
    else:
        win_share_a = float(win_share_a if win_share_a is not None else 1.0 - float(win_share_b))
        win_share_b = float(win_share_b if win_share_b is not None else 1.0 - float(win_share_a))
        winner_prob = max(win_share_a, win_share_b)

    winner_prob_source = legacy_prediction.get("winner_prob_source")
    if not winner_prob_source:
        winner_prob_source = "legacy_prediction"

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
        confidence=winner_prob,
        method=legacy_prediction.get("method"),
        round=legacy_prediction.get("round"),
        model_version=model_version,
        calibration_version=calibration_version,
        fighter_prior_version=fighter_prior_version,
        input_config=InputConfig(
            stoppage_sensitivity=float(stoppage_sensitivity) if stoppage_sensitivity is not None else 1.0,
            simulation_count=simulation_count,
        ),
        debug_metrics=debug_metrics,
        profile_sources=ProfileSources(
            fighter_a_profile_path=fighter_a_profile_path,
            fighter_b_profile_path=fighter_b_profile_path,
        ),
        profile_hashes=ProfileHashes(
            fighter_a_profile_hash=None,
            fighter_b_profile_hash=None,
        ),
        source_matchup_file=source_matchup_file,
        signal_gap=signal_gap,
        stoppage_propensity=stoppage_propensity,
        round_finish_tendency=round_finish_tendency,
    )
    print(f"[TRACE] adapter_return prediction={record!r}", file=sys.stderr)
    return record
    for k in ("fighter_b_win_pct", "B_win_pct", "B_win_share", "B", "win_share_b"):
        if k in legacy_prediction:
            win_share_b = legacy_prediction[k]
            break
    # If values are in percent, convert to [0,1]
    if win_share_a is not None and win_share_a > 1.0:
        win_share_a = win_share_a / 100.0
    if win_share_b is not None and win_share_b > 1.0:
        win_share_b = win_share_b / 100.0

    # Fallback: try win_probabilities dict
    if (win_share_a is None or win_share_b is None) and "win_probabilities" in legacy_prediction:
        win_probs = legacy_prediction["win_probabilities"]
        if isinstance(win_probs, dict):
            # Try both common keys and fallback
            for a_key in ("fighter_a", "A", "a"):
                if a_key in win_probs:
                    win_share_a = win_probs[a_key]
                    break
            for b_key in ("fighter_b", "B", "b"):
                if b_key in win_probs:
                    win_share_b = win_probs[b_key]
                    break

    # Fallback: try raw counts if available
    if (win_share_a is None or win_share_b is None) and all(k in legacy_prediction for k in ("win_count_a", "win_count_b", "total_sims")):
        total = legacy_prediction["total_sims"]
        if total:
            if win_share_a is None:
                win_share_a = legacy_prediction["win_count_a"] / total
            if win_share_b is None:
                win_share_b = legacy_prediction["win_count_b"] / total
    # Map predicted_winner_id to A or B
    winner_prob = None
    winner_prob_source = None
    if win_share_a is not None and win_share_b is not None:
        if predicted_winner_id == matchup_record["fighter_a_id"]:
            winner_prob = win_share_a
            winner_prob_source = "A"
        elif predicted_winner_id == matchup_record["fighter_b_id"]:
            winner_prob = win_share_b
            winner_prob_source = "B"
    # Clamp to [0,1] if present
    preclamp_winner_prob = winner_prob
    if winner_prob is not None:
        winner_prob = max(0.0, min(1.0, float(winner_prob)))
    # --- Collapse risk preservation ---
    debug_metrics = dict(legacy_prediction.get("debug_metrics", {}))
    # Patch: propagate new method/round specificity signals if present
    for key in ["stoppage_propensity", "signal_gap", "round_finish_tendency", "control_differential"]:
        if key in legacy_prediction:
            debug_metrics[key] = legacy_prediction[key]
    # Patch: Add simulation_trace to debug_metrics
    debug_metrics["simulation_trace"] = {
        "requested_total_sims": legacy_prediction.get("requested_total_sims"),
        "executed_sims": legacy_prediction.get("executed_sims"),
        "counted_total": legacy_prediction.get("counted_total"),
    }
    collapse_risk = legacy_prediction.get("confidence")
    if collapse_risk is not None:
        debug_metrics["collapse_risk_confidence"] = collapse_risk
    debug_metrics["adapter_version"] = ADAPTER_VERSION
    # --- Adapter key audit and extraction trace ---
    debug_metrics["adapter_key_audit"] = {
        "legacy_prediction_keys": sorted(list(legacy_prediction.keys())) if isinstance(legacy_prediction, dict) else None,
        # engine_output is not directly available here, but can be added if passed in
        "candidate_keys_present": [k for k in candidate_keys if k in legacy_prediction],
        "raw_A": legacy_prediction.get("A"),
        "raw_B": legacy_prediction.get("B"),
        "raw_fighter_a_win_pct": legacy_prediction.get("fighter_a_win_pct"),
        "raw_fighter_b_win_pct": legacy_prediction.get("fighter_b_win_pct"),
        "predicted_winner_id": predicted_winner_id,
        "fighter_a_id": matchup_record.get("fighter_a_id"),
        "fighter_b_id": matchup_record.get("fighter_b_id"),
        "win_share_a": win_share_a,
        "win_share_b": win_share_b,
        "winner_prob_source": winner_prob_source,
        "preclamp_winner_prob": preclamp_winner_prob,
        "final_confidence": winner_prob,
    }
    # --- Winner probability extraction trace ---
    debug_metrics["winner_probability_trace"] = {
        "selected_confidence_value": winner_prob,
        "selected_confidence_type": str(type(winner_prob).__name__) if winner_prob is not None else "NoneType",
        "winner_probability_source": winner_prob_source,
        "raw_a_value": win_share_a,
        "raw_b_value": win_share_b,
        "selected_side": (
            "A" if winner_prob_source == "A" else ("B" if winner_prob_source == "B" else None)
        ),
    }
    # --- Build record ---
    # Patch: propagate sim counts to canonical artifact
    matchup_id = (
        matchup_record.get("matchup_id")
        or matchup_record.get("id")
    )
    if not matchup_id:
        raise ValueError("matchup_record is missing both 'matchup_id' and fallback 'id'")

    debug_metrics = dict(legacy_prediction.get("debug_metrics", {}) or {})
    signal_gap = legacy_prediction.get("signal_gap", debug_metrics.get("signal_gap"))
    stoppage_propensity = legacy_prediction.get("stoppage_propensity", debug_metrics.get("stoppage_propensity"))
    round_finish_tendency = legacy_prediction.get("round_finish_tendency", debug_metrics.get("round_finish_tendency"))
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
        confidence=winner_prob,
        method=legacy_prediction.get("method"),
        round=legacy_prediction.get("round"),
        model_version=model_version,
        calibration_version=calibration_version,
        fighter_prior_version=fighter_prior_version,
        input_config=InputConfig(
            stoppage_sensitivity=float(stoppage_sensitivity) if stoppage_sensitivity is not None else 1.0,
            simulation_count=simulation_count,
        ),
        debug_metrics=debug_metrics,
        profile_sources=ProfileSources(
            fighter_a_profile_path=fighter_a_profile_path,
            fighter_b_profile_path=fighter_b_profile_path,
        ),
        profile_hashes=ProfileHashes(
            fighter_a_profile_hash=None,
            fighter_b_profile_hash=None,
        ),
        source_matchup_file=source_matchup_file,
        signal_gap=signal_gap,
        stoppage_propensity=stoppage_propensity,
        round_finish_tendency=round_finish_tendency,
    )
    print(f"[TRACE] adapter_return prediction={record!r}", file=sys.stderr)
    return record
