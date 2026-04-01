#!/usr/bin/env python3
"""
AI-RISA v1.4 Operator Dashboard (slice 1): read-only dashboard artifact generator.

Generates a minimal operator-facing dashboard from existing summary outputs only.
This script does not execute pipeline stages or mutate canonical pipeline schemas.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")

OUTPUT_DIR = Path("ops/dashboard")
OUTPUT_JSON = "operator_dashboard.json"
OUTPUT_MD = "operator_dashboard.md"

FULL_SUMMARY = Path("output/full_pipeline_run_summary.json")
BATCH_SUMMARY = Path("output/event_batch_run_summary.json")
BATCH_DRY_RUN_SUMMARY = Path("output/dry_run/event_batch_run_summary.json")
QUEUE_SUMMARY = Path("output/prediction_queue_run_summary.json")
RUN_HISTORY_INDEX = Path("runs/run_history_index.json")
RUN_FULL_PIPELINE_SUMMARY = "full_pipeline_run_summary.json"

STALE_WARNING_MINUTES = 120
STALE_CRITICAL_MINUTES = 720
LOCAL_TZ = datetime.now().astimezone().tzinfo or timezone.utc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only operator dashboard artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Output directory relative to repo root",
    )
    return parser.parse_args()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_path(path: Path) -> str:
    return path.as_posix()


def parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(timezone.utc)


def minutes_between(older: datetime, newer: datetime) -> int:
    delta_seconds = max(0.0, (newer - older).total_seconds())
    return int(delta_seconds // 60)


def classify_freshness(reference_time: datetime | None, now: datetime) -> dict[str, Any]:
    if reference_time is None:
        return {
            "state": "unknown",
            "age_minutes": None,
            "reference_timestamp_utc": None,
        }

    age_minutes = minutes_between(reference_time, now)
    if age_minutes >= STALE_CRITICAL_MINUTES:
        state = "stale_critical"
    elif age_minutes >= STALE_WARNING_MINUTES:
        state = "stale"
    else:
        state = "fresh"

    return {
        "state": state,
        "age_minutes": age_minutes,
        "reference_timestamp_utc": reference_time.isoformat(),
    }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_read_json(path: Path) -> tuple[Any, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return load_json(path), None
    except Exception as exc:
        return None, f"unreadable: {exc}"


def file_meta(abs_path: Path, rel_path: Path) -> dict[str, Any]:
    if not abs_path.exists():
        return {
            "path": normalize_path(rel_path),
            "exists": False,
            "last_modified_utc": None,
        }
    mtime = datetime.fromtimestamp(abs_path.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "path": normalize_path(rel_path),
        "exists": True,
        "last_modified_utc": mtime,
    }


def extract_recommended_action(markdown: str | None) -> str | None:
    if not markdown:
        return None

    lines = markdown.splitlines()
    in_section = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            in_section = line.lower().startswith("# recommended operator action")
            continue
        if in_section and line.startswith("-"):
            return line[1:].strip()
    return None


def collect_source_summaries(repo_root: Path, now: datetime) -> list[dict[str, Any]]:
    candidates = [
        ("full_pipeline", FULL_SUMMARY),
        ("event_batch", BATCH_SUMMARY),
        ("event_batch_dry_run", BATCH_DRY_RUN_SUMMARY),
        ("prediction_queue_run", QUEUE_SUMMARY),
    ]

    out: list[dict[str, Any]] = []
    for label, rel_path in candidates:
        abs_path = repo_root / rel_path
        summary, error = safe_read_json(abs_path)
        meta = file_meta(abs_path, rel_path)

        finished_at = summary.get("finished_at") if isinstance(summary, dict) else None
        finished_at_dt = parse_iso_datetime(finished_at)
        modified_dt = parse_iso_datetime(meta.get("last_modified_utc"))
        freshness = classify_freshness(finished_at_dt or modified_dt, now)

        if not meta.get("exists"):
            freshness["state"] = "missing"
        elif error is not None:
            freshness["state"] = "unreadable"

        entry = {
            "label": label,
            **meta,
            "read_error": error,
            "stage": summary.get("stage") if isinstance(summary, dict) else None,
            "status": summary.get("status") if isinstance(summary, dict) else None,
            "started_at": summary.get("started_at") if isinstance(summary, dict) else None,
            "finished_at": finished_at,
            "freshness": freshness,
        }
        out.append(entry)

    return out


def pick_primary(full_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(full_summary, dict):
        return {
            "status": "unknown",
            "summary_available": False,
            "message": "Full pipeline summary is missing or unreadable.",
        }

    counts = full_summary.get("counts") if isinstance(full_summary.get("counts"), dict) else {}
    warnings = full_summary.get("warnings") if isinstance(full_summary.get("warnings"), list) else []
    errors = full_summary.get("errors") if isinstance(full_summary.get("errors"), list) else []

    return {
        "summary_available": True,
        "stage": full_summary.get("stage"),
        "status": full_summary.get("status"),
        "started_at": full_summary.get("started_at"),
        "finished_at": full_summary.get("finished_at"),
        "counts": counts,
        "warnings_count": len(warnings),
        "errors_count": len(errors),
    }


def summarize_source_health(source_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "total": len(source_summaries),
        "fresh": 0,
        "stale": 0,
        "stale_critical": 0,
        "missing": 0,
        "unreadable": 0,
        "unknown": 0,
    }
    problematic: list[dict[str, Any]] = []

    for row in source_summaries:
        freshness = row.get("freshness") if isinstance(row.get("freshness"), dict) else {}
        state = str(freshness.get("state") or "unknown")
        if state not in totals:
            state = "unknown"
        totals[state] += 1

        if state != "fresh":
            problematic.append(
                {
                    "label": row.get("label"),
                    "path": row.get("path"),
                    "state": state,
                    "age_minutes": freshness.get("age_minutes"),
                    "read_error": row.get("read_error"),
                }
            )

    if totals["missing"] > 0 or totals["unreadable"] > 0 or totals["stale_critical"] > 0:
        overall = "critical"
    elif totals["stale"] > 0 or totals["unknown"] > 0:
        overall = "watch"
    else:
        overall = "healthy"

    return {
        "overall_state": overall,
        "totals": totals,
        "problematic_sources": problematic[:8],
    }


def parse_run_sort_timestamp(run: dict[str, Any]) -> datetime | None:
    for key in ("completed_at", "started_at", "timestamp"):
        parsed = parse_iso_datetime(run.get(key))
        if parsed is not None:
            return parsed
    return None


def get_recent_runs(repo_root: Path) -> list[dict[str, Any]]:
    raw, err = safe_read_json(repo_root / RUN_HISTORY_INDEX)
    if err is not None or not isinstance(raw, list):
        return []

    rows = [r for r in raw if isinstance(r, dict)]
    rows.sort(key=lambda r: parse_run_sort_timestamp(r) or datetime.min.replace(tzinfo=timezone.utc))
    return rows


def get_run_summary(repo_root: Path, run: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    run_path_value = run.get("run_path")
    if not isinstance(run_path_value, str) or not run_path_value.strip():
        return None, "missing_run_path"

    run_path = Path(run_path_value)
    if not run_path.is_absolute():
        run_path = repo_root / run_path

    summary_path = run_path / RUN_FULL_PIPELINE_SUMMARY
    summary, err = safe_read_json(summary_path)
    if err is not None:
        return None, err
    return summary if isinstance(summary, dict) else None, None


def int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def build_change_snapshot(repo_root: Path, current_full_summary: dict[str, Any] | None) -> dict[str, Any]:
    runs = get_recent_runs(repo_root)
    if len(runs) < 2:
        return {
            "available": False,
            "reason": "insufficient_run_history",
        }

    latest_run = runs[-1]
    previous_run = runs[-2]

    previous_summary, previous_err = get_run_summary(repo_root, previous_run)
    if previous_summary is None:
        return {
            "available": False,
            "reason": f"previous_summary_{previous_err or 'unavailable'}",
            "latest_run_id": latest_run.get("timestamp"),
            "previous_run_id": previous_run.get("timestamp"),
        }

    latest_summary = current_full_summary
    if latest_summary is None:
        latest_summary, latest_err = get_run_summary(repo_root, latest_run)
        if latest_summary is None:
            return {
                "available": False,
                "reason": f"latest_summary_{latest_err or 'unavailable'}",
                "latest_run_id": latest_run.get("timestamp"),
                "previous_run_id": previous_run.get("timestamp"),
            }

    latest_counts = latest_summary.get("counts") if isinstance(latest_summary.get("counts"), dict) else {}
    previous_counts = previous_summary.get("counts") if isinstance(previous_summary.get("counts"), dict) else {}
    latest_warnings = latest_summary.get("warnings") if isinstance(latest_summary.get("warnings"), list) else []
    previous_warnings = previous_summary.get("warnings") if isinstance(previous_summary.get("warnings"), list) else []

    metrics = {
        "failed": (int_or_none(latest_counts.get("failed")) or 0) - (int_or_none(previous_counts.get("failed")) or 0),
        "soft_skipped": (int_or_none(latest_counts.get("soft_skipped")) or 0) - (int_or_none(previous_counts.get("soft_skipped")) or 0),
        "completed": (int_or_none(latest_counts.get("completed")) or 0) - (int_or_none(previous_counts.get("completed")) or 0),
        "warnings": len(latest_warnings) - len(previous_warnings),
    }

    status_latest = latest_summary.get("status")
    status_previous = previous_summary.get("status")
    status_changed = status_latest != status_previous

    highlights: list[str] = []
    if status_changed:
        highlights.append(f"Run status changed: {status_previous} -> {status_latest}")
    for key, delta in metrics.items():
        if delta != 0:
            direction = "+" if delta > 0 else ""
            highlights.append(f"{key} delta: {direction}{delta}")

    if not highlights:
        highlights.append("No top-line count or status changes vs previous run.")

    return {
        "available": True,
        "latest_run_id": latest_run.get("timestamp"),
        "previous_run_id": previous_run.get("timestamp"),
        "status": {
            "latest": status_latest,
            "previous": status_previous,
            "changed": status_changed,
        },
        "count_deltas": metrics,
        "highlights": highlights,
    }


def build_prioritized_actions(
    latest_pipeline_snapshot: dict[str, Any],
    warning_readability: dict[str, Any],
    source_health: dict[str, Any],
    change_snapshot: dict[str, Any],
    fallback_action: str,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    if (latest_pipeline_snapshot.get("status") != "success") or (int_or_none(latest_pipeline_snapshot.get("errors_count")) or 0) > 0:
        actions.append(
            {
                "priority": 1,
                "severity": "critical",
                "title": "Investigate latest pipeline run",
                "action": "Review full pipeline summary errors and stage statuses before downstream use.",
            }
        )

    if source_health.get("overall_state") == "critical":
        actions.append(
            {
                "priority": 1,
                "severity": "critical",
                "title": "Recover unhealthy source summaries",
                "action": "Address missing/unreadable/stale-critical source summaries to restore dashboard reliability.",
            }
        )
    elif source_health.get("overall_state") == "watch":
        actions.append(
            {
                "priority": 2,
                "severity": "watch",
                "title": "Refresh stale source summaries",
                "action": "Re-run bounded reporting refresh for stale sources and confirm timestamps are current.",
            }
        )

    action_needed_count = int_or_none(warning_readability.get("action_needed_count")) or 0
    if action_needed_count > 0:
        actions.append(
            {
                "priority": 2,
                "severity": "watch",
                "title": "Resolve action-needed warnings",
                "action": f"Investigate {action_needed_count} action-needed warning(s) in reporting summaries.",
            }
        )

    if change_snapshot.get("available"):
        deltas = change_snapshot.get("count_deltas") if isinstance(change_snapshot.get("count_deltas"), dict) else {}
        failed_delta = int_or_none(deltas.get("failed")) or 0
        if failed_delta > 0:
            actions.append(
                {
                    "priority": 2,
                    "severity": "watch",
                    "title": "Review increased failed count",
                    "action": f"Failed count increased by {failed_delta} vs previous run; inspect run-to-run differences.",
                }
            )

    actions.append(
        {
            "priority": 3,
            "severity": "info",
            "title": "Baseline operator follow-up",
            "action": fallback_action,
        }
    )

    actions.sort(key=lambda x: (int_or_none(x.get("priority")) or 99, str(x.get("title") or "")))
    return actions


def pick_reporting_block(
    full_summary: dict[str, Any] | None,
    batch_dry_run_summary: dict[str, Any] | None,
) -> tuple[dict[str, Any], str]:
    def details_of(summary: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(summary, dict):
            return {}
        details = summary.get("details")
        return details if isinstance(details, dict) else {}

    full_details = details_of(full_summary)
    batch_details = details_of(batch_dry_run_summary)

    if full_details.get("analysis_coverage"):
        return full_details, normalize_path(FULL_SUMMARY)
    if batch_details.get("analysis_coverage"):
        return batch_details, normalize_path(BATCH_DRY_RUN_SUMMARY)

    return {}, "none"


def build_dashboard_payload(repo_root: Path) -> dict[str, Any]:
    now = now_utc()
    full_summary, _ = safe_read_json(repo_root / FULL_SUMMARY)
    batch_dry_run_summary, _ = safe_read_json(repo_root / BATCH_DRY_RUN_SUMMARY)

    source_summaries = collect_source_summaries(repo_root, now)
    latest_pipeline_snapshot = pick_primary(full_summary if isinstance(full_summary, dict) else None)

    details, details_source = pick_reporting_block(
        full_summary if isinstance(full_summary, dict) else None,
        batch_dry_run_summary if isinstance(batch_dry_run_summary, dict) else None,
    )

    coverage = details.get("analysis_coverage") if isinstance(details.get("analysis_coverage"), dict) else {}
    skipped = (
        details.get("skipped_items_exclusions")
        if isinstance(details.get("skipped_items_exclusions"), dict)
        else {}
    )
    interpretation = (
        details.get("operator_interpretation")
        if isinstance(details.get("operator_interpretation"), dict)
        else {}
    )
    warning_readability = (
        details.get("warning_readability")
        if isinstance(details.get("warning_readability"), dict)
        else {}
    )

    recommended_action = extract_recommended_action(
        details.get("human_readable_summary_markdown")
        if isinstance(details.get("human_readable_summary_markdown"), str)
        else None
    )

    if not recommended_action:
        if latest_pipeline_snapshot.get("status") == "success":
            recommended_action = (
                "Proceed with outputs while monitoring warning trends and documented exclusions."
            )
        else:
            recommended_action = (
                "Inspect failed stages and latest summary details before proceeding."
            )

    source_health = summarize_source_health(source_summaries)
    change_snapshot = build_change_snapshot(
        repo_root,
        full_summary if isinstance(full_summary, dict) else None,
    )
    prioritized_actions = build_prioritized_actions(
        latest_pipeline_snapshot,
        warning_readability,
        source_health,
        change_snapshot,
        recommended_action,
    )

    payload: dict[str, Any] = {
        "generated_at_utc": now.isoformat(),
        "dashboard_version": "v1.4-slice-2",
        "latest_pipeline_snapshot": {
            **latest_pipeline_snapshot,
            "source_summary_path": normalize_path(FULL_SUMMARY),
        },
        "coverage_snapshot": {
            "source": details_source,
            "analysis_coverage": coverage,
        },
        "skipped_exclusions_snapshot": {
            "source": details_source,
            "skipped_items_exclusions": skipped,
        },
        "warning_interpretation_snapshot": {
            "source": details_source,
            "operator_interpretation": interpretation,
            "warning_readability": warning_readability,
        },
        "recommended_operator_action": {
            "action": prioritized_actions[0]["action"] if prioritized_actions else recommended_action,
            "priority": prioritized_actions[0]["priority"] if prioritized_actions else 3,
            "title": prioritized_actions[0]["title"] if prioritized_actions else "Baseline operator follow-up",
            "source": details_source,
        },
        "prioritized_recommended_actions": prioritized_actions,
        "source_summary_health": source_health,
        "what_changed_since_last_run": change_snapshot,
        "source_summaries": source_summaries,
    }

    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    latest = payload.get("latest_pipeline_snapshot", {})
    coverage = payload.get("coverage_snapshot", {})
    skipped = payload.get("skipped_exclusions_snapshot", {})
    warn = payload.get("warning_interpretation_snapshot", {})
    action = payload.get("recommended_operator_action", {})
    prioritized_actions = payload.get("prioritized_recommended_actions", [])
    source_health = payload.get("source_summary_health", {})
    change_snapshot = payload.get("what_changed_since_last_run", {})
    sources = payload.get("source_summaries", [])

    analysis_coverage = coverage.get("analysis_coverage", {})
    skipped_items = skipped.get("skipped_items_exclusions", {})
    operator_interp = warn.get("operator_interpretation", {})
    warning_readability = warn.get("warning_readability", {})

    lines = [
        "# AI-RISA Operator Dashboard (Slice 2)",
        "",
        f"Generated (UTC): {payload.get('generated_at_utc')}",
        "",
        "## Latest Pipeline Snapshot",
        f"- Status: {latest.get('status')}",
        f"- Stage: {latest.get('stage')}",
        f"- Started At: {latest.get('started_at')}",
        f"- Finished At: {latest.get('finished_at')}",
        f"- Warnings: {latest.get('warnings_count')}",
        f"- Errors: {latest.get('errors_count')}",
        f"- Summary Path: {latest.get('source_summary_path')}",
        "",
        "## Coverage Snapshot",
        f"- Source: {coverage.get('source')}",
        f"- Analysis Coverage: {analysis_coverage}",
        "",
        "## Skipped/Exclusions Snapshot",
        f"- Source: {skipped.get('source')}",
        f"- Skipped/Exclusions: {skipped_items}",
        "",
        "## Warning Interpretation Snapshot",
        f"- Source: {warn.get('source')}",
        f"- Operator Interpretation: {operator_interp}",
        f"- Warning Readability: {warning_readability}",
        "",
        "## Recommended Operator Action",
        f"- {action.get('action')}",
        "",
        "## Prioritized Recommended Actions",
    ]

    if isinstance(prioritized_actions, list) and prioritized_actions:
        for row in prioritized_actions:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- P{priority} [{severity}] {title}: {action}".format(
                    priority=row.get("priority"),
                    severity=row.get("severity"),
                    title=row.get("title"),
                    action=row.get("action"),
                )
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Source Summary Health",
        f"- Overall State: {source_health.get('overall_state')}",
        f"- Totals: {source_health.get('totals')}",
        "",
        "## What Changed Since Last Run",
    ])

    if isinstance(change_snapshot, dict) and change_snapshot.get("available"):
        lines.append(f"- Latest Run ID: {change_snapshot.get('latest_run_id')}")
        lines.append(f"- Previous Run ID: {change_snapshot.get('previous_run_id')}")
        lines.append(f"- Status: {change_snapshot.get('status')}")
        lines.append(f"- Count Deltas: {change_snapshot.get('count_deltas')}")
        highlights = change_snapshot.get("highlights") if isinstance(change_snapshot.get("highlights"), list) else []
        lines.append(f"- Highlights: {highlights}")
    else:
        lines.append(f"- Unavailable: {change_snapshot.get('reason') if isinstance(change_snapshot, dict) else 'unknown'}")

    lines.extend([
        "",
        "## Source Summaries",
    ])

    if isinstance(sources, list) and sources:
        for row in sources:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- {label}: path={path} exists={exists} status={status} stage={stage} finished_at={finished_at} freshness={freshness} age_m={age_minutes}".format(
                    label=row.get("label"),
                    path=row.get("path"),
                    exists=row.get("exists"),
                    status=row.get("status"),
                    stage=row.get("stage"),
                    finished_at=row.get("finished_at"),
                    freshness=(row.get("freshness") or {}).get("state") if isinstance(row, dict) else None,
                    age_minutes=(row.get("freshness") or {}).get("age_minutes") if isinstance(row, dict) else None,
                )
            )
    else:
        lines.append("- None")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 1

    payload = build_dashboard_payload(repo_root)

    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / OUTPUT_JSON
    out_md = out_dir / OUTPUT_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] pipeline_status={status} coverage_source={source}".format(
            status=payload.get("latest_pipeline_snapshot", {}).get("status"),
            source=payload.get("coverage_snapshot", {}).get("source"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
