#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: operator checklist artifact generator.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate operator checklist artifacts")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--period",
        choices=["daily", "weekly", "both"],
        default="both",
        help="Which checklist artifact(s) to generate",
    )
    return parser.parse_args()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def checkbox(ok: bool) -> str:
    return "[x]" if ok else "[ ]"


def latest_run_ok(run_index: Any) -> tuple[bool, str]:
    if not isinstance(run_index, list) or not run_index:
        return False, "No run-history entries available."

    latest = run_index[-1]
    try:
        status_ok = str(latest.get("status", "")).lower() == "success"
        exit_ok = int(latest.get("exit_code", 1)) == 0
    except Exception:
        return False, "Latest run status/exit code malformed."

    if status_ok and exit_ok:
        return True, f"Latest run {latest.get('timestamp')} succeeded."
    return False, f"Latest run {latest.get('timestamp')} status={latest.get('status')} exit={latest.get('exit_code')}."


def render_checklist(
    title: str,
    latest_ok: tuple[bool, str],
    alert_state: dict[str, Any],
    daily: dict[str, Any],
    weekly: dict[str, Any],
    verification: dict[str, Any],
    operator_summary: dict[str, Any],
    period: str,
) -> str:
    alert_exists = isinstance(alert_state, dict) and "alert" in alert_state
    daily_ok = isinstance(daily, dict) and isinstance(daily.get("run_counts"), dict)
    weekly_ok = isinstance(weekly, dict) and isinstance(weekly.get("run_counts"), dict)

    verification_status = str(verification.get("overall_status", "")).lower() if isinstance(verification, dict) else ""
    verification_ok = verification_status == "pass"

    failed_recent = 0
    if period == "daily" and daily_ok:
        failed_recent = int(daily.get("run_counts", {}).get("failed", 0))
    elif period == "weekly" and weekly_ok:
        failed_recent = int(weekly.get("run_counts", {}).get("failed", 0))

    failures_reviewed_ok = failed_recent == 0

    run_index_health = isinstance(operator_summary, dict) and isinstance(operator_summary.get("latest_run_snapshot"), dict)

    recommended_action = (
        operator_summary.get("recommended_operator_action")
        if isinstance(operator_summary, dict)
        else None
    ) or "Inspect latest alert, verification, and health artifacts."

    lines = [
        f"# {title}",
        "",
        f"{checkbox(latest_ok[0])} Latest run succeeded",
        f"- {latest_ok[1]}",
        f"{checkbox(alert_exists)} Active alert state reviewed",
        f"- Alert active: {alert_state.get('alert') if isinstance(alert_state, dict) else 'unknown'}",
        f"{checkbox(daily_ok)} Daily summary generated",
        f"- Path: ops/health/daily_health_summary.json",
        f"{checkbox(weekly_ok)} Weekly rollup generated",
        f"- Path: ops/health/weekly_health_rollup.json",
        f"{checkbox(verification_ok)} Scheduler verification passed",
        f"- Status: {verification.get('overall_status') if isinstance(verification, dict) else 'unknown'}",
        f"{checkbox(failures_reviewed_ok)} Failed runs reviewed",
        f"- {period.title()} failed run count: {failed_recent}",
        f"{checkbox(run_index_health)} Retention/run-history health reviewed",
        f"- Run index and latest run snapshot are readable.",
        "",
        "## Next Operator Action",
        f"- {recommended_action}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    run_index = read_json(repo_root / "runs" / "run_history_index.json", default=[])
    alert_state = read_json(repo_root / "ops" / "alerts" / "latest_run_alert.json", default={})
    daily = read_json(repo_root / "ops" / "health" / "daily_health_summary.json", default={})
    weekly = read_json(repo_root / "ops" / "health" / "weekly_health_rollup.json", default={})
    verification = read_json(repo_root / "ops" / "verification" / "scheduler_verification.json", default={})
    operator_summary = read_json(repo_root / "ops" / "summary" / "operator_summary.json", default={})

    latest_ok = latest_run_ok(run_index)

    checklists_dir = repo_root / "ops" / "checklists"
    checklists_dir.mkdir(parents=True, exist_ok=True)

    if args.period in ("daily", "both"):
        daily_md = render_checklist(
            "AI-RISA Operator Checklist (Daily)",
            latest_ok,
            alert_state,
            daily,
            weekly,
            verification,
            operator_summary,
            "daily",
        )
        out_daily = checklists_dir / "operator_checklist_daily.md"
        out_daily.write_text(daily_md, encoding="utf-8")
        print(f"[WRITE] {out_daily}")

    if args.period in ("weekly", "both"):
        weekly_md = render_checklist(
            "AI-RISA Operator Checklist (Weekly)",
            latest_ok,
            alert_state,
            daily,
            weekly,
            verification,
            operator_summary,
            "weekly",
        )
        out_weekly = checklists_dir / "operator_checklist_weekly.md"
        out_weekly.write_text(weekly_md, encoding="utf-8")
        print(f"[WRITE] {out_weekly}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
