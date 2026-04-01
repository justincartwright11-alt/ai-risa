#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: latest run alert check.

Read-only checker that evaluates the newest canonical run-history entry and
its run folder summaries to determine whether an operator alert is required.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
RUNS_DIR_NAME = "runs"
RUN_INDEX_NAME = "run_history_index.json"

ALERT_JSON_NAME = "latest_run_alert.json"
ALERT_MD_NAME = "latest_run_alert.md"

FULL_SUMMARY_NAME = "full_pipeline_run_summary.json"
REQUIRED_STAGE_SUMMARIES = [
    "upcoming_events_ingest_summary.json",
    "upcoming_auto_summary.json",
    "dependency_resolution_summary.json",
    "prediction_queue_build_summary.json",
    "prediction_queue_run_summary.json",
    "event_batch_run_summary.json",
]

SUCCESS_STATUSES = {"success"}
NON_ALERT_STAGE_STATUSES = {"success", "soft_skip"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check latest run and emit alert artifacts")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


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


def choose_latest_run(runs: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    decorated: list[tuple[datetime, dict[str, Any]]] = []
    for run in runs:
        dt = (
            parse_timestamp(run.get("started_at"))
            or parse_timestamp(run.get("completed_at"))
            or parse_timestamp(run.get("timestamp"))
        )
        if dt is None:
            dt = datetime.min
        decorated.append((dt, run))

    if not decorated:
        return None
    decorated.sort(key=lambda x: x[0], reverse=True)
    return decorated[0][1]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def evaluate_latest_run(repo_root: Path) -> dict[str, Any]:
    runs_dir = repo_root / RUNS_DIR_NAME
    index_path = runs_dir / RUN_INDEX_NAME

    payload: dict[str, Any] = {
        "generated_at": now_iso(),
        "alert": False,
        "severity": "none",
        "reason_codes": [],
        "latest_run_id": None,
        "latest_run_path": None,
        "latest_run_timestamp": None,
        "latest_run_status": None,
        "latest_exit_code": None,
        "failed_stages": [],
        "summary_present": False,
        "stage_summaries_checked": len(REQUIRED_STAGE_SUMMARIES),
        "message": "Latest pipeline run passed validation.",
        "recommended_action": "No action required.",
        "missing_stage_summaries": [],
    }

    reason_codes: list[str] = []
    failed_stages: list[str] = []

    try:
        raw_index = load_json(index_path)
        runs = normalize_runs(raw_index)
    except Exception as exc:
        payload["alert"] = True
        payload["severity"] = "high"
        payload["reason_codes"] = ["run_index_unreadable"]
        payload["message"] = f"Cannot read run index: {exc}"
        payload["recommended_action"] = "Verify runs/run_history_index.json is present and valid JSON."
        return payload

    if not runs:
        payload["alert"] = True
        payload["severity"] = "high"
        payload["reason_codes"] = ["run_index_unreadable"]
        payload["message"] = "Run index is empty; latest run cannot be evaluated."
        payload["recommended_action"] = "Run a pipeline job and verify run index updates."
        return payload

    latest = choose_latest_run(runs)
    if latest is None:
        payload["alert"] = True
        payload["severity"] = "high"
        payload["reason_codes"] = ["run_index_unreadable"]
        payload["message"] = "No valid latest run entry found."
        payload["recommended_action"] = "Inspect run-history index entries for timestamp fields."
        return payload

    latest_run_id = latest.get("timestamp")
    latest_run_path = Path(str(latest.get("run_path", ""))) if latest.get("run_path") else None
    latest_status = str(latest.get("status", "")).strip().lower()
    latest_exit = latest.get("exit_code")

    payload["latest_run_id"] = latest_run_id
    payload["latest_run_path"] = str(latest_run_path) if latest_run_path else None
    payload["latest_run_timestamp"] = latest.get("completed_at") or latest.get("started_at") or latest.get("timestamp")
    payload["latest_run_status"] = latest.get("status")
    payload["latest_exit_code"] = latest_exit

    try:
        if int(latest_exit) != 0:
            reason_codes.append("non_zero_exit")
    except Exception:
        reason_codes.append("malformed_summary")

    if latest_status not in SUCCESS_STATUSES:
        reason_codes.append("run_status_failed")

    if latest_run_path is None or not latest_run_path.exists():
        reason_codes.append("missing_run_summary")
    else:
        summary_path = latest_run_path / FULL_SUMMARY_NAME
        if not summary_path.exists():
            reason_codes.append("missing_run_summary")
        else:
            payload["summary_present"] = True
            try:
                full_summary = load_json(summary_path)
            except Exception:
                reason_codes.append("malformed_summary")
                full_summary = None

            if isinstance(full_summary, dict):
                details = full_summary.get("details", {})
                stages = details.get("stages", []) if isinstance(details, dict) else []
                if not isinstance(stages, list):
                    reason_codes.append("malformed_summary")
                    stages = []

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

        missing_stage_summaries = []
        for name in REQUIRED_STAGE_SUMMARIES:
            if not (latest_run_path / name).exists():
                missing_stage_summaries.append(name)

        payload["missing_stage_summaries"] = missing_stage_summaries
        if missing_stage_summaries:
            reason_codes.append("missing_stage_summary")

    reason_codes = sorted(set(reason_codes))
    failed_stages = sorted(set(failed_stages))

    payload["failed_stages"] = failed_stages
    payload["reason_codes"] = reason_codes
    payload["alert"] = len(reason_codes) > 0

    if payload["alert"]:
        payload["severity"] = "high"
        payload["message"] = "Latest pipeline run failed validation."
        payload["recommended_action"] = (
            "Inspect full pipeline summary and failed stage logs for the latest run."
        )
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AI-RISA Latest Run Alert",
        "",
        f"Generated at: {payload.get('generated_at')}",
        f"Alert: {'YES' if payload.get('alert') else 'NO'}",
        f"Severity: {payload.get('severity')}",
        "",
        "## Latest Run",
        f"- Run ID: {payload.get('latest_run_id')}",
        f"- Run Path: {payload.get('latest_run_path')}",
        f"- Run Timestamp: {payload.get('latest_run_timestamp')}",
        f"- Run Status: {payload.get('latest_run_status')}",
        f"- Exit Code: {payload.get('latest_exit_code')}",
        f"- Summary Present: {payload.get('summary_present')}",
        f"- Stage Summaries Checked: {payload.get('stage_summaries_checked')}",
        "",
        "## Evaluation",
        f"- Reason Codes: {', '.join(payload.get('reason_codes') or []) or 'none'}",
        f"- Failed Stages: {', '.join(payload.get('failed_stages') or []) or 'none'}",
        f"- Missing Stage Summaries: {', '.join(payload.get('missing_stage_summaries') or []) or 'none'}",
        "",
        "## Operator Action",
        f"- Message: {payload.get('message')}",
        f"- Recommended Action: {payload.get('recommended_action')}",
        "",
    ]
    return "\n".join(lines)


def write_outputs(repo_root: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    alerts_dir = repo_root / "ops" / "alerts"
    ensure_dir(alerts_dir)

    json_path = alerts_dir / ALERT_JSON_NAME
    md_path = alerts_dir / ALERT_MD_NAME

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    payload = evaluate_latest_run(repo_root)
    json_path, md_path = write_outputs(repo_root, payload)

    print(f"[WRITE] {json_path}")
    print(f"[WRITE] {md_path}")
    print(f"[STATUS] alert={payload.get('alert')} reasons={payload.get('reason_codes')}")

    return 2 if payload.get("alert") else 0


if __name__ == "__main__":
    sys.exit(main())
