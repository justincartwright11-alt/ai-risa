#!/usr/bin/env python3
"""
Shared read-only aggregation utilities for AI-RISA ops visibility.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

RUNS_DIR_NAME = "runs"
RUN_INDEX_NAME = "run_history_index.json"
FULL_SUMMARY_NAME = "full_pipeline_run_summary.json"

SUCCESS_STATUSES = {"success"}
NON_ALERT_STAGE_STATUSES = {"success", "soft_skip"}


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


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_runs(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def load_run_history(repo_root: Path) -> list[dict[str, Any]]:
    index_path = repo_root / RUNS_DIR_NAME / RUN_INDEX_NAME
    raw = load_json(index_path)
    return normalize_runs(raw)


def run_datetime(record: dict[str, Any]) -> datetime | None:
    return (
        parse_timestamp(record.get("completed_at"))
        or parse_timestamp(record.get("started_at"))
        or parse_timestamp(record.get("timestamp"))
    )


def sort_runs_newest(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(runs, key=lambda r: run_datetime(r) or datetime.min, reverse=True)


def choose_latest_run(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    ordered = sort_runs_newest(runs)
    return ordered[0] if ordered else None


def choose_latest_successful_run(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    for run in sort_runs_newest(runs):
        if not is_failed_run(run):
            return run
    return None


def choose_latest_failed_run(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    for run in sort_runs_newest(runs):
        if is_failed_run(run):
            return run
    return None


def run_snapshot(record: dict[str, Any] | None) -> dict[str, Any]:
    if not record:
        return {
            "run_id": None,
            "status": None,
            "exit_code": None,
            "path": None,
            "timestamp": None,
        }

    return {
        "run_id": record.get("timestamp"),
        "status": record.get("status"),
        "exit_code": record.get("exit_code"),
        "path": record.get("run_path"),
        "timestamp": record.get("completed_at") or record.get("started_at") or record.get("timestamp"),
    }


def is_failed_run(record: dict[str, Any]) -> bool:
    status = str(record.get("status", "")).strip().lower()
    try:
        exit_code = int(record.get("exit_code", 0))
    except Exception:
        exit_code = 1
    return exit_code != 0 or status not in SUCCESS_STATUSES


def derive_failure_details(record: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
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


def runs_in_window(
    runs: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    selected: list[dict[str, Any]] = []

    for run in runs:
        dt = run_datetime(run)
        if dt is None:
            notes.append(
                f"Run entry missing parseable timestamp: {run.get('timestamp', 'unknown')}"
            )
            continue
        if window_start <= dt <= window_end:
            selected.append(run)

    return selected, notes


def aggregate_window(
    runs: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
) -> dict[str, Any]:
    window_runs, notes = runs_in_window(runs, window_start, window_end)

    total = len(window_runs)
    success = sum(1 for r in window_runs if not is_failed_run(r))
    failed = total - success
    success_rate = (success / total) if total else 0.0

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

    return {
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
        "failed_runs": failed_runs_payload,
        "stage_failure_counts": dict(sorted(stage_failure_counts.items())),
        "failure_reason_counts": dict(sorted(reason_counts.items())),
        "data_quality_notes": sorted(set(notes)),
    }
