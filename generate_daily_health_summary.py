#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: daily health summary generator.

Read-only aggregator over canonical run history + run-folder summaries.
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
    choose_latest_run,
    iso,
    load_run_history,
    now_local,
    run_snapshot,
)

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")

HEALTH_JSON_NAME = "daily_health_summary.json"
HEALTH_MD_NAME = "daily_health_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate daily AI-RISA health summary")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--hours", type=int, default=24, help="Window size in hours (default: 24)")
    return parser.parse_args()


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
    if args.hours <= 0:
        print("ERROR: --hours must be > 0", file=sys.stderr)
        return 1

    try:
        runs = load_run_history(repo_root)
    except Exception as exc:
        print(f"ERROR: unable to read run index: {exc}", file=sys.stderr)
        return 1

    window_end = now_local()
    window_start = window_end - timedelta(hours=args.hours)

    payload = aggregate_window(runs, window_start, window_end)
    payload["generated_at"] = iso(now_local())
    payload["latest_run"] = run_snapshot(choose_latest_run(runs))
    payload["notes"] = payload.pop("data_quality_notes", [])

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
