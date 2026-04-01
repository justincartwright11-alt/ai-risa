import argparse
import csv
import json
import os
import re
from datetime import datetime


QUEUE_PATH = os.path.join("output", "prediction_queue.json")
SUMMARY_JSON_PATH = os.path.join("output", "prediction_queue_run_summary.json")
SUMMARY_CSV_PATH = os.path.join("output", "prediction_queue_run_summary.csv")
PREDICTIONS_DIR = "predictions"


def log(msg, *args, verbose=False, always=False, file=None):
    if always or verbose:
        print(msg.format(*args), flush=True, file=file)


def safe_prediction_filename(prediction_id):
    text = str(prediction_id or '').strip()
    if not text:
        return None
    # Keep output path Windows-safe while preserving prediction_id inside payload/summary rows.
    text = re.sub(r'[<>:"/\\|?*]+', '_', text)
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'_+', '_', text).strip('._')
    return text or None


def generate_prediction(event_id, bout_id, fighter_1_id, fighter_2_id, matchup_id, prediction_id):
    if not (fighter_1_id and fighter_2_id and matchup_id):
        return None, "prediction_skipped_missing_dependency"

    safe_name = safe_prediction_filename(prediction_id)
    if not safe_name:
        return None, "prediction_skipped_missing_dependency"

    pred_path = os.path.join(PREDICTIONS_DIR, f"{safe_name}.json")
    if os.path.exists(pred_path):
        return pred_path, "prediction_already_exists"

    payload = {
        "event_id": event_id,
        "bout_id": bout_id,
        "fighter_1_id": fighter_1_id,
        "fighter_2_id": fighter_2_id,
        "matchup_id": matchup_id,
        "prediction_id": prediction_id,
        "winner": None,
        "method": None,
        "confidence": None,
    }
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return pred_path, "prediction_created"


def main():
    parser = argparse.ArgumentParser(description="AI-RISA Prediction Queue Runner")
    parser.add_argument("--queue-path", default=QUEUE_PATH)
    parser.add_argument("--summary-json-path", default=SUMMARY_JSON_PATH)
    parser.add_argument("--summary-csv-path", default=SUMMARY_CSV_PATH)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    verbose = args.verbose

    started_at = datetime.now().isoformat()
    warnings = []
    errors = []
    rows = []
    artifacts = [args.summary_json_path, args.summary_csv_path]

    if not os.path.exists(args.queue_path):
        errors.append({"type": "queue_missing", "detail": args.queue_path})
        queue = []
    else:
        with open(args.queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

    for row in queue:
        event_id = row.get("event_id")
        bout_id = row.get("bout_id")
        fighter_1_id = row.get("fighter_1_id")
        fighter_2_id = row.get("fighter_2_id")
        matchup_id = row.get("matchup_id")
        prediction_id = row.get("prediction_id")

        try:
            pred_path, outcome = generate_prediction(
                event_id,
                bout_id,
                fighter_1_id,
                fighter_2_id,
                matchup_id,
                prediction_id,
            )
        except Exception as exc:
            pred_path = None
            outcome = "prediction_failed"
            errors.append(
                {
                    "event_id": event_id,
                    "bout_id": bout_id,
                    "type": "prediction_failed",
                    "detail": str(exc),
                }
            )

        if pred_path:
            artifacts.append(pred_path)

        if outcome == "prediction_skipped_missing_dependency":
            warnings.append({"event_id": event_id, "bout_id": bout_id, "type": "skipped_missing_dependency"})
        if outcome == "prediction_already_exists":
            warnings.append({"event_id": event_id, "bout_id": bout_id, "type": "already_exists"})

        rows.append(
            {
                "event_id": event_id,
                "bout_id": bout_id,
                "fighter_1_id": fighter_1_id,
                "fighter_2_id": fighter_2_id,
                "matchup_id": matchup_id,
                "prediction_id": prediction_id,
                "prediction_file": pred_path or "",
                "outcome": outcome,
            }
        )

    counts = {
        "queued_bouts": len(queue),
        "created_predictions": sum(1 for r in rows if r["outcome"] == "prediction_created"),
        "skipped_missing_dependencies": sum(1 for r in rows if r["outcome"] == "prediction_skipped_missing_dependency"),
        "already_exists": sum(1 for r in rows if r["outcome"] == "prediction_already_exists"),
        "failed": sum(1 for r in rows if r["outcome"] == "prediction_failed"),
    }

    os.makedirs(os.path.dirname(args.summary_csv_path), exist_ok=True)
    with open(args.summary_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["event_id", "bout_id", "fighter_1_id", "fighter_2_id", "matchup_id", "prediction_id", "prediction_file", "outcome"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    summary_payload = {
        "stage": "prediction_queue_run",
        "status": "success" if not errors else "error",
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "counts": counts,
        "warnings": warnings,
        "errors": errors,
        "artifacts": sorted(set(artifacts)),
        "details": {
            "rows": rows,
        },
    }

    os.makedirs(os.path.dirname(args.summary_json_path), exist_ok=True)
    with open(args.summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)

    log("[DONE] Prediction queue run summary written: {}, {}", args.summary_json_path, args.summary_csv_path, always=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
