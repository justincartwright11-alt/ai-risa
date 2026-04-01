import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCHEDULE_SOURCE = "C:/ai_risa_data/incoming/upcoming_events.json"
SCHEDULE_OUT = "C:/ai_risa_data/schedules/upcoming_auto.json"
SCHEDULE_EVENTS_DIR = "C:/ai_risa_data/events"
SCHEDULE_SUMMARY_JSON = "C:/ai_risa_data/output/upcoming_auto_summary.json"
SCHEDULE_SUMMARY_CSV = "C:/ai_risa_data/output/upcoming_auto_summary.csv"

SUMMARY_PATH = Path("output/full_pipeline_run_summary.json")
SUMMARY_CSV_PATH = Path("output/full_pipeline_run_summary.csv")

STAGES = [
    ("ingest", "ingest_upcoming_events_sources.py", ["incoming/upcoming_events_ingest_summary.json"]),
    ("schedule", "build_upcoming_schedule_auto.py", [SCHEDULE_SUMMARY_JSON, SCHEDULE_SUMMARY_CSV, SCHEDULE_OUT]),
    ("resolver", "resolve_missing_dependencies_auto.py", ["output/dependency_resolution_summary.json"]),
    ("queue_build", "build_prediction_queue_auto.py", ["output/prediction_queue.json", "output/prediction_queue_build_summary.json"]),
    ("queue_run", "run_prediction_queue_auto.py", ["output/prediction_queue_run_summary.json"]),
    ("batch", "run_event_batch_auto.py", ["output/event_batch_run_summary.json"]),
]

DRY_RUN_EXECUTE_WITH_FLAG = {"schedule", "batch"}


def log(msg, *args, verbose=False, always=False, file=None):
    if always or verbose:
        print(msg.format(*args), flush=True, file=file)


def parse_args():
    parser = argparse.ArgumentParser(description="AI-RISA Full Pipeline Orchestrator")
    parser.add_argument("--formats", nargs="*", default=["md", "docx", "pdf"])
    parser.add_argument("--strict", action="store_true", help="Abort on first hard stage failure")
    parser.add_argument("--force-predictions", action="store_true", help="Forward force flag to queue-run stage if supported")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Simulate orchestration without mutating production stage outputs")
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument("--skip-schedule", action="store_true")
    parser.add_argument("--skip-resolver", action="store_true")
    parser.add_argument("--skip-queue-build", action="store_true")
    parser.add_argument("--skip-queue-run", action="store_true")
    parser.add_argument("--skip-batch", action="store_true")
    return parser.parse_args()


def write_json(path, payload):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_csv(path, stage_rows):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    fieldnames = ["stage", "status", "started_at", "finished_at", "exit_code", "command", "summary_paths"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in stage_rows:
            writer.writerow(
                {
                    "stage": row.get("stage"),
                    "status": row.get("status"),
                    "started_at": row.get("started_at"),
                    "finished_at": row.get("finished_at"),
                    "exit_code": row.get("exit_code"),
                    "command": row.get("command"),
                    "summary_paths": ";".join(row.get("summary_paths", [])),
                }
            )


def run_stage(stage_name, script, summary_paths, args):
    started_at = datetime.now().isoformat()

    skip_flag_name = f"skip_{stage_name.replace('-', '_')}"
    if getattr(args, skip_flag_name, False):
        return {
            "stage": stage_name,
            "status": "soft_skip",
            "started_at": started_at,
            "finished_at": datetime.now().isoformat(),
            "exit_code": 0,
            "command": "",
            "summary_paths": summary_paths,
            "details": {"stdout": "", "stderr": "Skipped by flag."},
        }

    if args.dry_run and stage_name not in DRY_RUN_EXECUTE_WITH_FLAG:
        if stage_name == "ingest":
            cmd = [sys.executable, script]
        elif stage_name == "resolver":
            cmd = [sys.executable, script]
        elif stage_name == "queue_build":
            cmd = [sys.executable, script]
        elif stage_name == "queue_run":
            cmd = [sys.executable, script]
        else:
            cmd = [sys.executable, script]
        return {
            "stage": stage_name,
            "status": "soft_skip",
            "started_at": started_at,
            "finished_at": datetime.now().isoformat(),
            "exit_code": 0,
            "command": " ".join(cmd),
            "summary_paths": [],
            "details": {
                "stdout": "",
                "stderr": "",
                "note": "not executed in dry-run mode",
            },
        }

    if stage_name == "schedule":
        cmd = [
            sys.executable,
            script,
            "--source",
            SCHEDULE_SOURCE,
            "--schedule-out",
            SCHEDULE_OUT,
            "--events-dir",
            SCHEDULE_EVENTS_DIR,
            "--summary-json",
            SCHEDULE_SUMMARY_JSON,
            "--summary-csv",
            SCHEDULE_SUMMARY_CSV,
            "--formats",
            *args.formats,
        ]
        if args.dry_run:
            cmd.append("--dry-run")
    elif stage_name == "batch":
        cmd = [
            sys.executable,
            script,
            "--schedule",
            SCHEDULE_OUT,
            "--formats",
            *args.formats,
        ]
        if args.dry_run:
            dryrun_dir = "output/dry_run"
            os.makedirs(dryrun_dir, exist_ok=True)
            cmd.extend([
                "--dry-run",
                "--summary-json",
                f"{dryrun_dir}/event_batch_run_summary.json",
                "--summary-csv",
                f"{dryrun_dir}/event_batch_run_summary.csv",
            ])
            summary_paths = [
                f"{dryrun_dir}/event_batch_run_summary.json",
                f"{dryrun_dir}/event_batch_run_summary.csv",
            ]
    else:
        cmd = [sys.executable, script]
        if stage_name == "queue_run" and args.force_predictions:
            cmd.append("--force")

    proc = subprocess.run(cmd, cwd=os.getcwd(), capture_output=True, text=True)
    status = "success" if proc.returncode == 0 else ("failed" if args.strict else "warning")

    return {
        "stage": stage_name,
        "status": status,
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "exit_code": proc.returncode,
        "command": " ".join(cmd),
        "summary_paths": summary_paths,
        "details": {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        },
    }


def existing_paths(paths):
    return [p for p in paths if p and os.path.exists(p)]


def main():
    args = parse_args()
    verbose = args.verbose

    started_at = datetime.now().isoformat()
    summary = {
        "stage": "full_pipeline",
        "status": "success",
        "started_at": started_at,
        "finished_at": started_at,
        "counts": {},
        "warnings": [],
        "errors": [],
        "artifacts": [str(SUMMARY_PATH), str(SUMMARY_CSV_PATH)],
        "details": {
            "stages": [],
        },
    }

    exit_code = 0
    try:
        for stage_name, script, summary_paths in STAGES:
            stage_result = run_stage(stage_name, script, summary_paths, args)
            stage_result["summary_paths"] = existing_paths(stage_result.get("summary_paths", []))
            summary["details"]["stages"].append(stage_result)
            summary["artifacts"].extend(stage_result["summary_paths"])

            if stage_result["status"] == "soft_skip" and args.dry_run:
                summary["warnings"].append({
                    "stage": stage_name,
                    "type": "dry_run_soft_skip",
                    "detail": stage_result.get("details", {}).get("note", "not executed in dry-run mode"),
                })

            if stage_result["status"] == "warning":
                summary["warnings"].append({
                    "stage": stage_name,
                    "exit_code": stage_result["exit_code"],
                    "detail": (stage_result["details"].get("stderr") or stage_result["details"].get("stdout") or "").strip(),
                })
            if stage_result["status"] == "failed":
                summary["errors"].append({
                    "stage": stage_name,
                    "exit_code": stage_result["exit_code"],
                    "detail": (stage_result["details"].get("stderr") or stage_result["details"].get("stdout") or "").strip(),
                })
                exit_code = 1
                if args.strict:
                    break

            write_json(SUMMARY_PATH, summary)
            write_csv(SUMMARY_CSV_PATH, summary["details"]["stages"])

        stages = summary["details"]["stages"]
        summary["counts"] = {
            "stage_total": len(stages),
            "completed": sum(1 for s in stages if s["status"] == "success"),
            "warnings": sum(1 for s in stages if s["status"] == "warning"),
            "failed": sum(1 for s in stages if s["status"] == "failed"),
            "soft_skipped": sum(1 for s in stages if s["status"] == "soft_skip"),
            "stages_run": sum(1 for s in stages if s["status"] in {"success", "warning"}),
            "stages_soft_skipped": sum(1 for s in stages if s["status"] == "soft_skip"),
            "stages_failed": sum(1 for s in stages if s["status"] == "failed"),
        }
        if summary["errors"]:
            summary["status"] = "error"
            exit_code = 1
        elif args.dry_run:
            summary["status"] = "success"
        elif summary["warnings"]:
            summary["status"] = "warning"
        else:
            summary["status"] = "success"
    except Exception as exc:
        summary["status"] = "error"
        summary["errors"].append({"stage": "full_pipeline", "detail": str(exc)})
        exit_code = 1
    finally:
        summary["finished_at"] = datetime.now().isoformat()
        summary["artifacts"] = sorted(set(existing_paths(summary["artifacts"])))
        write_json(SUMMARY_PATH, summary)
        write_csv(SUMMARY_CSV_PATH, summary["details"]["stages"])
        log("[DONE] Full pipeline run summary written: {}, {}", SUMMARY_PATH, SUMMARY_CSV_PATH, always=True)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
