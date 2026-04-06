import sys

def _trace_record(label: str, payload=None) -> None:
    try:
        if payload is None:
            print(f"[TRACE] {label}", file=sys.stderr)
        else:
            print(f"[TRACE] {label}={payload!r}", file=sys.stderr)
    except Exception:
        pass

import sys
from dataclasses import asdict, is_dataclass

# Minimal helper for ingest_matchup serialization
def _to_dict(obj):
    return obj if isinstance(obj, dict) else obj.__dict__


    print(f"[TRACE] {label} {snapshot}", file=sys.stderr)
    sys.stderr.flush()
from dataclasses import dataclass

@dataclass
class Fighter:
    id: str
    name: str

@dataclass
class Matchup:
    id: str
    fighter_a_id: str
    fighter_b_id: str
    event: Optional[str] = None
    date: Optional[str] = None
    weight_class: Optional[str] = None
    rounds: Optional[int] = None
    notes: Optional[str] = None

# Deterministic project root for all artifact writes
import os
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# --- Diagnostic: Calibration Persistence Self-Test ---
def debug_calibration_persistence() -> dict:
    import os
    report = {
        "cwd": os.getcwd(),
        "module_file": __file__,
        "base_data_dir": _base_data_dir(),
        "calibration_dir": _calibration_dir(),
        "calibration_reports_dir": _calibration_reports_dir(),
        "update_history_dir": _update_history_dir(),
        "model_state_path": _model_state_path(),
        "exists": {},
        "writable": {},
        "test_writes": {},
    }

    paths = {
        "base_data_dir": report["base_data_dir"],
        "calibration_dir": report["calibration_dir"],
        "calibration_reports_dir": report["calibration_reports_dir"],
        "update_history_dir": report["update_history_dir"],
    }

    for name, path in paths.items():
        report["exists"][name] = os.path.exists(path)
        report["writable"][name] = os.access(path, os.W_OK) if os.path.exists(path) else False

    try:
        os.makedirs(report["calibration_reports_dir"], exist_ok=True)
        os.makedirs(report["update_history_dir"], exist_ok=True)

        test_report_path = os.path.join(report["calibration_reports_dir"], "_debug_test_report.json")
        test_update_path = os.path.join(report["update_history_dir"], "_debug_test_update.json")
        test_state_path = report["model_state_path"]

        _atomic_write_json(test_report_path, {"ok": True, "type": "report"})
        _atomic_write_json(test_update_path, {"ok": True, "type": "update"})
        _atomic_write_json(test_state_path, {"version": "debug", "ok": True})

        report["test_writes"]["report"] = test_report_path
        report["test_writes"]["update"] = test_update_path
        report["test_writes"]["state"] = test_state_path
        report["status"] = "ok"
    except Exception as exc:
        report["status"] = "error"
        report["error_type"] = exc.__class__.__name__
        report["error_message"] = str(exc)

    return report
# === Unified Calibration Path Helpers ===
def _base_data_dir() -> str:
    return os.path.join(ROOT_DIR, "ai_risa_data")

def _calibration_dir() -> str:
    path = os.path.join(_base_data_dir(), "calibration")
    os.makedirs(path, exist_ok=True)
    return path

def _calibration_reports_dir() -> str:
    path = os.path.join(_calibration_dir(), "calibration_reports")
    os.makedirs(path, exist_ok=True)
    return path

def _update_history_dir() -> str:
    path = os.path.join(_calibration_dir(), "update_history")
    os.makedirs(path, exist_ok=True)
    return path

def _model_state_path() -> str:
    return os.path.join(_calibration_dir(), "model_state_v1_1.json")
# === AI-RISA v1.1 Operational Learning Patch ===
# --- A. File helpers ---
import shutil
from datetime import datetime

def _results_dir():
    return os.path.join(DATA_ROOT, FOLDERS["results"])

def _calibration_dir():
    d = os.path.join(DATA_ROOT, "calibration")
    os.makedirs(d, exist_ok=True)
    return d

def _model_state_path():
    return os.path.join(_calibration_dir(), "model_state_v1_1.json")

def _read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _atomic_write_json(path: str, payload: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, default=str, indent=2)
    shutil.move(tmp, path)

def _bounded_adjust(current: float, delta: float, min_value: float, max_value: float) -> float:
    return max(min(current + delta, max_value), min_value)

def utc_now_iso():
    return datetime.utcnow().isoformat()

# --- B. Result ingestion ---
def ingest_actual_result(result_payload: dict) -> str:
    normalized = {
        "id": result_payload.get("id") or f"result_{result_payload['matchup_id']}",
        "matchup_id": result_payload["matchup_id"],
        "event_id": result_payload.get("event_id"),
        "actual_winner_id": result_payload["actual_winner_id"],
        "method": result_payload.get("method"),
        "round": result_payload.get("round"),
        "scorecards": result_payload.get("scorecards", []),
        "source": result_payload.get("source", "official"),
        "notes": result_payload.get("notes"),
        "created_at": result_payload.get("created_at") or utc_now_iso(),
    }
    path = os.path.join(_results_dir(), f"{normalized['id']}.json")
    _atomic_write_json(path, normalized)
    return path

# --- C. Calibration engine ---
def calibrate_prediction_error(prediction_id: str, result_id: str) -> dict:
    # Load prediction and result
    pred_path = os.path.join(DATA_ROOT, FOLDERS["predictions"], f"{prediction_id}.json")
    res_path = os.path.join(_results_dir(), f"{result_id}.json")
    prediction = _read_json(pred_path)
    result = _read_json(res_path)
    # Winner
    winner_correct = (prediction["predicted_winner_id"] == result["actual_winner_id"])
    # Method (bucketed: KO/TKO, decision, submission)
    def method_bucket(m):
        if not m: return "unknown"
        m = m.lower()
        if any(x in m for x in ["ko", "tko"]): return "ko"
        if "decision" in m: return "decision"
        if "sub" in m: return "submission"
        return m
    method_correct = (method_bucket(prediction.get("method")) == method_bucket(result.get("method")))
    # Round error
    round_error = None
    if prediction.get("round") and result.get("round"):
        try:
            round_error = abs(int(prediction["round"]) - int(result["round"]))
        except Exception:
            round_error = None
    # Confidence error
    confidence = prediction.get("confidence", 0)
    confidence_error = (100 - confidence) if winner_correct else (0 - confidence)
    # Component errors (heuristic, placeholder)
    component_errors = {
        "decision_structure": 0.0 if winner_correct else 0.25,
        "energy_use": 0.0,
        "fatigue_failure_points": 0.0,
        "mental_condition": 0.0,
        "collapse_triggers": 0.0 if method_correct else 0.25,
    }
    # Recommended updates (bounded, placeholder logic)
    recommended_updates = {
        "confidence_scale": -0.03 if not winner_correct else 0.0,
        "stoppage_sensitivity": -0.04 if not method_correct else 0.0,
        "late_fatigue_bias": 0.05 if round_error and round_error > 2 else 0.0,
        "judge_decision_bias": 0.02 if not winner_correct and method_bucket(result.get("method")) == "decision" else 0.0,
    }
    cal_id = f"cal_{prediction_id}"
    report = {
        "id": cal_id,
        "prediction_id": prediction_id,
        "result_id": result_id,
        "matchup_id": prediction["matchup_id"],
        "winner_correct": winner_correct,
        "method_correct": method_correct,
        "round_error": round_error,
        "confidence_error": confidence_error,
        "component_errors": component_errors,
        "recommended_updates": recommended_updates,
        "created_at": utc_now_iso(),
    }
    # Write calibration report to unified path
    cal_path = os.path.join(_calibration_reports_dir(), f"{cal_id}.json")
    _atomic_write_json(cal_path, report)
    return report

# --- D. Bounded model-state update ---
def load_model_state() -> dict:
    path = _model_state_path()
    if not os.path.exists(path):
        state = {
            "version": "model_state_v1_1",
            "updated_at": utc_now_iso(),
            "confidence_scale": 1.0,
            "stoppage_sensitivity": 1.0,
            "late_fatigue_bias": 1.0,
            "judge_decision_bias": 1.0,
            "style_interaction_adjustments": {},
            "notes": "bounded operational calibration state"
        }
        _atomic_write_json(path, state)
        return state
    return _read_json(path)

def apply_model_updates(calibration_report: dict) -> dict:
    state = load_model_state()
    MAX_STEP = 0.05
    MIN_FACTOR = 0.75
    MAX_FACTOR = 1.25
    updates = calibration_report.get("recommended_updates", {})
    changed = False
    applied_updates = {}
    for k in ["confidence_scale", "stoppage_sensitivity", "late_fatigue_bias", "judge_decision_bias"]:
        if k in updates:
            delta = max(min(updates[k], MAX_STEP), -MAX_STEP)
            old = state.get(k, 1.0)
            new = _bounded_adjust(old, delta, MIN_FACTOR, MAX_FACTOR)
            if new != old:
                state[k] = new
                applied_updates[k] = delta
                changed = True
    state["updated_at"] = utc_now_iso()
    # Always write model state
    _atomic_write_json(_model_state_path(), state)
    # Always write update history
    update_id = f"update_{state['updated_at'].replace(':','-').replace('.','_')}"
    update_payload = {
        "id": update_id,
        "source_calibration_id": calibration_report["id"],
        "applied_updates": applied_updates,
        "previous_state_version": state.get("version", "model_state_v1_1"),
        "updated_at": state["updated_at"]
    }
    update_path = os.path.join(_update_history_dir(), f"{update_id}.json")
    _atomic_write_json(update_path, update_payload)
    state["applied_updates"] = applied_updates
    return state
import tempfile
def write_prediction_record(prediction_payload: dict) -> str:
    # Deterministically return the prediction record (no file write)
    print("[TRACE] write_prediction_record:DEPRECATED - no file write performed", file=sys.stderr)
    return prediction_payload
# --- Phase 6: Batch Automation ---

def run_event_card_pipeline(event_id: str, fight_list: list, mode_set: list, engine, model_version_obj=None, export_pdf_fn=None, summary_manifest_path=None, model_state=None) -> dict:
    """
    For each fight in fight_list, run the full pipeline for all requested modes.
    engine: callable(matchup) -> engine_output
    export_pdf_fn: optional callable(matchup_id, report_payload, mode, output_path) for PDF export
    summary_manifest_path: optional path to write event-level JSON/markdown summary
    Returns batch summary, per-fight outputs, failures, and release readiness.
    """
    import sys
    print("[MARKER] RUN_EVENT_CARD_PIPELINE_LIVE", file=sys.stderr); sys.stderr.flush()
    print(f"[TRACE] pipeline:entered fight_count={len(fight_list)} matchup_ids={[f.get('matchup_id') for f in fight_list]}", file=sys.stderr); sys.stderr.flush()
    print(f"[TRACE] pipeline:fight_list_len={len(fight_list)}", file=sys.stderr); sys.stderr.flush()
    print("[TRACE] pipeline:before_loop", file=sys.stderr); sys.stderr.flush()
    batch_summary = {"event_id": event_id, "fights": [], "failures": [], "warnings": [], "release_ready": True, "artifacts": []}
    fight_results = {}


    from ai_risa_models import load_model_state
    if model_state is None:
        model_state = load_model_state()
    print(
        f"[TRACE] pipeline:effective_model_state stoppage_sensitivity={model_state.get('stoppage_sensitivity', 1.0)}",
        file=sys.stderr,
    )
    sys.stderr.flush()
    confidence_scale = model_state.get("confidence_scale", 1.0)
    stoppage_sensitivity = model_state.get("stoppage_sensitivity", 1.0)
    requested_total_sims = model_state.get("requested_total_sims", model_state.get("total_sims", 10000))
    print(f"[SIM_TRACE] models received requested_total_sims={requested_total_sims}", flush=True)
    import sys
    print(f"[TRACE] model_state stoppage_sensitivity={stoppage_sensitivity}", file=sys.stderr)
    sys.stderr.flush()
    late_fatigue_bias = model_state.get("late_fatigue_bias", 1.0)
    judge_decision_bias = model_state.get("judge_decision_bias", 1.0)

    print(f"[TRACE] fight_list_ids={[f.get('matchup_id') for f in fight_list]}", file=sys.stderr)
    sys.stderr.flush()
    requested_matchup_id = None
    if fight_list:
        requested_matchup_id = fight_list[0].get('matchup_id')
    for fight in fight_list:
        matchup_id = fight.get("matchup_id") or f"{fight.get('fighter_a_id')}_vs_{fight.get('fighter_b_id')}"
        print(f"[TRACE] loop_matchup_id={matchup_id}", file=sys.stderr)
        print(f"[TRACE] requested_matchup_id={requested_matchup_id}", file=sys.stderr)
        sys.stderr.flush()
        fighter_a_id = fight["fighter_a_id"]
        fighter_b_id = fight["fighter_b_id"]
        matchup_id = fight.get("matchup_id") or f"{fighter_a_id}_vs_{fighter_b_id}"
        fight_results[matchup_id] = {
            "matchup_id": matchup_id,
            "reports": {},
            "pdfs": {},
            "warnings": [],
            "failures": []
        }
        skip_reason = None
        if skip_reason:
            print(f"[TRACE] engine_skip matchup_id={matchup_id} reason={skip_reason}", file=sys.stderr)
        try:
            print(f"[TRACE] pipeline:engine_call:start matchup_id={matchup_id}", file=sys.stderr); sys.stderr.flush()
            matchup = Matchup(
                id=matchup_id,
                fighter_a_id=fighter_a_id,
                fighter_b_id=fighter_b_id,
                event=event_id,
                date=fight.get("date"),
                weight_class=fight.get("weight_class"),
                rounds=fight.get("rounds"),
                notes=fight.get("notes")
            )
            fighters = [
                Fighter(id=fighter_a_id, name=fight.get("fighter_a_name", fighter_a_id.replace('_', ' ').title())),
                Fighter(id=fighter_b_id, name=fight.get("fighter_b_name", fighter_b_id.replace('_', ' ').title())),
            ]
            ingest_matchup(matchup, fighters)
            engine_input = {
                "matchup_id": matchup_id,
                "fighter_a_id": fighter_a_id,
                "fighter_b_id": fighter_b_id,
                "event_id": event_id,
                "date": fight.get("date"),
                "weight_class": fight.get("weight_class"),
                "rounds": fight.get("rounds"),
                "notes": fight.get("notes"),
                "fighter_a_profile": fight.get("fighter_a_profile"),
                "fighter_b_profile": fight.get("fighter_b_profile"),
            }
            print(f"[TRACE] engine_call_kwargs stoppage_sensitivity={stoppage_sensitivity}", file=sys.stderr)
            sys.stderr.flush()
            print(f"[TRACE] engine_callable_module={engine.__module__}", file=sys.stderr)
            print(f"[TRACE] engine_callable_file={engine.__code__.co_filename}", file=sys.stderr)
            print(f"[TRACE] engine_callable_name={engine.__name__}", file=sys.stderr)
            print(f"[TRACE] engine_call_input matchup_id={matchup_id} fighterA_name={fight.get('fighter_a_name')} fighterB_name={fight.get('fighter_b_name')} a_profile_loaded={fight.get('fighter_a_profile') is not None} b_profile_loaded={fight.get('fighter_b_profile') is not None}", file=sys.stderr)
            sys.stderr.flush()
            print(f"[SIM_TRACE] models->v40 requested_total_sims={requested_total_sims}", flush=True)
            engine_output = engine(
                engine_input,
                confidence_scale=confidence_scale,
                stoppage_sensitivity=stoppage_sensitivity,
                late_fatigue_bias=late_fatigue_bias,
                judge_decision_bias=judge_decision_bias,
                requested_total_sims=requested_total_sims,
            )
            print(f"[TRACE] pipeline:engine_result={engine_output!r}", file=sys.stderr)
            sys.stderr.flush()
            if matchup_id == "fighter_ricky_simon_vs_fighter_adrian_yanez":
                print(f"[TRACE] sparse_case_engine_output={engine_output!r}", file=sys.stderr)
                sys.stderr.flush()
                print(f"[TRACE] sparse_case_engine_fields winner={engine_output.get('predicted_winner_id') if isinstance(engine_output, dict) else getattr(engine_output, 'predicted_winner_id', None)} method={engine_output.get('method') if isinstance(engine_output, dict) else getattr(engine_output, 'method', None)} round={engine_output.get('round') if isinstance(engine_output, dict) else getattr(engine_output, 'round', None)} debug_metrics={engine_output.get('debug_metrics') if isinstance(engine_output, dict) else getattr(engine_output, 'debug_metrics', None)}", file=sys.stderr)
                sys.stderr.flush()
            print("[MARKER] DICT_ONLY_PIPELINE_PATH", file=sys.stderr)
            sys.stderr.flush()
            prediction_record = generate_prediction_from_engine(matchup_id, engine_output, fighter_a_id=fighter_a_id, fighter_b_id=fighter_b_id, event_id=event_id)
            print(f"[TRACE] pipeline:prediction_record={prediction_record!r}", file=sys.stderr)
            sys.stderr.flush()
            if not isinstance(prediction_record, dict):
                raise TypeError(f"generate_prediction_from_engine must return dict, got {type(prediction_record).__name__}")
            print(f"[TRACE] pre_validation_predicted_winner_id={prediction_record.get('predicted_winner_id') if isinstance(prediction_record, dict) else 'non-dict'}", file=sys.stderr)
            sys.stderr.flush()
            required = ["matchup_id", "fighter_a_id", "fighter_b_id", "predicted_winner_id"]
            for field in required:
                if not prediction_record.get(field):
                    raise ValueError(f"Prediction record missing required field: {field} for {matchup_id}")
            # If only one fight, write and return the record directly with trace
            if len(fight_list) == 1:
                print(f"[TRACE] pipeline:pre_return prediction_record={prediction_record}", file=sys.stderr)
                print(f"[TRACE] pipeline:returning_single={prediction_record}", file=sys.stderr)
                sys.stderr.flush()
                return prediction_record
            else:
                print(f"[TRACE] pipeline:returning_batch={fight_results!r}", file=sys.stderr)
                sys.stderr.flush()
                fight_results[matchup_id]["prediction_record"] = prediction_record
            for mode in mode_set:
                prediction_payload = {
                    # Use generate_prediction_from_engine to build the payload and propagate required fields
                    **generate_prediction_from_engine(
                        matchup_id,
                        engine_output,
                        fighter_a_id=fighter_a_id,
                        fighter_b_id=fighter_b_id,
                        event_id=event_id
                    )
                }
                from ai_risa_models import _trace_record
                _trace_record("generate_prediction_from_engine_payload", prediction_payload)
                print(f"[TRACE] gen_pred:engine_result={engine_output!r}", file=sys.stderr)
                print(f"[TRACE] gen_pred:prediction_payload={prediction_payload!r}", file=sys.stderr)
                sys.stderr.flush()
                # Return normalized prediction payload only, no file write
                return prediction_payload
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            pdf_path = export_pdf_fn(matchup_id, mode, output_path)
            fight_results[matchup_id]["pdfs"][mode] = pdf_path
            batch_summary["artifacts"].append(pdf_path)
            artifact_paths = prediction_record.get("artifact_paths")
            if not isinstance(artifact_paths, list):
                artifact_paths = []
            artifact_paths.append(pdf_path)
            prediction_record["artifact_paths"] = artifact_paths
            # No internal write here
        except Exception as e:
            fight_results[matchup_id]["warnings"].append(f"PDF export failed for {matchup_id}: {e}")
            if model_version_obj:
                save_model_version(model_version_obj)
        except Exception as e:
            import traceback
            print(f"[TRACE] pipeline:exception={e!r}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            sys.stderr.flush()
            fight_results[matchup_id]["failures"].append(str(e))
            batch_summary["failures"].append({"matchup_id": matchup_id, "error": str(e)})
            batch_summary["release_ready"] = False
    batch_summary["fights"] = list(fight_results.values())
    # No internal write for summary_manifest_path
    globals().get("_trace_record", lambda *args, **kwargs: None)(
        "pipeline_return_record",
        batch_summary,
    )
    return batch_summary

def export_matchup_bundle(matchup_id: str, formats: list = ["premium", "broadcast", "betting"]) -> dict:
    """
    Export all requested report formats for a matchup.
    Returns dict of report_ids and payloads.
    """
    ensure_dirs()
    bundle = {}
    for mode in formats:
        # Try to find report for this mode
        found = None
        for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["reports"])):
            if fname == f"report_{matchup_id}_{mode}.json":
                with open(os.path.join(DATA_ROOT, FOLDERS["reports"], fname), "r", encoding="utf-8") as f:
                    found = json.load(f)
                break
        if found:
            bundle[mode] = found
    return bundle
# --- Phase 5: Feedback Review & Version Promotion ---
from collections import Counter, defaultdict

def apply_feedback_review(report_id: str) -> dict:
    """
    Load all feedback for the report, group by engine/template/audience, summarize repeated issues,
    classify as cosmetic/content/model-affecting, and output a review object/action list.
    """
    ensure_dirs()
    feedback_dir = os.path.join(DATA_ROOT, FOLDERS["feedback"])
    feedbacks = []
    for fname in os.listdir(feedback_dir):
        with open(os.path.join(feedback_dir, fname), "r", encoding="utf-8") as f:
            fb = json.load(f)
            if fb.get("report_id") == report_id:
                feedbacks.append(fb)
    # Group by engine/template/audience
    groups = defaultdict(list)
    for fb in feedbacks:
        key = (fb.get("audience_type"), fb.get("category"), fb.get("severity"))
        groups[key].append(fb)
    # Summarize repeated issues
    issue_counter = Counter()
    for fb in feedbacks:
        issue_counter[(fb.get("category"), fb.get("severity"))] += 1
    # Classify
    classified = {"cosmetic": [], "content": [], "model_affecting": []}
    for fb in feedbacks:
        cat = fb.get("category", "")
        sev = fb.get("severity", "")
        if cat in ["typo", "format", "visual"]:
            classified["cosmetic"].append(fb)
        elif cat in ["accuracy", "logic", "data"] and sev in ["high", "blocker"]:
            classified["model_affecting"].append(fb)
        else:
            classified["content"].append(fb)
    # Output review object
    review = {
        "feedback_count": len(feedbacks),
        "grouped": dict(groups),
        "issue_summary": dict(issue_counter),
        "classified": classified,
        "action_list": [
            {"category": k[0], "severity": k[1], "count": v}
            for k, v in issue_counter.items()
        ]
    }
    return review

def promote_model_version(model_version: str, release_notes: str = "") -> dict:
    """
    Promote a model version if all checks pass, record promotion timestamp, attach notes, supersede prior active version.
    """
    ensure_dirs()
    mv_path = os.path.join(DATA_ROOT, FOLDERS["model_versions"], f"{model_version}.json")
    if not os.path.exists(mv_path):
        raise FileNotFoundError(f"Model version {model_version} not found.")
    # Load model version
    with open(mv_path, "r", encoding="utf-8") as f:
        mv = json.load(f)
    # Check for open blocker/major feedback
    feedback_dir = os.path.join(DATA_ROOT, FOLDERS["feedback"])
    blockers = []
    for fname in os.listdir(feedback_dir):
        with open(os.path.join(feedback_dir, fname), "r", encoding="utf-8") as f:
            fb = json.load(f)
            if fb.get("category") in ["accuracy", "logic", "data"] and fb.get("severity") in ["blocker", "high"] and fb.get("status") != "resolved":
                blockers.append(fb)
    if blockers:
        return {"promoted": False, "reason": "Open blocker/major feedback exists.", "blockers": blockers}
    # Mark prior active version as superseded (add 'superseded_by' field)
    for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["model_versions"])):
        if fname != f"{model_version}.json":
            path = os.path.join(DATA_ROOT, FOLDERS["model_versions"], fname)
            with open(path, "r", encoding="utf-8") as f:
                other = json.load(f)
            if not other.get("superseded_by"):
                other["superseded_by"] = model_version
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(other, f, default=str, indent=2)
    # Update promoted version
    mv["promoted_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mv["release_notes"] = release_notes
    with open(mv_path, "w", encoding="utf-8") as f:
        json.dump(mv, f, default=str, indent=2)
    return {"promoted": True, "model_version": model_version, "promoted_at": mv["promoted_at"], "release_notes": release_notes}
# --- Phase 4 Query/Inspection Helpers ---
def get_matchup_bundle(matchup_id: str) -> dict:
    """Return all objects for a matchup: matchup, prediction, report, result, calibration, model version, feedback."""
    ensure_dirs()
    bundle = {}
    # Matchup
    m_path = os.path.join(DATA_ROOT, FOLDERS["matchups"], f"{matchup_id}.json")
    if os.path.exists(m_path):
        with open(m_path, "r", encoding="utf-8") as f:
            bundle["matchup"] = json.load(f)
    # Prediction
    for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["predictions"])):
        with open(os.path.join(DATA_ROOT, FOLDERS["predictions"], fname), "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("matchup_id") == matchup_id:
                bundle["prediction"] = data
                break
    # Report
    for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["reports"])):
        with open(os.path.join(DATA_ROOT, FOLDERS["reports"], fname), "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("matchup_id") == matchup_id:
                bundle["report"] = data
                break
    # Result
    for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["results"])):
        with open(os.path.join(DATA_ROOT, FOLDERS["results"], fname), "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("matchup_id") == matchup_id:
                bundle["result"] = data
                break
    # Calibration
    for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["calibration"])):
        with open(os.path.join(DATA_ROOT, FOLDERS["calibration"], fname), "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("prediction_id") and data.get("result_id") and bundle.get("prediction") and bundle.get("result"):
                if data["prediction_id"] == bundle["prediction"]["id"] and data["result_id"] == bundle["result"]["id"]:
                    bundle["calibration"] = data
                    break
    # Model Version (from prediction if available)
    if "prediction" in bundle:
        mv = bundle["prediction"].get("model_version")
        if mv:
            mv_path = os.path.join(DATA_ROOT, FOLDERS["model_versions"], f"{mv}.json")
            if os.path.exists(mv_path):
                with open(mv_path, "r", encoding="utf-8") as f:
                    bundle["model_version"] = json.load(f)
    # Feedback (all for this report)
    if "report" in bundle:
        report_id = bundle["report"].get("id")
        feedbacks = []
        for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["feedback"])):
            with open(os.path.join(DATA_ROOT, FOLDERS["feedback"], fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("report_id") == report_id:
                    feedbacks.append(data)
        bundle["feedback"] = feedbacks
    return bundle

def list_matchup_history(fighter_id: str) -> list:
    """Return all matchup_ids where this fighter appeared."""
    ensure_dirs()
    history = []
    for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["matchups"])):
        with open(os.path.join(DATA_ROOT, FOLDERS["matchups"], fname), "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("fighter_a_id") == fighter_id or data.get("fighter_b_id") == fighter_id:
                history.append(data["id"])
    return history

def list_calibration_misses(style_pair: str = None, fighter_id: str = None) -> list:
    """Return all calibration logs where correct == False, optionally filtered by style_pair or fighter_id."""
    ensure_dirs()
    misses = []
    for fname in os.listdir(os.path.join(DATA_ROOT, FOLDERS["calibration"])):
        with open(os.path.join(DATA_ROOT, FOLDERS["calibration"], fname), "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data.get("correct"):
                # Optionally filter by style_pair or fighter_id
                add = True
                if style_pair or fighter_id:
                    # Need to load prediction and matchup for context
                    pred_id = data.get("prediction_id")
                    res_id = data.get("result_id")
                    pred = None
                    matchup = None
                    # Find prediction
                    for pf in os.listdir(os.path.join(DATA_ROOT, FOLDERS["predictions"])):
                        with open(os.path.join(DATA_ROOT, FOLDERS["predictions"], pf), "r", encoding="utf-8") as pfh:
                            pdat = json.load(pfh)
                            if pdat.get("id") == pred_id:
                                pred = pdat
                                break
                    if pred:
                        m_id = pred.get("matchup_id")
                        for mf in os.listdir(os.path.join(DATA_ROOT, FOLDERS["matchups"])):
                            with open(os.path.join(DATA_ROOT, FOLDERS["matchups"], mf), "r", encoding="utf-8") as mfh:
                                mdat = json.load(mfh)
                                if mdat.get("id") == m_id:
                                    matchup = mdat
                                    break
                    if style_pair and matchup:
                        # Assume style_pair is a string like "striking-vs-grappling"
                        a_style = pred.get("details", {}).get("style_a") or ""
                        b_style = pred.get("details", {}).get("style_b") or ""
                        if f"{a_style}-vs-{b_style}" != style_pair:
                            add = False
                    if fighter_id and matchup:
                        if fighter_id not in [matchup.get("fighter_a_id"), matchup.get("fighter_b_id")]:
                            add = False
                if add:
                    misses.append(data)
    return misses
# --- Phase 4 Orchestration ---
from typing import Union

def run_full_fight_pipeline(
    fighter_a_id: str,
    fighter_b_id: str,
    engine_output: dict,
    report_payload: dict,
    result_payload: Union[dict, None] = None,
    model_version_obj: Union['ModelVersion', None] = None,
    mode: str = "premium"
) -> dict:
    """
    Orchestrate the full fight pipeline:
    1. Ingest matchup and fighters (minimal stubs if not present)
    2. Save prediction
    3. Save report
    4. Optionally save result
    5. Optionally run calibration
    6. Optionally attach model version
    Returns a dict with all object IDs and calibration output if run.
    """
    ensure_dirs()
    matchup_id = engine_output.get("matchup_id") or report_payload.get("matchup_id")
    if not matchup_id:
        matchup_id = f"{fighter_a_id}_vs_{fighter_b_id}"
    # Minimal stub fighters
    fighters = []
    for fid in [fighter_a_id, fighter_b_id]:
        fighter_path = os.path.join(DATA_ROOT, FOLDERS["fighters"], f"{fid}.json")
        if os.path.exists(fighter_path):
            with open(fighter_path, "r", encoding="utf-8") as f:
                from_json = json.load(f)
            fighters.append(Fighter(**from_json))
        else:
            fighters.append(Fighter(id=fid, name=fid.replace('_', ' ').title()))
    # Ingest matchup
    matchup = Matchup(
        id=matchup_id,
        fighter_a_id=fighter_a_id,
        fighter_b_id=fighter_b_id,
        event=report_payload.get("event"),
        date=report_payload.get("date"),
        weight_class=report_payload.get("weight_class"),
        rounds=report_payload.get("rounds"),
        notes=report_payload.get("notes")
    )
    ingest_matchup(matchup, fighters)
    # Save prediction (now returns normalized dict, no file write)
    prediction = generate_prediction_from_engine(matchup_id, engine_output)
    # Save report
    report_id = save_report(matchup_id, report_payload, mode=mode)
    # Optionally save result and calibrate
    calibration = None
    result_id = None
    if result_payload:
        result = save_result(matchup_id, result_payload)
        result_id = result.id
        calibration = run_post_fight_calibration(matchup_id)
    # Optionally attach model version
    model_version_id = None
    if model_version_obj:
        model_version_id = save_model_version(model_version_obj)
    return {
        "matchup_id": matchup_id,
        "prediction": prediction,
        "report_id": report_id,
        "result_id": result_id,
        "calibration": _to_dict(calibration) if calibration else None,
        "model_version_id": model_version_id
    }
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

# --- Models ---


def generate_prediction_from_engine(matchup_id: str, engine_output: dict) -> 'Prediction':
    """Convert engine output to normalized dict and persist with debug_metrics."""
    import sys
    print("[MARKER] GENERATE_PREDICTION_FROM_ENGINE_LIVE", file=sys.stderr); sys.stderr.flush()
    print("[TRACE] generate_prediction_from_engine:entry", file=sys.stderr)
    print(f"[TRACE] engine_result_keys={list(engine_output.keys())}", file=sys.stderr)
    print(f"[TRACE] engine_result_debug_metrics={engine_output.get('debug_metrics')}", file=sys.stderr)
    print(f"[TRACE] engine_result_method={engine_output.get('method')}", file=sys.stderr)
    print(f"[TRACE] engine_result_round={engine_output.get('round')}", file=sys.stderr)
    legacy_id = _get_field(engine_output, "id", f"pred_{matchup_id}")
    print(
        f"[TRACE] legacy_id_assignment:matchup_id={matchup_id} legacy_id={legacy_id!r}",
        file=sys.stderr,
    )
    prediction_payload = {
        "id": legacy_id,
        "matchup_id": matchup_id,
        "event_id": engine_output.get("event_id"),
        "model_version": _get_field(engine_output, "model_version", "unknown"),
        "predicted_winner_id": _get_field(engine_output, "predicted_winner_id"),
        "confidence": _get_field(engine_output, "confidence"),
        "method": _get_field(engine_output, "method"),
        "round": _get_field(engine_output, "round"),
        "details": _get_field(engine_output, "details"),
        "debug_metrics": engine_output.get("debug_metrics", {}),
    }
    print(f"[TRACE] generate_prediction_from_engine:normalized={prediction_payload}", file=sys.stderr)
    return prediction_payload

class Prediction(BaseModel):
    id: str
    matchup_id: str
    model_version: str
    predicted_winner_id: str
    confidence: float | None = None
    method: Optional[str] = None  # e.g., "decision", "KO", "submission"
    round: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None

class Result(BaseModel):
    id: str
    matchup_id: str
    winner_id: str
    method: str
    round: int
    finished: bool
    notes: Optional[str] = None
    event: Optional[str] = None
    date: Optional[datetime] = None

class CalibrationLog(BaseModel):
    id: str
    prediction_id: str
    result_id: str
    model_version: str
    correct: bool
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


# --- Phase 3 Models ---
class Report(BaseModel):
    report_id: str
    matchup_id: str
    report_mode: str
    report_version: str
    sections: Dict[str, Any]
    artifacts: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ModelVersion(BaseModel):
    model_version: str
    engine_version: str
    template_version: str
    scorecard_model_version: str
    control_model_version: str
    style_tensor_version: str
    damage_dampener_version: str
    released_at: datetime
    notes: Optional[str] = None

class Feedback(BaseModel):
    feedback_id: str
    report_id: str
    audience_type: str
    category: str
    severity: str
    comment: str
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- File-based storage helpers ---

DATA_ROOT = "C:/Users/jusin/ai_risa_data"
FOLDERS = {
    "fighters": "fighters",
    "matchups": "matchups",
    "predictions": "predictions",
    "results": "results",
    "calibration": "calibration",
    "reports": "reports"
    ,"model_versions": "model_versions"
    ,"feedback": "feedback"
}

def ensure_dirs():
    for folder in FOLDERS.values():
        os.makedirs(os.path.join(DATA_ROOT, folder), exist_ok=True)


# --- Core Functions ---

def ingest_matchup(matchup: Matchup, fighters: List[Fighter]):
    """Save matchup and fighters to storage."""
    ensure_dirs()
    # Save fighters
    for fighter in fighters:
        path = os.path.join(DATA_ROOT, FOLDERS["fighters"], f"{fighter.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_to_dict(fighter), f, default=str, indent=2)
    # Save matchup
    path = os.path.join(DATA_ROOT, FOLDERS["matchups"], f"{matchup.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_to_dict(matchup), f, default=str, indent=2)


def save_prediction(prediction_payload: dict):
    """Legacy compatibility wrapper: DEPRECATED - no file write performed."""
    print("[TRACE] save_prediction:DEPRECATED - no file write performed", file=sys.stderr)
    return prediction_payload


def calibrate_prediction(prediction_id: str, result: Result, model_version: str):
    """Compare prediction to result, log calibration."""
    ensure_dirs()
    # Load prediction
    pred_path = os.path.join(DATA_ROOT, FOLDERS["predictions"], f"{prediction_id}.json")
    if not os.path.exists(pred_path):
        raise FileNotFoundError(f"Prediction {prediction_id} not found.")
    with open(pred_path, "r", encoding="utf-8") as f:
        pred_data = json.load(f)
    correct = (pred_data["predicted_winner_id"] == result.winner_id)
    log = CalibrationLog(
        id=f"calib_{prediction_id}_{result.id}",
        prediction_id=prediction_id,
        result_id=result.id,
        model_version=model_version,
        correct=correct,
        notes=None
    )
    # Save calibration log
    path = os.path.join(DATA_ROOT, FOLDERS["calibration"], f"{log.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_to_dict(log), f, default=str, indent=2)
    return log


# --- Phase 2 Integration Functions ---

# --- Output Mapping Helper ---
def _get_field(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def generate_prediction_from_engine(matchup_id: str, engine_output: dict, fighter_a_id=None, fighter_b_id=None, event_id=None) -> dict:
    # Patch: Ensure sim-count lineage fields are present in the payload
    for sim_field in ["requested_total_sims", "executed_sims", "counted_total"]:
        if sim_field not in engine_output and isinstance(engine_output, dict):
            debug_metrics = engine_output.get("debug_metrics", {})
            if sim_field in debug_metrics:
                engine_output[sim_field] = debug_metrics[sim_field]
    """Convert engine output to normalized dict and persist with debug_metrics."""
    import sys
    # Use fighter_a_id and fighter_b_id from the call context, not engine_output
    winner_raw = (
        _get_field(engine_output, "predicted_winner_id")
        or _get_field(engine_output, "winner")
        or _get_field(engine_output, "winner_id")
    )
    if winner_raw == "Win_A" and fighter_a_id:
        winner_raw = fighter_a_id
    elif winner_raw == "Win_B" and fighter_b_id:
        winner_raw = fighter_b_id

    debug_metrics = _get_field(engine_output, "debug_metrics", {}) or {}
    # Promote selected_method/selected_round if top-level fields are null
    method = _get_field(engine_output, "method")
    round_val = _get_field(engine_output, "round")
    if not method:
        method = debug_metrics.get("selected_method")
    if not round_val:
        round_val = debug_metrics.get("selected_round")
    legacy_id = _get_field(engine_output, "id", f"pred_{matchup_id}")
    print(
        f"[TRACE] legacy_id_assignment:matchup_id={matchup_id} legacy_id={legacy_id!r}",
        file=sys.stderr,
    )
    # --- Patch: propagate v100 winner-share and count fields, normalize as needed ---
    # --- PATCH: robust confidence extraction, no truthiness or fallback to 0.0 ---
    raw_confidence = None
    for src in (
        engine_output if isinstance(engine_output, dict) else {},
        debug_metrics if isinstance(debug_metrics, dict) else {},
    ):
        value = src.get("confidence")
        if value is not None:
            raw_confidence = value
            break
    try:
        confidence = float(raw_confidence) if raw_confidence is not None else None
    except Exception:
        confidence = None

    prediction_payload = {
        "id": legacy_id,
        "matchup_id": matchup_id,
        "event_id": event_id,
        "fighter_a_id": fighter_a_id,
        "fighter_b_id": fighter_b_id,
        "model_version": _get_field(engine_output, "model_version", "ai_risa_model_v1.0"),
        "predicted_winner_id": engine_output.get("predicted_winner_id") or engine_output.get("winner_id"),
        "winner_id": engine_output.get("predicted_winner_id") or engine_output.get("winner_id"),
        "confidence": confidence,
        "method": method,
        "round": round_val,
        "details": _get_field(engine_output, "details", {}),
        "debug_metrics": debug_metrics,
    }

    # Winner-share normalization and propagation
    win_a_pct = engine_output.get("fighter_a_win_pct") or engine_output.get("Win_A_%")
    win_b_pct = engine_output.get("fighter_b_win_pct") or engine_output.get("Win_B_%")
    # Convert to [0,1] if needed
    if win_a_pct is not None and win_a_pct > 1.0:
        win_a_pct = win_a_pct / 100.0
    if win_b_pct is not None and win_b_pct > 1.0:
        win_b_pct = win_b_pct / 100.0
    if win_a_pct is not None:
        prediction_payload["fighter_a_win_pct"] = win_a_pct
    if win_b_pct is not None:
        prediction_payload["fighter_b_win_pct"] = win_b_pct

    # Draw pct (if present)
    draw_pct = engine_output.get("draw_pct")
    if draw_pct is not None and draw_pct > 1.0:
        draw_pct = draw_pct / 100.0
    if draw_pct is not None:
        prediction_payload["draw_pct"] = draw_pct

    # Pass through win_probabilities and raw counts
    for key in ["win_probabilities", "win_count_a", "win_count_b", "draw_count", "total_sims"]:
        if key in engine_output:
            prediction_payload[key] = engine_output[key]

    # Also propagate legacy/other winner-share keys for robustness
    for key in ["A", "B", "Draw", "monte_carlo_summary"]:
        if key in engine_output:
            prediction_payload[key] = engine_output[key]
    from ai_risa_models import _trace_record
    import sys
    _trace_record("generate_prediction_from_engine_payload", prediction_payload)
    print(f"[TRACE] gen_pred:engine_result={{engine_output!r}}", file=sys.stderr)
    print(f"[TRACE] gen_pred:prediction_payload={{prediction_payload!r}}", file=sys.stderr)
    sys.stderr.flush()
    written_record = write_prediction_record(prediction_payload)
    print(f"[TRACE] gen_pred:written_record={written_record!r}", file=sys.stderr)
    print(f"[TRACE] gen_pred:prediction_payload_after_write={prediction_payload!r}", file=sys.stderr)
    sys.stderr.flush()
    if isinstance(written_record, dict):
        return written_record
    if written_record is None:
        return prediction_payload
    raise TypeError(
        f"write_prediction_record returned unsupported type: {type(written_record).__name__}"
    )



def save_report(matchup_id: str, report_payload: dict, mode: str = "premium"):
    """Save a report for a matchup."""
    ensure_dirs()
    report_id = report_payload.get("id", f"report_{matchup_id}_{mode}")
    # --- Patch: force fight_title in premium metadata ---
    if mode == "premium":
        fight_title = report_payload.get("fight_title")
        for fight in fight_list:
            try:
                requested_matchup_id = fight.get("matchup_id")
                # --- RESOLVER GUARD: log and check requested vs resolved matchup ---
                resolved_matchup = fight  # In this code, fight is the resolved matchup; adapt if you have a registry lookup
                print(f"[TRACE] resolver:requested_matchup_id={requested_matchup_id}", file=sys.stderr)
                print(f"[TRACE] resolver:resolved_matchup={resolved_matchup!r}", file=sys.stderr)

                resolved_matchup_id = resolved_matchup.get("matchup_id")
                fighter_a_id = resolved_matchup.get("fighter_a_id")
                fighter_b_id = resolved_matchup.get("fighter_b_id")

                print(f"[TRACE] resolver:resolved_fighter_a_id={fighter_a_id} resolved_fighter_b_id={fighter_b_id}", file=sys.stderr)

                if resolved_matchup_id != requested_matchup_id:
                    raise ValueError(
                        f"Matchup resolution mismatch: requested={requested_matchup_id} "
                        f"resolved={resolved_matchup_id}"
                    )

                if not fighter_a_id or not fighter_b_id:
                    raise ValueError(
                        f"Resolved matchup missing fighter ids: matchup_id={resolved_matchup_id} "
                        f"fighter_a_id={fighter_a_id} fighter_b_id={fighter_b_id}"
                    )

                matchup_id = resolved_matchup_id
                fight_results[matchup_id] = {
                    "matchup_id": matchup_id,
                    "reports": {},
                    "pdfs": {},
                    "warnings": [],
                    "failures": []
                }
                skip_reason = None
                if skip_reason:
                    print(f"[TRACE] engine_skip matchup_id={matchup_id} reason={skip_reason}", file=sys.stderr)

                print(f"[TRACE] pipeline:engine_call:start matchup_id={matchup_id}", file=sys.stderr); sys.stderr.flush()
                matchup = Matchup(
                    id=matchup_id,
                    fighter_a_id=fighter_a_id,
                    fighter_b_id=fighter_b_id,
                    event=event_id,
                    date=fight.get("date"),
                    weight_class=fight.get("weight_class"),
                    rounds=fight.get("rounds"),
                    notes=fight.get("notes")
                )
                fighters = [
                    Fighter(id=fighter_a_id, name=fight.get("fighter_a_name", fighter_a_id.replace('_', ' ').title())),
                    Fighter(id=fighter_b_id, name=fight.get("fighter_b_name", fighter_b_id.replace('_', ' ').title())),
                ]
                ingest_matchup(matchup, fighters)


                # --- After profile load, check loaded profile IDs ---   
            except Exception as e:
                print(f"[TRACE] pipeline:exception={e!r}", file=sys.stderr)
                import traceback
                print(traceback.format_exc(), file=sys.stderr)
                sys.stderr.flush()
                fighter_a_profile = fight.get("fighter_a_profile", {})
                fighter_b_profile = fight.get("fighter_b_profile", {})
                print(
                    f"[TRACE] resolver:loaded_profile_ids "
                    f"fighter_a_profile_id={fighter_a_profile.get('fighter_id')} "
                    f"fighter_b_profile_id={fighter_b_profile.get('fighter_id')}",
                    file=sys.stderr,
                )
                if fighter_a_profile.get("fighter_id") != fighter_a_id or fighter_b_profile.get("fighter_id") != fighter_b_id:
                    raise ValueError(
                        "Loaded fighter profiles do not match resolved matchup ids: "
                        f"expected=({fighter_a_id}, {fighter_b_id}) "
                        f"loaded=({fighter_a_profile.get('fighter_id')}, {fighter_b_profile.get('fighter_id')})"
                    )

                # Build engine input dict, preserving injected profiles if present
                engine_input = {
                    "matchup_id": matchup_id,
                    "fighter_a_id": fighter_a_id,
                    "fighter_b_id": fighter_b_id,
                    "event_id": event_id,
                    "date": fight.get("date"),
                    "weight_class": fight.get("weight_class"),
                    "rounds": fight.get("rounds"),
                    "notes": fight.get("notes"),
                    "fighter_a_profile": fight.get("fighter_a_profile"),
                    "fighter_b_profile": fight.get("fighter_b_profile"),
                }
                # --- After profile load, check loaded profile IDs ---
