#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: daily health summary generator.

Read-only aggregator over canonical run history + run-folder summaries.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
RUNS_DIR_NAME = "runs"
RUN_INDEX_NAME = "run_history_index.json"

HEALTH_JSON_NAME = "daily_health_summary.json"
HEALTH_MD_NAME = "daily_health_summary.md"

FULL_SUMMARY_NAME = "full_pipeline_run_summary.json"
SUCCESS_STATUSES = {"success"}
NON_ALERT_STAGE_STATUSES = {"success", "soft_skip"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate daily AI-RISA health summary")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--hours", type=int, default=24, help="Window size in hours (default: 24)")
    return parser.parse_args()


def now_local() -> datetime:
    return datetime.now().astimezone()


def iso(dt: datetime) -> str:
    return dt.astimezone().isoformat()


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d_%H%M%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def normalize_runs(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_datetime(record: dict[str, Any]) -> datetime | None:
    return (
        parse_timestamp(record.get("completed_at"))
        or parse_timestamp(record.get("started_at"))
        or parse_timestamp(record.get("timestamp"))
    )


def choose_latest_run(runs: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    decorated: list[tuple[datetime, dict[str, Any]]] = []
    for run in runs:
        dt = run_datetime(run) or datetime.min
        decorated.append((dt, run))
    if not decorated:
        return None
    decorated.sort(key=lambda x: x[0], reverse=True)
    return decorated[0][1]


def is_failed_run(record: dict[str, Any]) -> bool:
    status = str(record.get("status", "")).strip().lower()
    try:
        exit_code = int(record.get("exit_code", 0))
    except Exception:
        exit_code = 1
    return exit_code != 0 or status not in SUCCESS_STATUSES


def derive_failure_details(record: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """
    Returns tuple: (reason_codes, failed_stage_names, notes)
    """
    reason_codes: list[str] = []
    failed_stages: list[str] = []
    notes: list[str] = []

    status = str(record.get("status", "")).strip().lower()
    try:
        exit_code = int(record.get("exit_code", 0))
    except Exception:
        exit_code = 1
        reason_codes.append("malformed_summary")

    if exit_code != 0:
        reason_codes.append("non_zero_exit")
    if status not in SUCCESS_STATUSES:
        reason_codes.append("run_status_failed")

    run_path_value = record.get("run_path")
    if not run_path_value:
        reason_codes.append("missing_run_summary")
        return sorted(set(reason_codes)), failed_stages, notes

    run_path = Path(str(run_path_value))
    summary_path = run_path / FULL_SUMMARY_NAME
    if not summary_path.exists():
        reason_codes.append("missing_run_summary")
        return sorted(set(reason_codes)), failed_stages, notes

    try:
        summary = load_json(summary_path)
    except Exception:
        reason_codes.append("malformed_summary")
        return sorted(set(reason_codes)), failed_stages, notes

    details = summary.get("details", {}) if isinstance(summary, dict) else {}
    stages = details.get("stages", []) if isinstance(details, dict) else []

    if not isinstance(stages, list):
        reason_codes.append("malformed_summary")
        return sorted(set(reason_codes)), failed_stages, notes

    for stage in stages:
        if not isinstance(stage, dict):
            reason_codes.append("malformed_summary")
            continue
        stage_name = str(stage.get("stage", "unknown"))
        stage_status = str(stage.get("status", "")).strip().lower()
        if stage_status and stage_status not in NON_ALERT_STAGE_STATUSES:
            failed_stages.append(stage_name)

    if failed_stages:
        reason_codes.append("stage_failed")

    return sorted(set(reason_codes)), sorted(set(failed_stages)), notes


def aggregate_window(
    runs: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []

    window_runs: list[dict[str, Any]] = []
    for run in runs:
        dt = run_datetime(run)
        if dt is None:
            notes.append(
                f"Run entry missing parseable timestamp: {run.get('timestamp', 'unknown')}"
            )
            continue
        if window_start <= dt <= window_end:
            window_runs.append(run)

    total = len(window_runs)
    success = sum(1 for r in window_runs if not is_failed_run(r))
    failed = total - success
    success_rate = (success / total) if total else 0.0

    latest = choose_latest_run(runs)
    latest_payload = {
        "run_id": latest.get("timestamp") if latest else None,
        "status": latest.get("status") if latest else None,
        "exit_code": latest.get("exit_code") if latest else None,
        "path": latest.get("run_path") if latest else None,
        "timestamp": (latest.get("completed_at") or latest.get("started_at") or latest.get("timestamp")) if latest else None,
    }

    failed_runs_payload: list[dict[str, Any]] = []
    stage_failure_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()

    for run in window_runs:
        if not is_failed_run(run):
            continue
        reason_codes, failed_stages, more_notes = derive_failure_details(run)
        notes.extend(more_notes)
        reason_counts.update(reason_codes)
        stage_failure_counts.update(failed_stages)

        failed_runs_payload.append(
            {
                "run_id": run.get("timestamp"),
                "status": run.get("status"),
                "exit_code": run.get("exit_code"),
                "reason_codes": reason_codes,
            }
        )

    payload = {
        "generated_at": iso(now_local()),
        "window": {
            "start": iso(window_start),
            "end": iso(window_end),
        },
        "run_counts": {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": round(success_rate, 4),
        },
        "latest_run": latest_payload,
        "failed_runs": failed_runs_payload,
        "stage_failure_counts": dict(sorted(stage_failure_counts.items())),
        "failure_reason_counts": dict(sorted(reason_counts.items())),
        "notes": sorted(set(notes)),
    }

    return payload, notes


def render_markdown(payload: dict[str, Any]) -> str:
    run_counts = payload.get("run_counts", {})
    latest = payload.get("latest_run", {})
    failed_runs = payload.get("failed_runs", [])
    stage_failures = payload.get("stage_failure_counts", {})
    reason_counts = payload.get("failure_reason_counts", {})

    lines = [
        "# AI-RISA Daily Health Summary",
        "",
        f"Generated at: {payload.get('generated_at')}",
        f"Window: {payload.get('window', {}).get('start')} to {payload.get('window', {}).get('end')}",
        "",
        "## KPI",
        f"- Total Runs: {run_counts.get('total', 0)}",
        f"- Successful Runs: {run_counts.get('success', 0)}",
        f"- Failed Runs: {run_counts.get('failed', 0)}",
        f"- Success Rate: {run_counts.get('success_rate', 0.0):.2%}",
        "",
        "## Latest Run",
        f"- Run ID: {latest.get('run_id')}",
        f"- Status: {latest.get('status')}",
        f"- Exit Code: {latest.get('exit_code')}",
        f"- Path: {latest.get('path')}",
        f"- Timestamp: {latest.get('timestamp')}",
        "",
        "## Failed Runs",
    ]

    if failed_runs:
        for run in failed_runs:
            lines.append(
                f"- {run.get('run_id')}: status={run.get('status')} exit_code={run.get('exit_code')} reasons={','.join(run.get('reason_codes') or []) or 'none'}"
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Stage Failure Counts",
    ])

    if stage_failures:
        for stage, count in stage_failures.items():
            lines.append(f"- {stage}: {count}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Failure Reason Counts",
    ])

    if reason_counts:
        for reason, count in reason_counts.items():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Operator Notes",
    ])

    notes = payload.get("notes", [])
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("- No missing or incomplete records detected.")

    lines.append("")
    return "\n".join(lines)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)
    runs_dir = repo_root / RUNS_DIR_NAME
    index_path = runs_dir / RUN_INDEX_NAME

    if args.hours <= 0:
        print("ERROR: --hours must be > 0", file=sys.stderr)
        return 1

    try:
        raw_index = load_json(index_path)
        runs = normalize_runs(raw_index)
    except Exception as exc:
        print(f"ERROR: unable to read run index: {exc}", file=sys.stderr)
        return 1

    window_end = now_local()
    window_start = window_end - timedelta(hours=args.hours)

    payload, _notes = aggregate_window(runs, window_start, window_end)

    health_dir = repo_root / "ops" / "health"
    ensure_dir(health_dir)
    json_path = health_dir / HEALTH_JSON_NAME
    md_path = health_dir / HEALTH_MD_NAME

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {json_path}")
    print(f"[WRITE] {md_path}")
    print(f"[STATUS] total={payload['run_counts']['total']} success={payload['run_counts']['success']} failed={payload['run_counts']['failed']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
