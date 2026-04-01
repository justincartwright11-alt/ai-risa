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
            "summary_paths": summary_paths,
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


def load_stage_summary_json(summary_paths):
    for path in summary_paths or []:
        if str(path).lower().endswith(".json") and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                if isinstance(payload, dict):
                    return payload
            except Exception:
                continue
    return None


def propagate_enrichment_diagnostics(summary, stage_name, stage_payload):
    if not isinstance(stage_payload, dict):
        return
    counts = stage_payload.get("counts", {})
    if not isinstance(counts, dict):
        return

    details = summary.setdefault("details", {})
    diag = details.setdefault("enrichment_diagnostics", {})

    if stage_name == "resolver":
        resolver_counts = {
            "unresolved_missing_fighters": int(counts.get("unresolved_missing_fighters", 0) or 0),
            "unresolved_partial_fighters": int(counts.get("unresolved_partial_fighters", 0) or 0),
            "insufficient_enrichment": int(counts.get("insufficient_enrichment", 0) or 0),
            "skipped_tba": int(counts.get("skipped_tba", 0) or 0),
        }
        diag["resolver"] = resolver_counts
        summary.setdefault("counts", {})["resolver_unresolved_missing_fighters"] = resolver_counts["unresolved_missing_fighters"]
        summary.setdefault("counts", {})["resolver_unresolved_partial_fighters"] = resolver_counts["unresolved_partial_fighters"]
        summary.setdefault("counts", {})["resolver_insufficient_enrichment"] = resolver_counts["insufficient_enrichment"]

    if stage_name == "queue_build":
        queue_counts = {
            "excluded_unresolved_fighter_identity": int(counts.get("excluded_unresolved_fighter_identity", 0) or 0),
            "excluded_partial_fighter_identity": int(counts.get("excluded_partial_fighter_identity", 0) or 0),
            "excluded_unresolved_matchup_mapping": int(counts.get("excluded_unresolved_matchup_mapping", 0) or 0),
            "excluded_insufficient_enrichment": int(counts.get("excluded_insufficient_enrichment", 0) or 0),
        }
        diag["queue_build"] = queue_counts
        summary.setdefault("counts", {})["queue_excluded_unresolved_fighter_identity"] = queue_counts["excluded_unresolved_fighter_identity"]
        summary.setdefault("counts", {})["queue_excluded_partial_fighter_identity"] = queue_counts["excluded_partial_fighter_identity"]
        summary.setdefault("counts", {})["queue_excluded_unresolved_matchup_mapping"] = queue_counts["excluded_unresolved_matchup_mapping"]
        summary.setdefault("counts", {})["queue_excluded_insufficient_enrichment"] = queue_counts["excluded_insufficient_enrichment"]

    # Add operator-facing warnings only when non-zero to avoid noisy summaries.
    for reason, count in (diag.get(stage_name, {}) or {}).items():
        if count > 0:
            summary.setdefault("warnings", []).append(
                {
                    "stage": stage_name,
                    "type": "enrichment_diagnostic",
                    "reason": reason,
                    "count": count,
                    "message": f"{stage_name} reported {count} item(s) for enrichment diagnostic '{reason}'.",
                }
            )


def classify_warning_readability(warning):
    wtype = warning.get("type")
    reason = warning.get("reason")
    if wtype == "dry_run_soft_skip":
        return "informational"
    if wtype == "enrichment_diagnostic":
        if reason == "skipped_tba":
            return "non_fatal_operational"
        return "action_needed"
    if "exit_code" in warning:
        return "action_needed"
    return "non_fatal_operational"


def add_reporting_clarity_blocks(summary):
    details = summary.setdefault("details", {})
    stages = details.get("stages", [])
    warnings = summary.get("warnings", [])
    errors = summary.get("errors", [])

    analyzed_stages = [s.get("stage") for s in stages if s.get("status") in {"success", "warning", "failed"}]
    skipped_stages = [s.get("stage") for s in stages if s.get("status") == "soft_skip"]

    warning_type_counts = {}
    for warning in warnings:
        wtype = warning.get("type") or "unspecified"
        warning_type_counts[wtype] = warning_type_counts.get(wtype, 0) + 1

    enrichment_diag = details.get("enrichment_diagnostics", {}) if isinstance(details.get("enrichment_diagnostics"), dict) else {}
    enrichment_rollup = {}
    for stage_name, stage_diag in enrichment_diag.items():
        if not isinstance(stage_diag, dict):
            continue
        for reason, count in stage_diag.items():
            n = int(count or 0)
            if n > 0:
                key = f"{stage_name}:{reason}"
                enrichment_rollup[key] = n

    details["analysis_coverage"] = {
        "stages_total": len(stages),
        "stages_analyzed": len(analyzed_stages),
        "stages_soft_skipped": len(skipped_stages),
        "analyzed_stage_names": analyzed_stages,
        "skipped_stage_names": skipped_stages,
    }
    details["skipped_items_exclusions"] = {
        "warning_type_counts": warning_type_counts,
        "enrichment_reason_rollup": enrichment_rollup,
    }

    informational = []
    non_fatal_operational = []
    action_needed = []
    for warning in warnings:
        classification = classify_warning_readability(warning)
        bucket_entry = {
            "type": warning.get("type"),
            "stage": warning.get("stage"),
            "reason": warning.get("reason"),
            "count": warning.get("count"),
            "message": warning.get("message") or warning.get("detail") or "No detail provided.",
        }
        if classification == "informational":
            informational.append(bucket_entry)
        elif classification == "action_needed":
            action_needed.append(bucket_entry)
        else:
            non_fatal_operational.append(bucket_entry)

    details["warning_readability"] = {
        "informational_count": len(informational),
        "non_fatal_operational_count": len(non_fatal_operational),
        "action_needed_count": len(action_needed),
        "informational_examples": informational[:5],
        "non_fatal_operational_examples": non_fatal_operational[:5],
        "action_needed_examples": action_needed[:5],
    }

    if errors:
        interpretation = "Run contains hard failures. Review errors before consuming downstream outputs."
    elif summary.get("status") == "success" and summary.get("warnings") and summary.get("counts", {}).get("soft_skipped", 0) > 0:
        interpretation = "Dry-run completed. Warnings are expected soft-skip notices and coverage indicators, not execution failures."
    elif warnings:
        interpretation = "Run completed with non-fatal warnings. Outputs are usable with documented coverage/exclusion limits."
    else:
        interpretation = "Run completed without warnings. Coverage is complete for executed stages."
    details["operator_interpretation"] = {
        "note": interpretation,
        "warning_non_fatal": bool(warnings and not errors),
    }

    warning_readability = details.get("warning_readability", {}) if isinstance(details.get("warning_readability"), dict) else {}
    action_needed_count = int(warning_readability.get("action_needed_count", 0) or 0)
    non_fatal_count = int(warning_readability.get("non_fatal_operational_count", 0) or 0)
    informational_count = int(warning_readability.get("informational_count", 0) or 0)

    if errors or action_needed_count > 0:
        recommended_action = "Review stage errors and action-needed warnings first; then re-run bounded validation."
    elif warnings:
        recommended_action = "Proceed with outputs while monitoring documented exclusions and non-fatal warning trends."
    else:
        recommended_action = "No immediate action required. Continue normal operations."

    lines = [
        "# Executive Summary",
        f"- Run Status: {summary.get('status')}",
        f"- Stages Run: {details['analysis_coverage'].get('stages_analyzed', 0)}/{details['analysis_coverage'].get('stages_total', 0)}",
        f"- Stages Soft-Skipped: {details['analysis_coverage'].get('stages_soft_skipped', 0)}",
        "",
        "# Analysis Coverage Snapshot",
        f"- Executed Stages: {', '.join(details['analysis_coverage'].get('analyzed_stage_names', [])) or 'None'}",
        f"- Soft-Skipped Stages: {', '.join(details['analysis_coverage'].get('skipped_stage_names', [])) or 'None'}",
        "",
        "# Skipped/Excluded Items Snapshot",
        f"- Warning Types: {details['skipped_items_exclusions'].get('warning_type_counts', {})}",
        f"- Enrichment Exclusions: {details['skipped_items_exclusions'].get('enrichment_reason_rollup', {})}",
        "",
        "# Warning Interpretation",
        f"- Informational: {informational_count}",
        f"- Non-Fatal Operational: {non_fatal_count}",
        f"- Action-Needed: {action_needed_count}",
        f"- Interpretation: {details['operator_interpretation'].get('note')}",
        "",
        "# Recommended Operator Action",
        f"- {recommended_action}",
    ]
    details["human_readable_summary_markdown"] = "\n".join(lines)


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

            stage_summary_payload = load_stage_summary_json(stage_result["summary_paths"])
            if stage_summary_payload and stage_name in {"resolver", "queue_build"}:
                propagate_enrichment_diagnostics(summary, stage_name, stage_summary_payload)

            summary["details"]["stages"].append(stage_result)
            summary["artifacts"].extend(stage_result["summary_paths"])

            if stage_result["status"] == "soft_skip" and args.dry_run:
                summary["warnings"].append({
                    "stage": stage_name,
                    "type": "dry_run_soft_skip",
                    "detail": stage_result.get("details", {}).get("note", "not executed in dry-run mode"),
                    "message": f"Stage '{stage_name}' was skipped by dry-run policy; this is informational.",
                })

            if stage_result["status"] == "warning":
                summary["warnings"].append({
                    "stage": stage_name,
                    "exit_code": stage_result["exit_code"],
                    "detail": (stage_result["details"].get("stderr") or stage_result["details"].get("stdout") or "").strip(),
                    "message": f"Stage '{stage_name}' completed with warning (exit_code={stage_result['exit_code']}). Review detail for actionability.",
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

        enrichment_diag = summary.get("details", {}).get("enrichment_diagnostics", {})
        resolver_diag = enrichment_diag.get("resolver", {}) if isinstance(enrichment_diag, dict) else {}
        queue_diag = enrichment_diag.get("queue_build", {}) if isinstance(enrichment_diag, dict) else {}
        summary["counts"].update(
            {
                "resolver_unresolved_missing_fighters": int(resolver_diag.get("unresolved_missing_fighters", 0) or 0),
                "resolver_unresolved_partial_fighters": int(resolver_diag.get("unresolved_partial_fighters", 0) or 0),
                "resolver_insufficient_enrichment": int(resolver_diag.get("insufficient_enrichment", 0) or 0),
                "queue_excluded_unresolved_fighter_identity": int(queue_diag.get("excluded_unresolved_fighter_identity", 0) or 0),
                "queue_excluded_partial_fighter_identity": int(queue_diag.get("excluded_partial_fighter_identity", 0) or 0),
                "queue_excluded_unresolved_matchup_mapping": int(queue_diag.get("excluded_unresolved_matchup_mapping", 0) or 0),
                "queue_excluded_insufficient_enrichment": int(queue_diag.get("excluded_insufficient_enrichment", 0) or 0),
            }
        )
        add_reporting_clarity_blocks(summary)
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
