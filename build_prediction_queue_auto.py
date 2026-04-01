import argparse
import csv
import json
import os
from datetime import datetime


def log(msg, *args, verbose=False, always=False, file=None):
    if always or verbose:
        print(msg.format(*args), flush=True, file=file)


SUMMARY_PATH = os.path.join("output", "dependency_resolution_summary.json")
QUEUE_JSON_PATH = os.path.join("output", "prediction_queue.json")
QUEUE_CSV_PATH = os.path.join("output", "prediction_queue.csv")
QUEUE_SUMMARY_JSON_PATH = os.path.join("output", "prediction_queue_build_summary.json")


def name_to_id(name):
    if not name or str(name).strip().upper() == "TBA":
        return None
    return str(name).strip().lower().replace(" ", "_")


def build_matchup_id(f1, f2):
    if not f1 or not f2:
        return None
    if str(f1).strip().upper() == "TBA" or str(f2).strip().upper() == "TBA":
        return None
    return f"{name_to_id(f1)}_vs_{name_to_id(f2)}"


def build_prediction_id(event_id, bout_id):
    return f"{event_id}__{bout_id}"


def main():
    parser = argparse.ArgumentParser(description="AI-RISA Prediction Queue Builder")
    parser.add_argument("--summary-path", default=SUMMARY_PATH)
    parser.add_argument("--queue-json-path", default=QUEUE_JSON_PATH)
    parser.add_argument("--queue-csv-path", default=QUEUE_CSV_PATH)
    parser.add_argument("--summary-json-path", default=QUEUE_SUMMARY_JSON_PATH)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    verbose = args.verbose

    started_at = datetime.now().isoformat()
    warnings = []
    errors = []
    rows = []

    if not os.path.exists(args.summary_path):
        errors.append({"type": "dependency_summary_missing", "detail": args.summary_path})
        resolver_rows = []
    else:
        with open(args.summary_path, "r", encoding="utf-8") as f:
            dep_summary = json.load(f)
        resolver_rows = dep_summary.get("details", {}).get("rows", []) if isinstance(dep_summary, dict) else []

    queue = []
    for row in resolver_rows:
        actions = row.get("actions", [])
        if "prediction_missing" not in actions:
            continue
        if "skipped_tba" in actions:
            warnings.append({"event_id": row.get("event_id"), "bout_id": row.get("bout_id"), "type": "skipped_tba"})
            continue

        event_id = row.get("event_id")
        bout_id = row.get("bout_id")
        fighter_1 = row.get("fighter_1")
        fighter_2 = row.get("fighter_2")
        fighter_1_id = name_to_id(fighter_1)
        fighter_2_id = name_to_id(fighter_2)
        matchup_id = build_matchup_id(fighter_1, fighter_2)
        prediction_id = build_prediction_id(event_id, bout_id)

        queue_row = {
            "event_id": event_id,
            "bout_id": bout_id,
            "fighter_1": fighter_1,
            "fighter_2": fighter_2,
            "fighter_1_id": fighter_1_id,
            "fighter_2_id": fighter_2_id,
            "matchup_id": matchup_id,
            "prediction_id": prediction_id,
            "reason": "prediction_missing",
        }
        queue.append(queue_row)
        rows.append(queue_row)

    os.makedirs(os.path.dirname(args.queue_json_path), exist_ok=True)
    with open(args.queue_json_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

    fieldnames = [
        "event_id",
        "bout_id",
        "fighter_1",
        "fighter_2",
        "fighter_1_id",
        "fighter_2_id",
        "matchup_id",
        "prediction_id",
        "reason",
    ]
    os.makedirs(os.path.dirname(args.queue_csv_path), exist_ok=True)
    with open(args.queue_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in queue:
            writer.writerow(row)

    counts = {
        "total_candidates_scanned": len(resolver_rows),
        "queued_bouts": len(queue),
        "excluded_tba": sum(1 for row in resolver_rows if "skipped_tba" in row.get("actions", [])),
    }

    artifacts = [args.queue_json_path, args.queue_csv_path, args.summary_json_path]
    summary_payload = {
        "stage": "prediction_queue_build",
        "status": "success" if not errors else "error",
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "counts": counts,
        "warnings": warnings,
        "errors": errors,
        "artifacts": artifacts,
        "details": {
            "rows": rows,
        },
    }

    os.makedirs(os.path.dirname(args.summary_json_path), exist_ok=True)
    with open(args.summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)

    log("[DONE] Prediction queue written: {}, {}", args.queue_json_path, args.queue_csv_path, verbose=verbose, always=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
