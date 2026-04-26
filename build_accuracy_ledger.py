def get_optional_signal(data, key, aliases=None, containers=None):
    aliases = aliases or []
    containers = containers or ["prediction", "prediction_record", "signals", "meta", "features"]
    for k in [key] + aliases:
        if isinstance(data, dict) and k in data:
            return data[k]
    for container in containers:
        block = data.get(container)
        if isinstance(block, dict):
            for k in [key] + aliases:
                if k in block:
                    return block[k]
    return None
import unicodedata
def normalize_winner_label(name):
    if not name or not isinstance(name, str):
        return "unknown"
    # Lowercase
    s = name.lower()
    # Strip accents
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    # Replace spaces and hyphens with underscores
    s = re.sub(r"[\s\-]+", "_", s)
    # Collapse duplicate underscores
    s = re.sub(r"_+", "_", s)
    # Trim leading/trailing underscores
    s = s.strip('_')
    return s or "unknown"

def normalize_method_label(method):
    if not method or not isinstance(method, str):
        return "unknown"
    s = method.lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('-', ' ').replace('_', ' ')
    s = re.sub(r"\s+", " ", s).strip()
    # Map to stable buckets
    if any(x in s for x in ["decision", "unanimous decision", "split decision", "majority decision"]):
        return "decision"
    if any(x in s for x in ["ko", "tko", "stoppage", "doctor stoppage", "corner stoppage"]):
        return "stoppage"
    if "submission" in s:
        return "submission"
    return "unknown"
# build_accuracy_ledger.py
"""
Scans all committed AI-RISA prediction outputs, normalizes them into the canonical accuracy ledger schema,
and writes both JSON and CSV ledgers to ops/accuracy/.
"""

import os
import json
import csv
from glob import glob
from typing import List, Dict, Any
from accuracy_ledger_schema import AccuracyLedgerRecord
from datetime import datetime
import re

PREDICTIONS_DIR = os.path.join(os.path.dirname(__file__), "predictions")
LEDGER_JSON = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger.json")
LEDGER_CSV = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger.csv")
LEDGER_WARNINGS = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger_warnings.json")
JOIN_AUDIT_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_join_audit.json")

def canonical_join_key(s):
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\.json$", "", s)
    s = re.sub(r"_prediction$", "", s)
    s = re.sub(r"^pred_", "", s)
    s = re.sub(r"_pred$", "", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip('_')
    return s
# build_accuracy_ledger.py
"""
Scans all committed AI-RISA prediction outputs, normalizes them into the canonical accuracy ledger schema,
and writes both JSON and CSV ledgers to ops/accuracy/.
"""

import os
import json
import csv
from glob import glob
from typing import List, Dict, Any
from accuracy_ledger_schema import AccuracyLedgerRecord
from datetime import datetime


PREDICTIONS_DIR = os.path.join(os.path.dirname(__file__), "predictions")
LEDGER_JSON = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger.json")
LEDGER_CSV = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger.csv")
LEDGER_WARNINGS = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger_warnings.json")


# Load actual results from canonical source
ACTUAL_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "actual_results.json")
def load_actual_results():
    if not os.path.exists(ACTUAL_RESULTS_PATH):
        return {}, {}, []
    with open(ACTUAL_RESULTS_PATH, encoding="utf-8") as f:
        records = json.load(f)
    by_fight_id = {r["fight_id"]: r for r in records if "fight_id" in r}
    by_canonical = {canonical_join_key(r["fight_id"]): r for r in records if "fight_id" in r}
    return by_fight_id, by_canonical, records


CONFIDENCE_BUCKETS = [
    (0, 49, "0-49"),
    (50, 59, "50-59"),
    (60, 69, "60-69"),
    (70, 79, "70-79"),
    (80, 89, "80-89"),
    (90, 101, "90-100"),
]

def bucket_confidence(conf):
    if conf is None:
        return "UNKNOWN"
    try:
        val = float(conf)
        if 0 <= val <= 1:
            val = val * 100
        if not (0 <= val <= 100):
            return "UNKNOWN"
        for low, high, label in CONFIDENCE_BUCKETS:
            if low <= val < high or (val == 100 and high == 101):
                return label
    except Exception:
        return "UNKNOWN"
    return "UNKNOWN"

def normalize_confidence(conf):
    if conf is None:
        return None
    try:
        val = float(conf)
        if 0 <= val <= 1:
            return round(val * 100, 2)
        if 0 <= val <= 100:
            return round(val, 2)
    except Exception:
        return None
    return None

def compute_round_error(pred, actual):
    try:
        return abs(int(pred) - int(actual))
    except Exception:
        return None


def load_prediction_files() -> List[str]:
    # Discover all relevant prediction files, including signal validation and calibrated
    files = []
    files += glob(os.path.join(PREDICTIONS_DIR, "*_signal_validation.json"))
    files += glob(os.path.join(PREDICTIONS_DIR, "*_calibrated.json"))
    files += glob(os.path.join(PREDICTIONS_DIR, "*_prediction.json"))
    files += glob(os.path.join(PREDICTIONS_DIR, "pred_*.json"))
    # Remove duplicates (same file could match multiple globs)
    files = list(dict.fromkeys(files))
    return files


def parse_fighter_names_from_filename(filename: str):
    # Try to extract fighter names from patterns like x_vs_y_prediction
    base = os.path.basename(filename)
    stem = base.replace('_prediction.json', '').replace('pred_', '')
    if '_vs_' in stem:
        parts = stem.split('_vs_')
        if len(parts) == 2:
            return parts[0], parts[1]
    return "UNKNOWN", "UNKNOWN"

def normalize_prediction(pred_path: str, warnings: List[Dict[str, Any]], actuals_by_id: Dict[str, Any], actuals_by_canonical: Dict[str, Any], join_audit: list) -> Dict[str, Any]:
    """
    Normalize a prediction file into the canonical ledger row.
    Handles full, intermediate, and legacy schemas.
    Joins actuals after normalization.
    """
    try:
        with open(pred_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        warnings.append({"file": pred_path, "error": f"Unreadable JSON: {e}"})
        return None

    # Try full schema
    try:
        from ai_risa_prediction_schema import PredictionRecord
        pred = PredictionRecord.model_validate(data)
        row = {
            "fight_id": getattr(pred, "matchup_id", None) or getattr(pred, "prediction_id", None) or os.path.splitext(os.path.basename(pred_path))[0],
            "event_date": pred.prediction_timestamp.strftime("%Y-%m-%d") if getattr(pred, "prediction_timestamp", None) else "UNKNOWN",
            "fighter_a": getattr(pred, "fighter_a_id", "UNKNOWN"),
            "fighter_b": getattr(pred, "fighter_b_id", "UNKNOWN"),
            "predicted_winner": getattr(pred, "predicted_winner_id", None) or getattr(pred, "winner", None) or getattr(pred, "predicted_winner", None) or "UNKNOWN",
            "predicted_method": getattr(pred, "method", None) or getattr(pred, "predicted_method", None) or "UNKNOWN",
            "predicted_round": getattr(pred, "round", None) or getattr(pred, "predicted_round", None) or None,
            "confidence": normalize_confidence(getattr(pred, "confidence", None)),
            "schema_variant": "full"
        }
    except Exception:
        # Try intermediate schema
        if any(k in data for k in ("predicted_winner", "winner", "method", "confidence")):
            row = normalize_legacy_prediction(data, pred_path)
            row["schema_variant"] = "intermediate"
        else:
            row = normalize_legacy_prediction(data, pred_path)
            row["schema_variant"] = "legacy"

    # Always emit stoppage/collapse features, mapped from prediction_data
    row["stoppage_propensity"] = get_optional_signal(data, "stoppage_propensity")
    row["round_finish_tendency"] = get_optional_signal(data, "round_finish_tendency")
    row["signal_gap"] = get_optional_signal(data, "signal_gap")

    # Join actuals with audit
    fight_id = row.get("fight_id", None)
    pred_canonical = canonical_join_key(fight_id)
    actual = None
    join_status = "no_actual_found"
    matched_actual_id = None
    # 1. Exact match
    if fight_id and fight_id in actuals_by_id:
        actual = actuals_by_id[fight_id]
        join_status = "matched_exact"
        matched_actual_id = fight_id
    # 2. Canonical match
    elif pred_canonical and pred_canonical in actuals_by_canonical:
        actual = actuals_by_canonical[pred_canonical]
        join_status = "matched_normalized"
        matched_actual_id = actual.get("fight_id")
    # 3. Fallback: try filename stem
    else:
        stem = canonical_join_key(os.path.splitext(os.path.basename(pred_path))[0])
        if stem in actuals_by_canonical:
            actual = actuals_by_canonical[stem]
            join_status = "matched_fallback"
            matched_actual_id = actual.get("fight_id")
        else:
            actual = {}
    row["actual_winner"] = actual.get("actual_winner", "UNKNOWN")
    row["actual_method"] = actual.get("actual_method", "UNKNOWN")
    row["actual_round"] = actual.get("actual_round", "UNKNOWN")
    row["predicted_winner_normalized"] = normalize_winner_label(row.get("predicted_winner"))
    row["actual_winner_normalized"] = normalize_winner_label(row.get("actual_winner"))
    row["predicted_method_normalized"] = normalize_method_label(row.get("predicted_method"))
    row["actual_method_normalized"] = normalize_method_label(row.get("actual_method"))
    row["resolved_result"] = bool(actual)
    row["hit_winner"] = (row["predicted_winner_normalized"] == row["actual_winner_normalized"])
    row["hit_method"] = (row["predicted_method_normalized"] == row["actual_method_normalized"])
    row["round_error"] = compute_round_error(row["predicted_round"], row["actual_round"])
    row["confidence_bucket"] = bucket_confidence(row["confidence"])
    row["source_file"] = os.path.relpath(pred_path, os.path.dirname(__file__))
    row["result_join_status"] = join_status
    # Audit entry
    join_audit.append({
        "ledger_fight_id": fight_id,
        "ledger_canonical": pred_canonical,
        "matched_actual_id": matched_actual_id,
        "join_status": join_status,
        "source_file": row["source_file"]
    })
    return row

def normalize_legacy_prediction(data, pred_path):
    """
    Normalize a legacy or minimal prediction file to the canonical ledger row.
    """
    row = {}
    row["fight_id"] = data.get("matchup_id") or data.get("prediction_id") or os.path.splitext(os.path.basename(pred_path))[0]
    row["event_date"] = data.get("event_date") or data.get("prediction_timestamp") or "UNKNOWN"
    if isinstance(row["event_date"], str) and len(row["event_date"]) > 10:
        try:
            row["event_date"] = datetime.fromisoformat(row["event_date"]).strftime("%Y-%m-%d")
        except Exception:
            row["event_date"] = "UNKNOWN"
    elif isinstance(row["event_date"], (int, float)):
        try:
            row["event_date"] = datetime.utcfromtimestamp(row["event_date"]).strftime("%Y-%m-%d")
        except Exception:
            row["event_date"] = "UNKNOWN"
    row["fighter_a"] = data.get("fighter_a_id") or data.get("fighter_a")
    row["fighter_b"] = data.get("fighter_b_id") or data.get("fighter_b")
    if not row["fighter_a"] or not row["fighter_b"]:
        fa, fb = parse_fighter_names_from_filename(pred_path)
        row["fighter_a"] = row["fighter_a"] or fa
        row["fighter_b"] = row["fighter_b"] or fb
    row["fighter_a"] = row["fighter_a"] or "UNKNOWN"
    row["fighter_b"] = row["fighter_b"] or "UNKNOWN"
    row["predicted_winner"] = data.get("predicted_winner_id") or data.get("winner") or data.get("predicted_winner") or "UNKNOWN"
    row["predicted_method"] = data.get("method") or data.get("predicted_method") or data.get("method_tendency") or "UNKNOWN"
    row["predicted_round"] = next((v for v in [data.get("round"), data.get("predicted_round")] if v is not None), None)
    conf = next((v for v in [data.get("confidence"), data.get("win_probability"), data.get("probability")] if v is not None), None)
    row["confidence"] = normalize_confidence(conf)
    return row


def write_json_ledger(records: List[Dict[str, Any]]):
    with open(LEDGER_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def write_csv_ledger(records: List[Dict[str, Any]]):
    if not records:
        return
    with open(LEDGER_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        for r in records:
            writer.writerow(r)



def main():
    os.makedirs(os.path.dirname(LEDGER_JSON), exist_ok=True)
    files = load_prediction_files()
    if not files:
        raise RuntimeError("No prediction files found.")
    actuals_by_id, actuals_by_canonical, actuals_list = load_actual_results()
    warnings = []
    join_audit = []
    # --- Dedupe/precedence logic ---
    # Map canonical fight_id to (precedence, file_path, row)
    precedence_map = {}
    precedence_order = ["signal_validation", "calibrated", "prediction", "legacy"]
    def file_precedence(f):
        base = os.path.basename(f)
        if base.endswith("_signal_validation.json"): return 0
        if base.endswith("_calibrated.json"): return 1
        if base.endswith("_prediction.json"): return 2
        if base.startswith("pred_"): return 3
        return 4
    for f in files:
        row = normalize_prediction(f, warnings, actuals_by_id, actuals_by_canonical, join_audit)
        if not row:
            continue
        canon = canonical_join_key(row.get("fight_id", ""))
        prec = file_precedence(f)
        if canon not in precedence_map or prec < precedence_map[canon][0]:
            precedence_map[canon] = (prec, f, row)
    # Only keep the highest-precedence row per canonical fight_id
    records = [v[2] for v in precedence_map.values()]
    if not records:
        raise RuntimeError("Zero rows could be normalized from prediction files.")
    write_json_ledger(records)
    write_csv_ledger(records)
    with open(LEDGER_WARNINGS, "w", encoding="utf-8") as wf:
        json.dump(warnings, wf, indent=2, ensure_ascii=False)
    # Write join audit for all actuals (including unresolved)
    audit_report = []
    ledger_keys = {r["ledger_fight_id"]: r for r in join_audit}
    canonical_ledger_keys = {r["ledger_canonical"]: r for r in join_audit}
    for actual in actuals_list:
        act_id = actual["fight_id"]
        act_canon = canonical_join_key(act_id)
        matched = ledger_keys.get(act_id) or canonical_ledger_keys.get(act_canon)
        audit_report.append({
            "manual_actual_fight_id": act_id,
            "manual_actual_canonical": act_canon,
            "matched_ledger_fight_id": matched["ledger_fight_id"] if matched else None,
            "matched_ledger_canonical": matched["ledger_canonical"] if matched else None,
            "join_status": matched["join_status"] if matched else "not_scored",
            "reason": "not_scored" if not matched else "matched"
        })
    with open(JOIN_AUDIT_PATH, "w", encoding="utf-8") as jf:
        json.dump(audit_report, jf, indent=2, ensure_ascii=False)
    print(f"Wrote {len(records)} records to {LEDGER_JSON} and {LEDGER_CSV}")
    print(f"Wrote {len(warnings)} warnings to {LEDGER_WARNINGS}")
    print(f"Wrote join audit to {JOIN_AUDIT_PATH}")

if __name__ == "__main__":
    main()
