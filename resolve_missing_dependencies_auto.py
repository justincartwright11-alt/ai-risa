import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path


def log(msg, *args, verbose=False, always=False, file=None):
    if always or verbose:
        print(msg.format(*args), flush=True, file=file)


def slugify(name):
    return str(name).strip().lower().replace(" ", "_")


def is_tba(name):
    if not name:
        return True
    n = str(name).strip().lower()
    return n in {"tba", "tbd", "to be announced", "to be determined", "unknown", "opponent tba"}


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="AI-RISA Dependency Resolver")
    parser.add_argument("--events-dir", default="events")
    parser.add_argument("--fighters-dir", default="fighters")
    parser.add_argument("--matchups-dir", default="matchups")
    parser.add_argument("--predictions-dir", default="predictions")
    parser.add_argument("--summary-json", default="output/dependency_resolution_summary.json")
    parser.add_argument("--summary-csv", default="output/dependency_resolution_summary.csv")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    verbose = args.verbose

    started_at = datetime.now().isoformat()
    status = "success"
    warnings = []
    errors = []
    counts = {}
    rows = []
    artifacts = [args.summary_json, args.summary_csv]

    event_files = sorted(Path(args.events_dir).glob("*.json"))
    action_counts = {}
    total_bouts = 0

    for event_file in event_files:
        try:
            with open(event_file, "r", encoding="utf-8") as f:
                event = json.load(f)
        except Exception as exc:
            errors.append({"type": "event_read_failed", "event_file": str(event_file), "detail": str(exc)})
            status = "error"
            continue

        event_id = event.get("event_id", "")
        bouts = event.get("bouts", [])
        log("[DEBUG] Processing event_id={}, bouts={}", event_id, len(bouts), verbose=verbose)

        for i, bout in enumerate(bouts):
            total_bouts += 1
            bout_id = bout.get("bout_id", f"idx_{i}")
            f1 = bout.get("fighter_1")
            f2 = bout.get("fighter_2")
            actions = []

            if is_tba(f1) or is_tba(f2):
                actions.append("skipped_tba")
            else:
                for fighter, role in [(f1, "fighter_1"), (f2, "fighter_2")]:
                    slug = slugify(fighter)
                    fighter_path = os.path.join(args.fighters_dir, f"{slug}.json")
                    if not os.path.exists(fighter_path):
                        os.makedirs(args.fighters_dir, exist_ok=True)
                        stub = {
                            "name": fighter,
                            "sport": "MMA",
                            "division": "Unknown",
                            "stance": "Orthodox",
                            "style": "Unknown",
                            "team": "",
                            "notes": "Auto-generated stub from dependency resolver.",
                        }
                        with open(fighter_path, "w", encoding="utf-8") as f:
                            json.dump(stub, f, indent=2, ensure_ascii=False)
                        actions.append(f"{role}_stub_created")
                    artifacts.append(fighter_path)

                matchup_slug = f"{slugify(f1)}_vs_{slugify(f2)}"
                matchup_path = os.path.join(args.matchups_dir, f"{matchup_slug}.json")
                if not os.path.exists(matchup_path):
                    os.makedirs(args.matchups_dir, exist_ok=True)
                    stub = {"fighters": [f1, f2], "weight_class": "Unknown", "sport": "MMA"}
                    with open(matchup_path, "w", encoding="utf-8") as f:
                        json.dump(stub, f, indent=2, ensure_ascii=False)
                    actions.append("matchup_stub_created")
                artifacts.append(matchup_path)

                prediction_path = os.path.join(args.predictions_dir, f"{matchup_slug}_prediction.json")
                if not os.path.exists(prediction_path):
                    actions.append("prediction_missing")
                else:
                    artifacts.append(prediction_path)

                if not actions:
                    actions.append("already_complete")

            for action in actions:
                action_counts[action] = action_counts.get(action, 0) + 1

            row = {
                "event_id": event_id,
                "bout_id": bout_id,
                "fighter_1": f1,
                "fighter_2": f2,
                "actions": actions,
            }
            rows.append(row)

    counts.update(action_counts)
    counts["processed_events"] = len(event_files)
    counts["processed_bouts"] = total_bouts

    if action_counts.get("skipped_tba", 0) > 0:
        warnings.append({"type": "skipped_tba", "count": action_counts["skipped_tba"]})

    summary_payload = {
        "stage": "dependency_resolution",
        "status": status if not errors else "error",
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

    write_json(args.summary_json, summary_payload)
    write_csv(args.summary_csv, rows, ["event_id", "bout_id", "fighter_1", "fighter_2", "actions"])
    log("[DONE] Dependency resolution complete. Summary written to {} and {}", args.summary_json, args.summary_csv, always=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
