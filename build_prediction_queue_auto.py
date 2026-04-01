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


def append_skip_warning(warnings, event_id, bout_id, warning_type, detail=None):
    warning = {
        "event_id": event_id,
        "bout_id": bout_id,
        "type": warning_type,
    }
    if detail:
        warning["detail"] = detail
    warnings.append(warning)


def bump_reason(reason_code_counts, code):
    reason_code_counts[code] = reason_code_counts.get(code, 0) + 1


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
    skipped_rows = []

    if not os.path.exists(args.summary_path):
        errors.append({"type": "dependency_summary_missing", "detail": args.summary_path})
        resolver_rows = []
    else:
        with open(args.summary_path, "r", encoding="utf-8") as f:
            dep_summary = json.load(f)
        resolver_rows = dep_summary.get("details", {}).get("rows", []) if isinstance(dep_summary, dict) else []

    queue = []
    exclusion_counts = {
        "excluded_tba": 0,
        "excluded_unresolved_fighter_identity": 0,
        "excluded_partial_fighter_identity": 0,
        "excluded_unresolved_matchup_mapping": 0,
        "excluded_insufficient_enrichment": 0,
    }
    reason_code_counts = {}

    for row in resolver_rows:
        actions = row.get("actions", [])
        event_id = row.get("event_id")
        bout_id = row.get("bout_id")

        if "prediction_missing" not in actions:
            if "unresolved_missing_fighters" in actions:
                exclusion_counts["excluded_unresolved_fighter_identity"] += 1
                exclusion_counts["excluded_insufficient_enrichment"] += 1
                bump_reason(reason_code_counts, "unresolved_missing_fighters")
                bump_reason(reason_code_counts, "insufficient_enrichment")
                append_skip_warning(
                    warnings,
                    event_id,
                    bout_id,
                    "unresolved_missing_fighters",
                    "resolver reported unresolved_missing_fighters",
                )
                skipped_rows.append({"event_id": event_id, "bout_id": bout_id, "reason": "unresolved_missing_fighters"})
            elif "unresolved_partial_fighters" in actions:
                exclusion_counts["excluded_partial_fighter_identity"] += 1
                exclusion_counts["excluded_insufficient_enrichment"] += 1
                bump_reason(reason_code_counts, "unresolved_partial_fighters")
                bump_reason(reason_code_counts, "insufficient_enrichment")
                append_skip_warning(
                    warnings,
                    event_id,
                    bout_id,
                    "unresolved_partial_fighters",
                    "resolver reported unresolved_partial_fighters",
                )
                skipped_rows.append({"event_id": event_id, "bout_id": bout_id, "reason": "unresolved_partial_fighters"})
            continue

        if "skipped_tba" in actions:
            exclusion_counts["excluded_tba"] += 1
            bump_reason(reason_code_counts, "skipped_tba")
            append_skip_warning(warnings, event_id, bout_id, "skipped_tba")
            skipped_rows.append({"event_id": event_id, "bout_id": bout_id, "reason": "skipped_tba"})
            continue

        fighter_1 = row.get("fighter_1")
        fighter_2 = row.get("fighter_2")
        fighter_1_id = name_to_id(fighter_1)
        fighter_2_id = name_to_id(fighter_2)
        matchup_id = build_matchup_id(fighter_1, fighter_2)

        if not fighter_1_id and not fighter_2_id:
            exclusion_counts["excluded_unresolved_fighter_identity"] += 1
            exclusion_counts["excluded_insufficient_enrichment"] += 1
            bump_reason(reason_code_counts, "unresolved_missing_fighters")
            bump_reason(reason_code_counts, "insufficient_enrichment")
            append_skip_warning(
                warnings,
                event_id,
                bout_id,
                "unresolved_missing_fighters",
                "both fighter ids unresolved during queue build",
            )
            skipped_rows.append({"event_id": event_id, "bout_id": bout_id, "reason": "unresolved_missing_fighters"})
            continue

        if not fighter_1_id or not fighter_2_id:
            exclusion_counts["excluded_partial_fighter_identity"] += 1
            exclusion_counts["excluded_insufficient_enrichment"] += 1
            bump_reason(reason_code_counts, "unresolved_partial_fighters")
            bump_reason(reason_code_counts, "insufficient_enrichment")
            append_skip_warning(
                warnings,
                event_id,
                bout_id,
                "unresolved_partial_fighters",
                "one fighter id unresolved during queue build",
            )
            skipped_rows.append({"event_id": event_id, "bout_id": bout_id, "reason": "unresolved_partial_fighters"})
            continue

        if not matchup_id:
            exclusion_counts["excluded_unresolved_matchup_mapping"] += 1
            exclusion_counts["excluded_insufficient_enrichment"] += 1
            bump_reason(reason_code_counts, "unresolved_matchup_mapping")
            bump_reason(reason_code_counts, "insufficient_enrichment")
            append_skip_warning(
                warnings,
                event_id,
                bout_id,
                "unresolved_matchup_mapping",
                "matchup_id could not be derived from resolved fighter ids",
            )
            skipped_rows.append({"event_id": event_id, "bout_id": bout_id, "reason": "unresolved_matchup_mapping"})
            continue

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
        "excluded_tba": exclusion_counts["excluded_tba"],
        "excluded_unresolved_fighter_identity": exclusion_counts["excluded_unresolved_fighter_identity"],
        "excluded_partial_fighter_identity": exclusion_counts["excluded_partial_fighter_identity"],
        "excluded_unresolved_matchup_mapping": exclusion_counts["excluded_unresolved_matchup_mapping"],
        "excluded_insufficient_enrichment": exclusion_counts["excluded_insufficient_enrichment"],
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
            "skipped_rows": skipped_rows,
            "reason_code_counts": reason_code_counts,
        },
    }

    os.makedirs(os.path.dirname(args.summary_json_path), exist_ok=True)
    with open(args.summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)

    log("[DONE] Prediction queue written: {}, {}", args.queue_json_path, args.queue_csv_path, verbose=verbose, always=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
