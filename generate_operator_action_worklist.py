#!/usr/bin/env python3
"""
AI-RISA v1.5 Operator Workflows (slice 2): operator state overlay.

Builds a merged operator worklist by overlaying local workflow state on top of
the read-only derived action queue. This script does not modify pipeline or
dashboard source logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_operator_action_queue import build_action_queue_payload

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/action_queue")
STATE_JSON = "operator_action_state.json"
WORKLIST_JSON = "operator_action_worklist.json"
WORKLIST_MD = "operator_action_worklist.md"

ALLOWED_STATUSES = {"new", "acknowledged", "deferred", "resolved"}
STATUS_ORDER = {
    "new": 0,
    "acknowledged": 1,
    "deferred": 2,
    "resolved": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate operator action worklist with state overlay"
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


def normalize_state_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        return {
            "status": "new",
            "owner": None,
            "note": None,
            "updated_at_utc": None,
        }

    status = str(entry.get("status") or "new").strip().lower()
    if status not in ALLOWED_STATUSES:
        status = "new"

    owner = entry.get("owner")
    note = entry.get("note")
    updated_at_utc = entry.get("updated_at_utc")
    return {
        "status": status,
        "owner": str(owner) if isinstance(owner, str) and owner.strip() else None,
        "note": str(note) if isinstance(note, str) and note.strip() else None,
        "updated_at_utc": str(updated_at_utc) if isinstance(updated_at_utc, str) and updated_at_utc.strip() else None,
    }


def ensure_state_store(path: Path, queue_items: list[dict[str, Any]]) -> dict[str, Any]:
    raw, err = safe_read_json(path)
    items_state: dict[str, Any] = {}

    if err is None and isinstance(raw, dict) and isinstance(raw.get("items"), dict):
        items_state = {str(key): normalize_state_entry(value) for key, value in raw.get("items", {}).items()}

    for item in queue_items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "")
        if item_id and item_id not in items_state:
            items_state[item_id] = {
                "status": "new",
                "owner": None,
                "note": None,
                "updated_at_utc": None,
            }

    payload = {
        "state_version": "v1.5-slice-2",
        "generated_at_utc": now_utc_iso(),
        "items": items_state,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def merge_items(queue_items: list[dict[str, Any]], state_items: dict[str, Any]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for row in queue_items:
        if not isinstance(row, dict):
            continue
        item_id = str(row.get("id") or "")
        state = normalize_state_entry(state_items.get(item_id))
        merged.append(
            {
                **row,
                "workflow_state": state,
                "workflow_status": state.get("status"),
                "workflow_owner": state.get("owner"),
                "workflow_note": state.get("note"),
                "workflow_updated_at_utc": state.get("updated_at_utc"),
                "is_open": state.get("status") != "resolved",
            }
        )

    merged.sort(
        key=lambda row: (
            STATUS_ORDER.get(str(row.get("workflow_status") or "new"), 99),
            int(row.get("priority") or 99),
            str(row.get("title") or ""),
        )
    )
    return merged


def summarize_statuses(items: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {status: 0 for status in ALLOWED_STATUSES}
    open_count = 0
    for row in items:
        status = str(row.get("workflow_status") or "new")
        if status in counts:
            counts[status] += 1
        if row.get("is_open"):
            open_count += 1

    return {
        "status_counts": counts,
        "open_actions": open_count,
        "resolved_actions": counts["resolved"],
    }


def build_handoff(items: list[dict[str, Any]]) -> dict[str, Any]:
    open_items = [row for row in items if isinstance(row, dict) and row.get("is_open")]
    top_open = open_items[:5]
    return {
        "top_open_actions": [
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "priority": row.get("priority"),
                "severity": row.get("severity"),
                "workflow_status": row.get("workflow_status"),
                "owner": row.get("workflow_owner"),
            }
            for row in top_open
        ],
        "open_action_count": len(open_items),
    }


def build_worklist_payload(repo_root: Path) -> dict[str, Any]:
    queue_payload = build_action_queue_payload(repo_root)
    queue_items = queue_payload.get("items") if isinstance(queue_payload.get("items"), list) else []

    output_dir = repo_root / OUTPUT_DIR
    state_path = output_dir / STATE_JSON
    state_payload = ensure_state_store(state_path, queue_items)
    state_items = state_payload.get("items") if isinstance(state_payload.get("items"), dict) else {}

    merged_items = merge_items(queue_items, state_items)
    status_summary = summarize_statuses(merged_items)
    handoff = build_handoff(merged_items)

    return {
        "generated_at_utc": now_utc_iso(),
        "worklist_version": "v1.5-slice-2",
        "source_action_queue_version": queue_payload.get("action_queue_version"),
        "state_store": {
            "path": normalize_path(OUTPUT_DIR / STATE_JSON),
            "state_version": state_payload.get("state_version"),
        },
        "queue_summary": queue_payload.get("queue_summary"),
        "workflow_status_summary": status_summary,
        "operator_handoff": handoff,
        "items": merged_items,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    queue_summary = payload.get("queue_summary", {})
    workflow = payload.get("workflow_status_summary", {})
    handoff = payload.get("operator_handoff", {})
    items = payload.get("items", [])

    lines = [
        "# AI-RISA Operator Action Worklist (Slice 2)",
        "",
        f"Generated (UTC): {payload.get('generated_at_utc')}",
        f"Action Queue Version: {payload.get('source_action_queue_version')}",
        f"State Store: {payload.get('state_store')}",
        "",
        "## Queue Summary",
        f"- Queue Summary: {queue_summary}",
        "",
        "## Workflow Status Summary",
        f"- Status Counts: {workflow.get('status_counts')}",
        f"- Open Actions: {workflow.get('open_actions')}",
        f"- Resolved Actions: {workflow.get('resolved_actions')}",
        "",
        "## Operator Handoff",
        f"- Top Open Actions: {handoff.get('top_open_actions')}",
        f"- Open Action Count: {handoff.get('open_action_count')}",
        "",
        "## Worklist",
    ]

    if isinstance(items, list) and items:
        for row in items:
            if not isinstance(row, dict):
                continue
            lines.extend(
                [
                    f"- [{row.get('workflow_status')}] P{row.get('priority')} {row.get('title')}",
                    f"  Severity: {row.get('severity')}",
                    f"  Suggested Handling: {row.get('suggested_handling')}",
                    f"  Owner: {row.get('workflow_owner')}",
                    f"  Note: {row.get('workflow_note')}",
                    f"  Updated At: {row.get('workflow_updated_at_utc')}",
                    f"  Summary: {row.get('summary')}",
                ]
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

    payload = build_worklist_payload(repo_root)

    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / WORKLIST_JSON
    out_md = out_dir / WORKLIST_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] open_actions={count} top_open={title}".format(
            count=(payload.get("workflow_status_summary") or {}).get("open_actions"),
            title=((payload.get("operator_handoff") or {}).get("top_open_actions") or [{}])[0].get("title") if (payload.get("operator_handoff") or {}).get("top_open_actions") else None,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())