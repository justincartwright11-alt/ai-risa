#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: weekly health rollup generator.

Read-only rollup over canonical run history + run-folder summaries.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

from ops_visibility_aggregation import (
    aggregate_window,
    choose_latest_failed_run,
    choose_latest_successful_run,
    iso,
    load_run_history,
    now_local,
    run_snapshot,
)

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
WEEKLY_JSON_NAME = "weekly_health_rollup.json"
WEEKLY_MD_NAME = "weekly_health_rollup.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly AI-RISA health rollup")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--days", type=int, default=7, help="Window size in days (default: 7)")
    return parser.parse_args()


def render_markdown(payload: dict[str, Any]) -> str:
    rc = payload.get("run_counts", {})
    trend = payload.get("trend", {})

    lines = [
        "# AI-RISA Weekly Health Rollup",
        "",
        f"Generated at: {payload.get('generated_at')}",
        f"Window: {payload.get('window', {}).get('start')} to {payload.get('window', {}).get('end')}",
        f"Previous Window: {payload.get('previous_window', {}).get('start')} to {payload.get('previous_window', {}).get('end')}",
        "",
        "## KPI",
        f"- Total Runs: {rc.get('total', 0)}",
        f"- Successful Runs: {rc.get('success', 0)}",
        f"- Failed Runs: {rc.get('failed', 0)}",
        f"- Success Rate: {rc.get('success_rate', 0.0):.2%}",
        f"- Previous Success Rate: {trend.get('previous_success_rate')}",
        f"- Delta vs Previous: {trend.get('delta_success_rate')}",
        "",
        "## Latest Successful Run",
        f"- Run ID: {payload.get('latest_successful_run', {}).get('run_id')}",
        f"- Status: {payload.get('latest_successful_run', {}).get('status')}",
        f"- Exit Code: {payload.get('latest_successful_run', {}).get('exit_code')}",
        f"- Path: {payload.get('latest_successful_run', {}).get('path')}",
        "",
        "## Latest Failed Run",
        f"- Run ID: {payload.get('latest_failed_run', {}).get('run_id')}",
        f"- Status: {payload.get('latest_failed_run', {}).get('status')}",
        f"- Exit Code: {payload.get('latest_failed_run', {}).get('exit_code')}",
        f"- Path: {payload.get('latest_failed_run', {}).get('path')}",
        "",
        "## Failure Reason Counts",
    ]

    reason_counts = payload.get("failure_reason_counts", {})
    if reason_counts:
        for reason, count in reason_counts.items():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Stage Failure Counts"])
    stage_counts = payload.get("stage_failure_counts", {})
    if stage_counts:
        for stage, count in stage_counts.items():
            lines.append(f"- {stage}: {count}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Trend Note",
        f"- {trend.get('trend_note')}",
        "",
        "## Data Quality Notes",
    ])

    notes = payload.get("data_quality_notes", [])
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("- No missing or incomplete records detected.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    if args.days <= 0:
        print("ERROR: --days must be > 0", file=sys.stderr)
        return 1

    try:
        runs = load_run_history(repo_root)
    except Exception as exc:
        print(f"ERROR: unable to read run index: {exc}", file=sys.stderr)
        return 1

    now = now_local()
    window_end = now
    window_start = window_end - timedelta(days=args.days)
    previous_end = window_start
    previous_start = previous_end - timedelta(days=args.days)

    current = aggregate_window(runs, window_start, window_end)
    previous = aggregate_window(runs, previous_start, previous_end)

    current_rate = current["run_counts"]["success_rate"]
    previous_total = previous["run_counts"]["total"]
    previous_rate = previous["run_counts"]["success_rate"] if previous_total > 0 else None
    delta = round(current_rate - previous_rate, 4) if previous_rate is not None else None

    if previous_rate is None:
        trend_note = "No prior-window runs available; delta is null by design."
    elif delta >= 0.05:
        trend_note = "Success trend improving versus previous window."
    elif delta <= -0.05:
        trend_note = "Success trend declining versus previous window."
    else:
        trend_note = "Success trend stable versus previous window."

    payload: dict[str, Any] = {
        "generated_at": iso(now_local()),
        "window": current["window"],
        "previous_window": previous["window"],
        "run_counts": current["run_counts"],
        "latest_successful_run": run_snapshot(choose_latest_successful_run(runs)),
        "latest_failed_run": run_snapshot(choose_latest_failed_run(runs)),
        "failure_reason_counts": current["failure_reason_counts"],
        "stage_failure_counts": current["stage_failure_counts"],
        "trend": {
            "previous_success_rate": previous_rate,
            "delta_success_rate": delta,
            "trend_note": trend_note,
        },
        "data_quality_notes": sorted(
            set(current.get("data_quality_notes", []) + previous.get("data_quality_notes", []))
        ),
    }

    health_dir = repo_root / "ops" / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    json_path = health_dir / WEEKLY_JSON_NAME
    md_path = health_dir / WEEKLY_MD_NAME

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {json_path}")
    print(f"[WRITE] {md_path}")
    print(
        f"[STATUS] total={payload['run_counts']['total']} success={payload['run_counts']['success']} failed={payload['run_counts']['failed']} delta={payload['trend']['delta_success_rate']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
