#!/usr/bin/env python3
"""
AI-RISA v1.5 Operator Workflows (slice 1): read-only operator action queue.

Builds a prioritized operator action queue from existing dashboard and reporting
signals only. This script does not execute pipeline stages or modify canonical
pipeline schemas.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_operator_dashboard_artifact import build_dashboard_payload

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/action_queue")
OUTPUT_JSON = "operator_action_queue.json"
OUTPUT_MD = "operator_action_queue.md"

SEVERITY_ORDER = {
    "critical": 0,
    "watch": 1,
    "info": 2,
}

FRESHNESS_ORDER = {
    "stale_critical": 0,
    "missing": 1,
    "unreadable": 1,
    "stale": 2,
    "unknown": 3,
    "fresh": 4,
    None: 5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only operator action queue artifacts"
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


def normalize_path(path: Path) -> str:
    return path.as_posix()


def handling_for(priority: int, severity: str) -> str:
    if severity == "critical" or priority <= 1:
        return "review_now"
    if severity == "watch" or priority == 2:
        return "defer"
    return "monitor"


def build_baseline_item(dashboard: dict[str, Any]) -> dict[str, Any]:
    action = dashboard.get("recommended_operator_action", {})
    source_health = dashboard.get("source_summary_health", {})
    change_snapshot = dashboard.get("what_changed_since_last_run", {})
    highlights = change_snapshot.get("highlights") if isinstance(change_snapshot.get("highlights"), list) else []

    return {
        "id": "action-baseline-follow-up",
        "category": "recommended_action",
        "severity": "info",
        "priority": int(action.get("priority") or 3),
        "title": str(action.get("title") or "Baseline operator follow-up"),
        "summary": str(action.get("action") or "Review dashboard signals and continue normal operation."),
        "suggested_handling": handling_for(int(action.get("priority") or 3), "info"),
        "freshness_state": str(source_health.get("overall_state") or "healthy"),
        "source_paths": [str(action.get("source") or "output/full_pipeline_run_summary.json")],
        "supporting_evidence": {
            "source_health": source_health.get("overall_state"),
            "change_highlights": highlights,
        },
    }


def build_problem_source_items(problematic_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in problematic_sources:
        if not isinstance(row, dict):
            continue

        state = str(row.get("state") or "unknown")
        severity = "critical" if state in {"stale_critical", "missing", "unreadable"} else "watch"
        priority = 1 if severity == "critical" else 2
        label = str(row.get("label") or "unknown_source")

        items.append(
            {
                "id": f"source-{label}",
                "category": "source_summary_health",
                "severity": severity,
                "priority": priority,
                "title": f"Address {label} source summary state",
                "summary": f"Source summary '{label}' is {state} and should be reviewed before relying on downstream dashboard guidance.",
                "suggested_handling": handling_for(priority, severity),
                "freshness_state": state,
                "source_paths": [str(row.get("path") or "")],
                "supporting_evidence": {
                    "age_minutes": row.get("age_minutes"),
                    "read_error": row.get("read_error"),
                },
            }
        )

    return items


def build_warning_item(dashboard: dict[str, Any]) -> dict[str, Any] | None:
    warning = dashboard.get("warning_interpretation_snapshot", {})
    readability = warning.get("warning_readability", {}) if isinstance(warning.get("warning_readability"), dict) else {}
    action_needed_count = int(readability.get("action_needed_count") or 0)
    non_fatal_count = int(readability.get("non_fatal_operational_count") or 0)

    if action_needed_count <= 0 and non_fatal_count <= 0:
        return None

    severity = "critical" if action_needed_count > 0 else "watch"
    priority = 1 if action_needed_count > 0 else 2
    summary = (
        f"Investigate {action_needed_count} action-needed warning(s)."
        if action_needed_count > 0
        else f"Review {non_fatal_count} non-fatal operational warning(s) and confirm they remain acceptable."
    )

    return {
        "id": "warning-review",
        "category": "warning_interpretation",
        "severity": severity,
        "priority": priority,
        "title": "Review warning and diagnostic surface",
        "summary": summary,
        "suggested_handling": handling_for(priority, severity),
        "freshness_state": "fresh",
        "source_paths": [str(warning.get("source") or "output/full_pipeline_run_summary.json")],
        "supporting_evidence": {
            "action_needed_count": action_needed_count,
            "non_fatal_operational_count": non_fatal_count,
        },
    }


def build_change_item(change_snapshot: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(change_snapshot, dict) or not change_snapshot.get("available"):
        return None

    count_deltas = change_snapshot.get("count_deltas", {}) if isinstance(change_snapshot.get("count_deltas"), dict) else {}
    highlights = change_snapshot.get("highlights") if isinstance(change_snapshot.get("highlights"), list) else []
    non_zero = {key: value for key, value in count_deltas.items() if int(value or 0) != 0}

    if not non_zero and not bool((change_snapshot.get("status") or {}).get("changed")):
        return {
            "id": "run-change-stable",
            "category": "change_snapshot",
            "severity": "info",
            "priority": 4,
            "title": "No top-line run changes detected",
            "summary": "Latest run matches the previous run on top-line status, warnings, and counts.",
            "suggested_handling": handling_for(4, "info"),
            "freshness_state": "fresh",
            "source_paths": ["runs/run_history_index.json"],
            "supporting_evidence": {
                "latest_run_id": change_snapshot.get("latest_run_id"),
                "previous_run_id": change_snapshot.get("previous_run_id"),
                "highlights": highlights,
            },
        }

    severity = "critical" if int(non_zero.get("failed") or 0) > 0 else "watch"
    priority = 1 if severity == "critical" else 2
    return {
        "id": "run-change-review",
        "category": "change_snapshot",
        "severity": severity,
        "priority": priority,
        "title": "Review latest run changes",
        "summary": "Latest run differs from the previous run and should be reviewed before operator handoff.",
        "suggested_handling": handling_for(priority, severity),
        "freshness_state": "fresh",
        "source_paths": ["runs/run_history_index.json"],
        "supporting_evidence": {
            "latest_run_id": change_snapshot.get("latest_run_id"),
            "previous_run_id": change_snapshot.get("previous_run_id"),
            "count_deltas": count_deltas,
            "highlights": highlights,
        },
    }


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        key = (str(row.get("category") or ""), str(row.get("title") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda row: (
            int(row.get("priority") or 99),
            SEVERITY_ORDER.get(str(row.get("severity") or "info"), 9),
            FRESHNESS_ORDER.get(str(row.get("freshness_state") or None), 9),
            str(row.get("title") or ""),
        ),
    )


def summarize_queue(items: list[dict[str, Any]]) -> dict[str, Any]:
    severity_counts = {"critical": 0, "watch": 0, "info": 0}
    handling_counts = {"review_now": 0, "defer": 0, "monitor": 0}

    for row in items:
        severity = str(row.get("severity") or "info")
        handling = str(row.get("suggested_handling") or "monitor")
        if severity in severity_counts:
            severity_counts[severity] += 1
        if handling in handling_counts:
            handling_counts[handling] += 1

    top_item = items[0] if items else None
    return {
        "total_actions": len(items),
        "severity_counts": severity_counts,
        "handling_counts": handling_counts,
        "top_action": {
            "id": top_item.get("id") if isinstance(top_item, dict) else None,
            "title": top_item.get("title") if isinstance(top_item, dict) else None,
            "priority": top_item.get("priority") if isinstance(top_item, dict) else None,
            "severity": top_item.get("severity") if isinstance(top_item, dict) else None,
        },
    }


def build_action_queue_payload(repo_root: Path) -> dict[str, Any]:
    dashboard = build_dashboard_payload(repo_root)
    source_health = dashboard.get("source_summary_health", {}) if isinstance(dashboard.get("source_summary_health"), dict) else {}
    problematic_sources = source_health.get("problematic_sources") if isinstance(source_health.get("problematic_sources"), list) else []
    change_snapshot = dashboard.get("what_changed_since_last_run", {}) if isinstance(dashboard.get("what_changed_since_last_run"), dict) else {}

    items: list[dict[str, Any]] = []
    items.extend(build_problem_source_items(problematic_sources))

    warning_item = build_warning_item(dashboard)
    if warning_item is not None:
        items.append(warning_item)

    change_item = build_change_item(change_snapshot)
    if change_item is not None:
        items.append(change_item)

    items.append(build_baseline_item(dashboard))
    items = sort_items(dedupe_items(items))

    payload: dict[str, Any] = {
        "generated_at_utc": now_utc_iso(),
        "action_queue_version": "v1.5-slice-1",
        "source_dashboard_version": dashboard.get("dashboard_version"),
        "queue_summary": summarize_queue(items),
        "items": items,
        "dashboard_snapshot": {
            "latest_pipeline_status": (dashboard.get("latest_pipeline_snapshot") or {}).get("status"),
            "source_summary_health": source_health.get("overall_state"),
            "recommended_operator_action": dashboard.get("recommended_operator_action"),
        },
        "source_paths": {
            "dashboard_generator": normalize_path(Path("generate_operator_dashboard_artifact.py")),
            "dashboard_json": normalize_path(Path("ops/dashboard/operator_dashboard.json")),
            "full_pipeline_summary": normalize_path(Path("output/full_pipeline_run_summary.json")),
            "run_history_index": normalize_path(Path("runs/run_history_index.json")),
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    queue_summary = payload.get("queue_summary", {})
    dashboard_snapshot = payload.get("dashboard_snapshot", {})
    items = payload.get("items", [])

    lines = [
        "# AI-RISA Operator Action Queue (Slice 1)",
        "",
        f"Generated (UTC): {payload.get('generated_at_utc')}",
        f"Dashboard Version: {payload.get('source_dashboard_version')}",
        "",
        "## Queue Summary",
        f"- Total Actions: {queue_summary.get('total_actions')}",
        f"- Severity Counts: {queue_summary.get('severity_counts')}",
        f"- Handling Counts: {queue_summary.get('handling_counts')}",
        f"- Top Action: {queue_summary.get('top_action')}",
        "",
        "## Dashboard Snapshot",
        f"- Latest Pipeline Status: {dashboard_snapshot.get('latest_pipeline_status')}",
        f"- Source Summary Health: {dashboard_snapshot.get('source_summary_health')}",
        f"- Recommended Operator Action: {dashboard_snapshot.get('recommended_operator_action')}",
        "",
        "## Action Queue",
    ]

    if isinstance(items, list) and items:
        for row in items:
            if not isinstance(row, dict):
                continue
            lines.extend(
                [
                    f"- [{row.get('severity')}] P{row.get('priority')} {row.get('title')}",
                    f"  Summary: {row.get('summary')}",
                    f"  Suggested Handling: {row.get('suggested_handling')}",
                    f"  Freshness State: {row.get('freshness_state')}",
                    f"  Source Paths: {row.get('source_paths')}",
                    f"  Evidence: {row.get('supporting_evidence')}",
                ]
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Source Paths",
            f"- {payload.get('source_paths')}",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 1

    payload = build_action_queue_payload(repo_root)

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
        "[STATUS] total_actions={total} top_action={title}".format(
            total=(payload.get("queue_summary") or {}).get("total_actions"),
            title=((payload.get("queue_summary") or {}).get("top_action") or {}).get("title"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())