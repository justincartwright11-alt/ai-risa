#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: operator summary artifact generator.

Fast-read operator artifact derived from canonical run history and slice-1 alert state.
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
ALERT_JSON = Path("ops/alerts/latest_run_alert.json")
SUMMARY_JSON = "operator_summary.json"
SUMMARY_MD = "operator_summary.md"

HEALTHY_MIN_WEEKLY_RATE = 0.90
WATCH_MIN_WEEKLY_RATE = 0.75
DECLINE_WATCH_DELTA = -0.05


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate operator-facing summary artifact")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--daily-hours", type=int, default=24)
    parser.add_argument("--weekly-days", type=int, default=7)
    return parser.parse_args()


def load_alert_state(repo_root: Path) -> dict[str, Any]:
    path = repo_root / ALERT_JSON
    if not path.exists():
        return {
            "generated_at": None,
            "alert": None,
            "reason_codes": ["alert_artifact_missing"],
            "message": "Alert artifact not found.",
        }

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {
        "generated_at": None,
        "alert": None,
        "reason_codes": ["alert_artifact_unreadable"],
        "message": "Alert artifact unreadable.",
    }


def classify_status(
    alert_state: dict[str, Any],
    daily: dict[str, Any],
    weekly: dict[str, Any],
    trend_delta: float | None,
) -> tuple[str, str]:
    active_alert = bool(alert_state.get("alert"))
    weekly_rate = float(weekly["run_counts"]["success_rate"])
    daily_failed = int(daily["run_counts"]["failed"])

    if active_alert or weekly_rate < WATCH_MIN_WEEKLY_RATE:
        return (
            "degraded",
            "Inspect latest run alert and failed stage summaries immediately.",
        )

    if daily_failed > 0 or weekly_rate < HEALTHY_MIN_WEEKLY_RATE or (
        trend_delta is not None and trend_delta <= DECLINE_WATCH_DELTA
    ):
        return (
            "watch",
            "Review recent failures and trend decline; inspect latest logs and stage summaries.",
        )

    return ("healthy", "No immediate action required.")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AI-RISA Operator Summary",
        "",
        f"Generated at: {payload.get('generated_at')}",
        f"Overall Health Status: {payload.get('overall_health_status')}",
        "",
        "## Latest Run Snapshot",
        f"- Run ID: {payload.get('latest_run_snapshot', {}).get('run_id')}",
        f"- Status: {payload.get('latest_run_snapshot', {}).get('status')}",
        f"- Exit Code: {payload.get('latest_run_snapshot', {}).get('exit_code')}",
        f"- Path: {payload.get('latest_run_snapshot', {}).get('path')}",
        "",
        "## Daily KPI Snapshot",
        f"- Total Runs (24h): {payload.get('daily_kpi', {}).get('run_counts', {}).get('total')}",
        f"- Success: {payload.get('daily_kpi', {}).get('run_counts', {}).get('success')}",
        f"- Failed: {payload.get('daily_kpi', {}).get('run_counts', {}).get('failed')}",
        f"- Success Rate: {payload.get('daily_kpi', {}).get('run_counts', {}).get('success_rate')}",
        "",
        "## Weekly KPI Snapshot",
        f"- Total Runs (7d): {payload.get('weekly_kpi', {}).get('run_counts', {}).get('total')}",
        f"- Success: {payload.get('weekly_kpi', {}).get('run_counts', {}).get('success')}",
        f"- Failed: {payload.get('weekly_kpi', {}).get('run_counts', {}).get('failed')}",
        f"- Success Rate: {payload.get('weekly_kpi', {}).get('run_counts', {}).get('success_rate')}",
        f"- Previous Success Rate: {payload.get('weekly_kpi', {}).get('previous_success_rate')}",
        f"- Delta: {payload.get('weekly_kpi', {}).get('delta_success_rate')}",
        "",
        "## Active Alert State",
        f"- Alert Active: {payload.get('active_alert_state', {}).get('alert')}",
        f"- Reason Codes: {', '.join(payload.get('active_alert_state', {}).get('reason_codes') or []) or 'none'}",
        f"- Message: {payload.get('active_alert_state', {}).get('message')}",
        "",
        "## Recent Failures",
    ]

    failures = payload.get("recent_failures", [])
    if failures:
        for row in failures:
            lines.append(
                f"- {row.get('run_id')}: status={row.get('status')} exit_code={row.get('exit_code')} reasons={','.join(row.get('reason_codes') or []) or 'none'}"
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Recommended Operator Action",
        f"- {payload.get('recommended_operator_action')}",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    if args.daily_hours <= 0 or args.weekly_days <= 0:
        print("ERROR: --daily-hours and --weekly-days must be > 0", file=sys.stderr)
        return 1

    try:
        runs = load_run_history(repo_root)
    except Exception as exc:
        print(f"ERROR: unable to read run index: {exc}", file=sys.stderr)
        return 1

    now = now_local()

    daily_end = now
    daily_start = daily_end - timedelta(hours=args.daily_hours)
    daily = aggregate_window(runs, daily_start, daily_end)

    weekly_end = now
    weekly_start = weekly_end - timedelta(days=args.weekly_days)
    previous_end = weekly_start
    previous_start = previous_end - timedelta(days=args.weekly_days)
    weekly = aggregate_window(runs, weekly_start, weekly_end)
    previous = aggregate_window(runs, previous_start, previous_end)

    prev_total = previous["run_counts"]["total"]
    previous_rate = previous["run_counts"]["success_rate"] if prev_total > 0 else None
    delta = (
        round(weekly["run_counts"]["success_rate"] - previous_rate, 4)
        if previous_rate is not None
        else None
    )

    alert_state = load_alert_state(repo_root)
    status, recommended_action = classify_status(alert_state, daily, weekly, delta)

    payload: dict[str, Any] = {
        "generated_at": iso(now_local()),
        "overall_health_status": status,
        "latest_run_snapshot": run_snapshot(choose_latest_run(runs)),
        "daily_kpi": {
            "window": daily["window"],
            "run_counts": daily["run_counts"],
        },
        "weekly_kpi": {
            "window": weekly["window"],
            "run_counts": weekly["run_counts"],
            "previous_success_rate": previous_rate,
            "delta_success_rate": delta,
        },
        "recent_failures": daily.get("failed_runs", [])[:10],
        "active_alert_state": {
            "generated_at": alert_state.get("generated_at"),
            "alert": alert_state.get("alert"),
            "reason_codes": alert_state.get("reason_codes", []),
            "message": alert_state.get("message"),
        },
        "recommended_operator_action": recommended_action,
        "thresholds": {
            "healthy_min_weekly_success_rate": HEALTHY_MIN_WEEKLY_RATE,
            "watch_min_weekly_success_rate": WATCH_MIN_WEEKLY_RATE,
            "watch_decline_delta": DECLINE_WATCH_DELTA,
        },
    }

    summary_dir = repo_root / "ops" / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    json_path = summary_dir / SUMMARY_JSON
    md_path = summary_dir / SUMMARY_MD

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {json_path}")
    print(f"[WRITE] {md_path}")
    print(
        f"[STATUS] health={payload['overall_health_status']} alert={payload['active_alert_state']['alert']} daily_failed={payload['daily_kpi']['run_counts']['failed']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
