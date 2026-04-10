# backfill_actual_results.py
"""
Semi-automated backfill of actual results for all prediction files.
- Reads all predictions in predictions/
- Attempts to match each to an actual result (stub: manual or future API integration)
- Writes:
  - ops/accuracy/actual_results.json (resolved)
  - ops/accuracy/actual_results_unresolved.json (unresolved)
  - ops/accuracy/actual_results_backfill_report.md (summary)
"""
import os
import json
from glob import glob
from datetime import datetime

PREDICTIONS_DIR = os.path.join(os.path.dirname(__file__), "predictions")
ACTUALS_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "actual_results.json")
UNRESOLVED_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "actual_results_unresolved.json")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "actual_results_backfill_report.md")


MANUAL_ACTUALS_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "actual_results_manual.json")

def load_manual_actuals():
    if not os.path.exists(MANUAL_ACTUALS_PATH):
        return {}
    with open(MANUAL_ACTUALS_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Convert list of dicts to {fight_id: actuals_dict}
            return {row["fight_id"]: row for row in data if row.get("fight_id")}
        except Exception as e:
            print(f"Warning: Could not load manual actuals: {e}")
            return {}

def parse_fight_id(pred_path):
    base = os.path.basename(pred_path)
    if base.endswith("_prediction.json"):
        return base[:-len("_prediction.json")]
    if base.startswith("pred_") and base.endswith(".json"):
        return base[len("pred_"):-len(".json")]
    return os.path.splitext(base)[0]

def parse_fighter_names(fight_id):
    if "_vs_" in fight_id:
        parts = fight_id.split("_vs_")
        if len(parts) == 2:
            return parts[0], parts[1]
    return "UNKNOWN", "UNKNOWN"

def main():
    os.makedirs(os.path.dirname(ACTUALS_PATH), exist_ok=True)
    pred_files = glob(os.path.join(PREDICTIONS_DIR, "*_prediction.json")) + glob(os.path.join(PREDICTIONS_DIR, "pred_*.json"))
    manual_actuals = load_manual_actuals()
    resolved = []
    unresolved = []
    for pred_path in pred_files:
        fight_id = parse_fight_id(pred_path)
        fighter_a, fighter_b = parse_fighter_names(fight_id)
        # 1. Try to match from manual actuals
        actual = manual_actuals.get(fight_id)
        # 2. (future) Try to match from automated sources here
        if actual:
            resolved.append({
                "fight_id": fight_id,
                "actual_winner": actual.get("actual_winner", "UNKNOWN"),
                "actual_method": actual.get("actual_method", "UNKNOWN"),
                "actual_round": actual.get("actual_round", "UNKNOWN"),
                "event_date": actual.get("event_date", "UNKNOWN"),
                "source": actual.get("source", "manual")
            })
        else:
            unresolved.append({
                "fight_id": fight_id,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "prediction_file": os.path.relpath(pred_path, os.path.dirname(__file__))
            })
    with open(ACTUALS_PATH, "w", encoding="utf-8") as f:
        json.dump(resolved, f, indent=2, ensure_ascii=False)
    with open(UNRESOLVED_PATH, "w", encoding="utf-8") as f:
        json.dump(unresolved, f, indent=2, ensure_ascii=False)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Actual Results Backfill Report\n\n")
        f.write(f"Total predictions: {len(pred_files)}\n")
        f.write(f"Resolved actuals: {len(resolved)}\n")
        f.write(f"Unresolved: {len(unresolved)}\n\n")
        if unresolved:
            f.write("## Unresolved fights:\n")
            for u in unresolved:
                f.write(f"- {u['fight_id']} ({u['fighter_a']} vs {u['fighter_b']})\n")
    print(f"Wrote {ACTUALS_PATH}, {UNRESOLVED_PATH}, {REPORT_PATH}")

if __name__ == "__main__":
    main()
