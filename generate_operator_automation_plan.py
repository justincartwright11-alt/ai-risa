#!/usr/bin/env python3
"""
AI-RISA v1.6 Operator Automation (slice 2): automation policy overlay.

Builds a merged automation plan by overlaying local policy configuration on top
of the read-only automation queue and workflow worklist. This script does not
mutate workflow state or pipeline outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_operator_action_worklist import build_worklist_payload
from generate_operator_automation_queue import (
    OUTPUT_DIR as AUTOMATION_QUEUE_OUTPUT_DIR,
    OUTPUT_JSON as AUTOMATION_QUEUE_JSON,
    build_automation_queue_payload,
    age_hours,
    normalize_path,
)

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/automation")
POLICY_JSON = "operator_automation_policy.json"
PLAN_JSON = "operator_automation_plan.json"
PLAN_MD = "operator_automation_plan.md"

DEFAULT_POLICY = {
    "policy_version": "v1.6-slice-2",
    "thresholds": {
        "escalation_age_hours": {
            "acknowledged": 12,
            "deferred": 24,
        },
        "reminder_age_hours": {
            "acknowledged": 8,
            "deferred": 18,
        },
        "stale_freshness_states": [
            "stale",
            "stale_critical",
            "missing",
            "unreadable",
        ],
    },
    "severity_weighting": {
        "critical": 100,
        "watch": 50,
        "info": 10,
    },
    "routing": {
        "escalation": {
            "critical": "ops-lead",
            "watch": "ops-primary",
            "info": "ops-monitor",
        },
        "priority_boost": {
            "critical": "ops-lead",
            "watch": "ops-primary",
            "info": "ops-monitor",
        },
        "reminder": {
            "critical": "ops-lead",
            "watch": "ops-primary",
            "info": "ops-monitor",
        },
        "handoff": {
            "default": "shift-handoff",
        },
    },
    "handoff": {
        "include_statuses": ["new", "acknowledged", "deferred"],
        "include_resolved": False,
        "max_items": 5,
    },
}

SEVERITY_ORDER = {
    "critical": 0,
    "watch": 1,
    "info": 2,
}

AUTOMATION_KIND_ORDER = {
    "escalation": 0,
    "priority_boost": 1,
    "reminder": 2,
    "handoff": 3,
}

REASON_FAMILY_MAP = {
    "acknowledged_item_aging": "acknowledged_aging",
    "policy_acknowledged_reminder_threshold": "acknowledged_aging",
    "deferred_item_aging": "deferred_aging",
    "policy_deferred_escalation_threshold": "deferred_aging",
    "stale_or_degraded_source_signal": "stale_signal",
    "policy_stale_signal_threshold": "stale_signal",
    "open_action_handoff": "handoff",
    "policy_handoff_inclusion_rules": "handoff",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate operator automation plan with policy overlay"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--worklist-output-dir",
        default="ops/action_queue",
        help="Worklist directory relative to repo root",
    )
    parser.add_argument(
        "--automation-output-dir",
        default=str(OUTPUT_DIR),
        help="Automation directory relative to repo root",
    )
    return parser.parse_args()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_utc_iso() -> str:
    return now_utc().isoformat()


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


def int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def normalize_policy(raw: Any) -> dict[str, Any]:
    policy = json.loads(json.dumps(DEFAULT_POLICY))
    if not isinstance(raw, dict):
        return policy

    thresholds = raw.get("thresholds") if isinstance(raw.get("thresholds"), dict) else {}
    escalation_age = thresholds.get("escalation_age_hours") if isinstance(thresholds.get("escalation_age_hours"), dict) else {}
    reminder_age = thresholds.get("reminder_age_hours") if isinstance(thresholds.get("reminder_age_hours"), dict) else {}
    stale_states = thresholds.get("stale_freshness_states") if isinstance(thresholds.get("stale_freshness_states"), list) else []

    policy["thresholds"]["escalation_age_hours"]["acknowledged"] = int_or_default(
        escalation_age.get("acknowledged"),
        policy["thresholds"]["escalation_age_hours"]["acknowledged"],
    )
    policy["thresholds"]["escalation_age_hours"]["deferred"] = int_or_default(
        escalation_age.get("deferred"),
        policy["thresholds"]["escalation_age_hours"]["deferred"],
    )
    policy["thresholds"]["reminder_age_hours"]["acknowledged"] = int_or_default(
        reminder_age.get("acknowledged"),
        policy["thresholds"]["reminder_age_hours"]["acknowledged"],
    )
    policy["thresholds"]["reminder_age_hours"]["deferred"] = int_or_default(
        reminder_age.get("deferred"),
        policy["thresholds"]["reminder_age_hours"]["deferred"],
    )
    if stale_states:
        policy["thresholds"]["stale_freshness_states"] = [str(x) for x in stale_states if str(x).strip()]

    severity_weighting = raw.get("severity_weighting") if isinstance(raw.get("severity_weighting"), dict) else {}
    for key in ("critical", "watch", "info"):
        policy["severity_weighting"][key] = int_or_default(
            severity_weighting.get(key),
            policy["severity_weighting"][key],
        )

    routing = raw.get("routing") if isinstance(raw.get("routing"), dict) else {}
    for kind in ("escalation", "priority_boost", "reminder"):
        route_map = routing.get(kind) if isinstance(routing.get(kind), dict) else {}
        for severity in ("critical", "watch", "info"):
            value = route_map.get(severity)
            if isinstance(value, str) and value.strip():
                policy["routing"][kind][severity] = value.strip()
    handoff_routing = routing.get("handoff") if isinstance(routing.get("handoff"), dict) else {}
    default_handoff = handoff_routing.get("default")
    if isinstance(default_handoff, str) and default_handoff.strip():
        policy["routing"]["handoff"]["default"] = default_handoff.strip()

    handoff = raw.get("handoff") if isinstance(raw.get("handoff"), dict) else {}
    include_statuses = handoff.get("include_statuses") if isinstance(handoff.get("include_statuses"), list) else []
    if include_statuses:
        policy["handoff"]["include_statuses"] = [str(x) for x in include_statuses if str(x).strip()]
    include_resolved = handoff.get("include_resolved")
    if isinstance(include_resolved, bool):
        policy["handoff"]["include_resolved"] = include_resolved
    policy["handoff"]["max_items"] = int_or_default(
        handoff.get("max_items"),
        policy["handoff"]["max_items"],
    )

    return policy


def ensure_policy_store(path: Path) -> dict[str, Any]:
    raw, err = safe_read_json(path)
    policy = normalize_policy(raw if err is None else None)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2, ensure_ascii=False)
    return policy


def route_for(policy: dict[str, Any], automation_kind: str, severity: str) -> str:
    routing = policy.get("routing") if isinstance(policy.get("routing"), dict) else {}
    if automation_kind == "handoff":
        return str(((routing.get("handoff") or {}) if isinstance(routing.get("handoff"), dict) else {}).get("default") or "shift-handoff")
    route_map = routing.get(automation_kind) if isinstance(routing.get(automation_kind), dict) else {}
    return str(route_map.get(severity) or route_map.get("info") or "ops-monitor")


def build_policy_candidate_from_item(item: dict[str, Any], policy: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    item_id = str(item.get("id") or "")
    title = str(item.get("title") or "Untitled action")
    severity = str(item.get("severity") or "info")
    status = str(item.get("workflow_status") or "new")
    updated_at = item.get("workflow_updated_at_utc")
    freshness_state = str(item.get("freshness_state") or "unknown")
    age = age_hours(updated_at, now)
    thresholds = policy.get("thresholds") if isinstance(policy.get("thresholds"), dict) else {}
    escalation_age = thresholds.get("escalation_age_hours") if isinstance(thresholds.get("escalation_age_hours"), dict) else {}
    reminder_age = thresholds.get("reminder_age_hours") if isinstance(thresholds.get("reminder_age_hours"), dict) else {}
    stale_states = set(thresholds.get("stale_freshness_states") or [])

    if status == "acknowledged" and age is not None and age >= int_or_default(reminder_age.get("acknowledged"), 8):
        candidates.append(
            {
                "id": f"{item_id}-policy-reminder",
                "source_item_id": item_id,
                "automation_kind": "reminder",
                "severity": "watch" if severity != "critical" else "critical",
                "priority": min(int(item.get("priority") or 99), 2),
                "title": f"Policy reminder for acknowledged item: {title}",
                "recommendation": "Issue a reminder based on the local acknowledged-item reminder threshold.",
                "reason": "policy_acknowledged_reminder_threshold",
                "source_paths": item.get("source_paths") or [],
                "workflow_context": {
                    "status": status,
                    "updated_at_utc": updated_at,
                    "age_hours": age,
                    "freshness_state": freshness_state,
                },
            }
        )

    if status == "deferred" and age is not None and age >= int_or_default(escalation_age.get("deferred"), 24):
        candidates.append(
            {
                "id": f"{item_id}-policy-deferred-boost",
                "source_item_id": item_id,
                "automation_kind": "priority_boost",
                "severity": severity if severity != "info" else "watch",
                "priority": min(int(item.get("priority") or 99), 2),
                "title": f"Policy boost for deferred item: {title}",
                "recommendation": "Promote this deferred item back into active review based on the local deferral threshold.",
                "reason": "policy_deferred_escalation_threshold",
                "source_paths": item.get("source_paths") or [],
                "workflow_context": {
                    "status": status,
                    "updated_at_utc": updated_at,
                    "age_hours": age,
                    "freshness_state": freshness_state,
                },
            }
        )

    if freshness_state in stale_states and status != "resolved":
        candidates.append(
            {
                "id": f"{item_id}-policy-stale-routing",
                "source_item_id": item_id,
                "automation_kind": "priority_boost",
                "severity": "critical" if freshness_state in {"stale_critical", "missing", "unreadable"} else "watch",
                "priority": min(int(item.get("priority") or 99), 2),
                "title": f"Policy stale-source routing: {title}",
                "recommendation": "Route this item using the local stale-source policy because the underlying signal is degraded.",
                "reason": "policy_stale_signal_threshold",
                "source_paths": item.get("source_paths") or [],
                "workflow_context": {
                    "status": status,
                    "updated_at_utc": updated_at,
                    "freshness_state": freshness_state,
                },
            }
        )

    return candidates


def build_policy_handoff(worklist: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    items = worklist.get("items") if isinstance(worklist.get("items"), list) else []
    handoff_policy = policy.get("handoff") if isinstance(policy.get("handoff"), dict) else {}
    include_statuses = set(str(x) for x in (handoff_policy.get("include_statuses") or []))
    include_resolved = bool(handoff_policy.get("include_resolved"))
    max_items = int_or_default(handoff_policy.get("max_items"), 5)

    eligible = []
    for row in items:
        if not isinstance(row, dict):
            continue
        status = str(row.get("workflow_status") or "new")
        if status == "resolved" and not include_resolved:
            continue
        if include_statuses and status not in include_statuses:
            continue
        if status != "resolved" and not row.get("is_open"):
            continue
        eligible.append(row)

    eligible.sort(
        key=lambda row: (
            int(row.get("priority") or 99),
            SEVERITY_ORDER.get(str(row.get("severity") or "info"), 9),
            str(row.get("title") or ""),
        )
    )

    top_items = eligible[:max_items]
    return {
        "route_target": route_for(policy, "handoff", "info"),
        "included_statuses": sorted(include_statuses),
        "include_resolved": include_resolved,
        "max_items": max_items,
        "top_open_actions": [
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "priority": row.get("priority"),
                "severity": row.get("severity"),
                "workflow_status": row.get("workflow_status"),
                "owner": row.get("workflow_owner"),
            }
            for row in top_items
        ],
    }


def overlay_candidate(candidate: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    severity = str(candidate.get("severity") or "info")
    kind = str(candidate.get("automation_kind") or "handoff")
    priority = int(candidate.get("priority") or 99)
    weighting = policy.get("severity_weighting") if isinstance(policy.get("severity_weighting"), dict) else {}
    score = int_or_default(weighting.get(severity), 0) + max(0, 25 - priority)
    return {
        **candidate,
        "route_target": route_for(policy, kind, severity),
        "policy_score": score,
        "policy_source": "base_queue",
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


def candidate_merge_key(candidate: dict[str, Any]) -> tuple[str, str, str]:
    source_item_id = str(candidate.get("source_item_id") or "__none__")
    automation_kind = str(candidate.get("automation_kind") or "handoff")
    reason = str(candidate.get("reason") or "unknown")
    return (
        source_item_id,
        automation_kind,
        REASON_FAMILY_MAP.get(reason, reason),
    )


def merge_candidates(
    base_candidates: list[dict[str, Any]], policy_candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str]] = []

    for row in base_candidates:
        if not isinstance(row, dict):
            continue
        key = candidate_merge_key(row)
        if key not in merged_by_key:
            order.append(key)
        merged_by_key[key] = row

    for row in policy_candidates:
        if not isinstance(row, dict):
            continue
        key = candidate_merge_key(row)
        if key not in merged_by_key:
            order.append(key)
        merged_by_key[key] = row

    return [merged_by_key[key] for key in order]


def sort_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda row: (
            int(row.get("priority") or 99),
            -int_or_default(row.get("policy_score"), 0),
            SEVERITY_ORDER.get(str(row.get("severity") or "info"), 9),
            AUTOMATION_KIND_ORDER.get(str(row.get("automation_kind") or "handoff"), 9),
            str(row.get("title") or ""),
        ),
    )


def summarize_plan(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    severity_counts = {"critical": 0, "watch": 0, "info": 0}
    route_counts: dict[str, int] = {}
    for row in candidates:
        severity = str(row.get("severity") or "info")
        route = str(row.get("route_target") or "unrouted")
        if severity in severity_counts:
            severity_counts[severity] += 1
        route_counts[route] = route_counts.get(route, 0) + 1

    top = candidates[0] if candidates else None
    return {
        "total_plan_items": len(candidates),
        "severity_counts": severity_counts,
        "route_counts": route_counts,
        "top_plan_item": {
            "id": top.get("id") if isinstance(top, dict) else None,
            "title": top.get("title") if isinstance(top, dict) else None,
            "priority": top.get("priority") if isinstance(top, dict) else None,
            "route_target": top.get("route_target") if isinstance(top, dict) else None,
            "policy_score": top.get("policy_score") if isinstance(top, dict) else None,
        },
    }


def build_automation_plan_payload(repo_root: Path, worklist_output_dir: Path, automation_output_dir: Path) -> dict[str, Any]:
    queue_payload = build_automation_queue_payload(repo_root, worklist_output_dir)
    worklist_payload = build_worklist_payload(repo_root, worklist_output_dir)
    policy_path = repo_root / automation_output_dir / POLICY_JSON
    policy = ensure_policy_store(policy_path)
    now = now_utc()

    base_candidates = queue_payload.get("candidates") if isinstance(queue_payload.get("candidates"), list) else []
    merged_candidates = [overlay_candidate(row, policy) for row in base_candidates if isinstance(row, dict)]
    policy_candidates: list[dict[str, Any]] = []

    worklist_items = worklist_payload.get("items") if isinstance(worklist_payload.get("items"), list) else []
    for row in worklist_items:
        if isinstance(row, dict) and row.get("is_open"):
            for candidate in build_policy_candidate_from_item(row, policy, now):
                policy_candidates.append(
                    {
                        **candidate,
                        "route_target": route_for(policy, str(candidate.get("automation_kind") or "handoff"), str(candidate.get("severity") or "info")),
                        "policy_score": int_or_default((policy.get("severity_weighting") or {}).get(candidate.get("severity")), 0) + max(0, 25 - int(candidate.get("priority") or 99)),
                        "policy_source": "policy_overlay",
                    }
                )

    handoff_plan = build_policy_handoff(worklist_payload, policy)
    policy_candidates.append(
        {
            "id": "policy-handoff-plan",
            "source_item_id": None,
            "automation_kind": "handoff",
            "severity": "info",
            "priority": 4,
            "title": "Generate policy-scoped handoff summary",
            "recommendation": "Generate a handoff summary using the local handoff inclusion rules and route it to the configured handoff target.",
            "reason": "policy_handoff_inclusion_rules",
            "source_paths": [normalize_path(worklist_output_dir / "operator_action_worklist.json")],
            "workflow_context": handoff_plan,
            "route_target": handoff_plan.get("route_target"),
            "policy_score": 10,
            "policy_source": "policy_overlay",
        }
    )

    merged_candidates = merge_candidates(merged_candidates, policy_candidates)
    merged_candidates = sort_candidates(dedupe_candidates(merged_candidates))

    return {
        "generated_at_utc": now.isoformat(),
        "automation_plan_version": "v1.6-slice-2",
        "source_automation_queue_version": queue_payload.get("automation_queue_version"),
        "policy_store": {
            "path": normalize_path(automation_output_dir / POLICY_JSON),
            "policy_version": policy.get("policy_version"),
        },
        "plan_summary": summarize_plan(merged_candidates),
        "policy_snapshot": policy,
        "automation_queue_snapshot": queue_payload.get("queue_summary"),
        "candidates": merged_candidates,
        "source_paths": {
            "automation_queue_json": normalize_path(AUTOMATION_QUEUE_OUTPUT_DIR / AUTOMATION_QUEUE_JSON),
            "worklist_json": normalize_path(worklist_output_dir / "operator_action_worklist.json"),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("plan_summary", {})
    policy = payload.get("policy_snapshot", {})
    queue_snapshot = payload.get("automation_queue_snapshot", {})
    candidates = payload.get("candidates", [])

    lines = [
        "# AI-RISA Operator Automation Plan (Slice 2)",
        "",
        f"Generated (UTC): {payload.get('generated_at_utc')}",
        f"Automation Queue Version: {payload.get('source_automation_queue_version')}",
        f"Policy Store: {payload.get('policy_store')}",
        "",
        "## Plan Summary",
        f"- Total Plan Items: {summary.get('total_plan_items')}",
        f"- Severity Counts: {summary.get('severity_counts')}",
        f"- Route Counts: {summary.get('route_counts')}",
        f"- Top Plan Item: {summary.get('top_plan_item')}",
        "",
        "## Policy Snapshot",
        f"- {policy}",
        "",
        "## Automation Queue Snapshot",
        f"- {queue_snapshot}",
        "",
        "## Automation Plan",
    ]

    if isinstance(candidates, list) and candidates:
        for row in candidates:
            if not isinstance(row, dict):
                continue
            lines.extend(
                [
                    f"- [{row.get('severity')}] P{row.get('priority')} {row.get('title')} ({row.get('automation_kind')})",
                    f"  Route Target: {row.get('route_target')}",
                    f"  Policy Score: {row.get('policy_score')}",
                    f"  Policy Source: {row.get('policy_source')}",
                    f"  Recommendation: {row.get('recommendation')}",
                    f"  Reason: {row.get('reason')}",
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
    automation_output_dir = Path(args.automation_output_dir)
    payload = build_automation_plan_payload(repo_root, worklist_output_dir, automation_output_dir)

    out_dir = repo_root / automation_output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / PLAN_JSON
    out_md = out_dir / PLAN_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] total_plan_items={total} top_plan_item={title}".format(
            total=(payload.get("plan_summary") or {}).get("total_plan_items"),
            title=((payload.get("plan_summary") or {}).get("top_plan_item") or {}).get("title"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
