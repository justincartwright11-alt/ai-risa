#!/usr/bin/env python3
"""
AI-RISA v1.6 Operator Automation (slice 1): read-only automation queue.

Builds a read-only automation/escalation queue from the operator worklist. This
script recommends reminders and escalations without mutating workflow state.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_operator_action_worklist import build_worklist_payload

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/automation")
OUTPUT_JSON = "operator_automation_queue.json"
OUTPUT_MD = "operator_automation_queue.md"

STALE_ACKNOWLEDGED_HOURS = 12
STALE_DEFERRED_HOURS = 24
CRITICAL_NEW_PRIORITY = 1

SEVERITY_SCORE = {
    "critical": 0,
    "watch": 1,
    "info": 2,
}

AUTOMATION_KIND_SCORE = {
    "escalation": 0,
    "priority_boost": 1,
    "reminder": 2,
    "handoff": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only operator automation queue artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--worklist-output-dir",
        default="ops/action_queue",
        help="Worklist directory relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Output directory relative to repo root",
    )
    return parser.parse_args()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_utc_iso() -> str:
    return now_utc().isoformat()


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
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def age_hours(updated_at_utc: Any, now: datetime) -> float | None:
    dt = parse_iso_datetime(updated_at_utc)
    if dt is None:
        return None
    return max(0.0, (now - dt).total_seconds() / 3600.0)


def build_candidate_from_item(item: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    item_id = str(item.get("id") or "")
    title = str(item.get("title") or "Untitled action")
    severity = str(item.get("severity") or "info")
    priority = int(item.get("priority") or 99)
    status = str(item.get("workflow_status") or "new")
    freshness_state = str(item.get("freshness_state") or "unknown")
    updated_at = item.get("workflow_updated_at_utc")
    owner = item.get("workflow_owner")
    age = age_hours(updated_at, now)

    if severity == "critical" and status == "new" and priority <= CRITICAL_NEW_PRIORITY:
        candidates.append(
            {
                "id": f"{item_id}-escalate-critical-new",
                "source_item_id": item_id,
                "automation_kind": "escalation",
                "severity": "critical",
                "priority": 1,
                "title": f"Escalate unresolved critical item: {title}",
                "recommendation": "Escalate immediately because the item is critical, new, and still open.",
                "reason": "critical_new_open_item",
                "source_paths": item.get("source_paths") or [],
                "workflow_context": {
                    "status": status,
                    "owner": owner,
                    "updated_at_utc": updated_at,
                    "freshness_state": freshness_state,
                },
            }
        )

    if status == "acknowledged" and (age is None or age >= STALE_ACKNOWLEDGED_HOURS):
        candidates.append(
            {
                "id": f"{item_id}-remind-acknowledged",
                "source_item_id": item_id,
                "automation_kind": "reminder",
                "severity": "watch" if severity != "critical" else "critical",
                "priority": min(priority, 2),
                "title": f"Reminder for acknowledged item: {title}",
                "recommendation": "Send a reminder or re-surface this acknowledged item because it has remained open past the reminder threshold.",
                "reason": "acknowledged_item_aging",
                "source_paths": item.get("source_paths") or [],
                "workflow_context": {
                    "status": status,
                    "owner": owner,
                    "updated_at_utc": updated_at,
                    "age_hours": age,
                    "freshness_state": freshness_state,
                },
            }
        )

    if status == "deferred" and (age is None or age >= STALE_DEFERRED_HOURS):
        candidates.append(
            {
                "id": f"{item_id}-escalate-deferred",
                "source_item_id": item_id,
                "automation_kind": "priority_boost",
                "severity": "watch" if severity == "info" else severity,
                "priority": min(priority, 2),
                "title": f"Boost priority for deferred item: {title}",
                "recommendation": "Raise this deferred item back into active review because it has exceeded the deferral threshold.",
                "reason": "deferred_item_aging",
                "source_paths": item.get("source_paths") or [],
                "workflow_context": {
                    "status": status,
                    "owner": owner,
                    "updated_at_utc": updated_at,
                    "age_hours": age,
                    "freshness_state": freshness_state,
                },
            }
        )

    if freshness_state in {"stale", "stale_critical", "missing", "unreadable"} and status != "resolved":
        candidates.append(
            {
                "id": f"{item_id}-stale-followup",
                "source_item_id": item_id,
                "automation_kind": "priority_boost",
                "severity": "critical" if freshness_state in {"stale_critical", "missing", "unreadable"} else "watch",
                "priority": min(priority, 2),
                "title": f"Boost stale-source item: {title}",
                "recommendation": "Re-surface this item because its underlying freshness or source state indicates the signal may be aging or degraded.",
                "reason": "stale_or_degraded_source_signal",
                "source_paths": item.get("source_paths") or [],
                "workflow_context": {
                    "status": status,
                    "owner": owner,
                    "updated_at_utc": updated_at,
                    "freshness_state": freshness_state,
                },
            }
        )

    return candidates


def build_handoff_candidate(worklist: dict[str, Any]) -> dict[str, Any]:
    handoff = worklist.get("operator_handoff") if isinstance(worklist.get("operator_handoff"), dict) else {}
    top_open = handoff.get("top_open_actions") if isinstance(handoff.get("top_open_actions"), list) else []
    return {
        "id": "generate-handoff-summary",
        "source_item_id": None,
        "automation_kind": "handoff",
        "severity": "info",
        "priority": 4,
        "title": "Generate operator handoff summary",
        "recommendation": "Prepare a compact handoff summary for the next operator shift using the current top open actions.",
        "reason": "open_action_handoff",
        "source_paths": ["ops/action_queue/operator_action_worklist.json"],
        "workflow_context": {
            "open_action_count": handoff.get("open_action_count"),
            "top_open_actions": top_open,
        },
    }


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in candidates:
        row_id = str(row.get("id") or "")
        if not row_id or row_id in seen:
            continue
        seen.add(row_id)
        out.append(row)
    return out


def sort_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda row: (
            int(row.get("priority") or 99),
            SEVERITY_SCORE.get(str(row.get("severity") or "info"), 9),
            AUTOMATION_KIND_SCORE.get(str(row.get("automation_kind") or "handoff"), 9),
            str(row.get("title") or ""),
        ),
    )


def summarize_queue(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    severity_counts = {"critical": 0, "watch": 0, "info": 0}
    automation_counts = {"escalation": 0, "priority_boost": 0, "reminder": 0, "handoff": 0}
    for row in candidates:
        severity = str(row.get("severity") or "info")
        kind = str(row.get("automation_kind") or "handoff")
        if severity in severity_counts:
            severity_counts[severity] += 1
        if kind in automation_counts:
            automation_counts[kind] += 1

    top = candidates[0] if candidates else None
    return {
        "total_candidates": len(candidates),
        "severity_counts": severity_counts,
        "automation_kind_counts": automation_counts,
        "top_candidate": {
            "id": top.get("id") if isinstance(top, dict) else None,
            "title": top.get("title") if isinstance(top, dict) else None,
            "priority": top.get("priority") if isinstance(top, dict) else None,
            "severity": top.get("severity") if isinstance(top, dict) else None,
            "automation_kind": top.get("automation_kind") if isinstance(top, dict) else None,
        },
    }


def build_automation_queue_payload(repo_root: Path, worklist_output_dir: Path) -> dict[str, Any]:
    worklist = build_worklist_payload(repo_root, worklist_output_dir)
    now = now_utc()
    items = worklist.get("items") if isinstance(worklist.get("items"), list) else []

    candidates: list[dict[str, Any]] = []
    for row in items:
        if isinstance(row, dict) and row.get("is_open"):
            candidates.extend(build_candidate_from_item(row, now))

    candidates.append(build_handoff_candidate(worklist))
    candidates = sort_candidates(dedupe_candidates(candidates))

    payload: dict[str, Any] = {
        "generated_at_utc": now.isoformat(),
        "automation_queue_version": "v1.6-slice-1",
        "source_worklist_version": worklist.get("worklist_version"),
        "queue_summary": summarize_queue(candidates),
        "candidates": candidates,
        "worklist_snapshot": {
            "workflow_status_summary": worklist.get("workflow_status_summary"),
            "operator_handoff": worklist.get("operator_handoff"),
            "state_store": worklist.get("state_store"),
        },
        "source_paths": {
            "worklist_generator": normalize_path(Path("generate_operator_action_worklist.py")),
            "worklist_json": normalize_path(worklist_output_dir / "operator_action_worklist.json"),
            "action_queue_json": normalize_path(worklist_output_dir / "operator_action_queue.json"),
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("queue_summary", {})
    snapshot = payload.get("worklist_snapshot", {})
    candidates = payload.get("candidates", [])

    lines = [
        "# AI-RISA Operator Automation Queue (Slice 1)",
        "",
        f"Generated (UTC): {payload.get('generated_at_utc')}",
        f"Worklist Version: {payload.get('source_worklist_version')}",
        "",
        "## Queue Summary",
        f"- Total Candidates: {summary.get('total_candidates')}",
        f"- Severity Counts: {summary.get('severity_counts')}",
        f"- Automation Kind Counts: {summary.get('automation_kind_counts')}",
        f"- Top Candidate: {summary.get('top_candidate')}",
        "",
        "## Worklist Snapshot",
        f"- Workflow Status Summary: {snapshot.get('workflow_status_summary')}",
        f"- Operator Handoff: {snapshot.get('operator_handoff')}",
        f"- State Store: {snapshot.get('state_store')}",
        "",
        "## Automation Candidates",
    ]

    if isinstance(candidates, list) and candidates:
        for row in candidates:
            if not isinstance(row, dict):
                continue
            lines.extend(
                [
                    f"- [{row.get('severity')}] P{row.get('priority')} {row.get('title')} ({row.get('automation_kind')})",
                    f"  Recommendation: {row.get('recommendation')}",
                    f"  Reason: {row.get('reason')}",
                    f"  Source Item: {row.get('source_item_id')}",
                    f"  Source Paths: {row.get('source_paths')}",
                    f"  Workflow Context: {row.get('workflow_context')}",
                ]
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Source Paths", f"- {payload.get('source_paths')}", ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 1

    worklist_output_dir = Path(args.worklist_output_dir)
    payload = build_automation_queue_payload(repo_root, worklist_output_dir)

    out_dir = repo_root / Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / OUTPUT_JSON
    out_md = out_dir / OUTPUT_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] total_candidates={total} top_candidate={title}".format(
            total=(payload.get("queue_summary") or {}).get("total_candidates"),
            title=((payload.get("queue_summary") or {}).get("top_candidate") or {}).get("title"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())