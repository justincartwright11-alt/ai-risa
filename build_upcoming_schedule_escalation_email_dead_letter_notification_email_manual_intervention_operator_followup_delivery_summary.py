"""
v74.1-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-delivery-summary

- Reads v74.0 reconciled dispatch (JSON)
- Summarizes operator follow-up delivery outcomes
- Emits:
    - delivery summary JSON/Markdown
- Enforces idempotence on rerun
- No mutation of v74.0 or earlier artifacts
- Summary fields: total delivered, failed, pending, by channel/target, etc.
"""

import json
import os
from collections import Counter, defaultdict

RECONCILED_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch_reconciled.json"
SUMMARY_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_delivery_summary.json"
SUMMARY_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_delivery_summary.md"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_md(lines, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def summarize_dispatches(dispatches):
    summary = {
        "total": len(dispatches),
        "by_state": Counter(),
        "by_channel": Counter(),
        "by_target": Counter(),
        "delivered": 0,
        "failed": 0,
        "pending": 0,
    }
    for d in dispatches:
        state = d.get("dispatch_state", "unknown")
        channel = d.get("dispatch_channel", "unknown")
        target = d.get("dispatch_target", "unknown")
        summary["by_state"][state] += 1
        summary["by_channel"][channel] += 1
        summary["by_target"][target] += 1
        if state == "delivered":
            summary["delivered"] += 1
        elif state == "failed":
            summary["failed"] += 1
        else:
            summary["pending"] += 1
    # Convert Counters to dicts for JSON serialization
    summary["by_state"] = dict(summary["by_state"])
    summary["by_channel"] = dict(summary["by_channel"])
    summary["by_target"] = dict(summary["by_target"])
    return summary

def summary_to_md(summary):
    lines = ["# Operator Follow-up Delivery Summary", ""]
    lines.append(f"Total Dispatches: {summary['total']}")
    lines.append(f"Delivered: {summary['delivered']}")
    lines.append(f"Failed: {summary['failed']}")
    lines.append(f"Pending: {summary['pending']}")
    lines.append("")
    lines.append("## By State")
    for k, v in summary["by_state"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## By Channel")
    for k, v in summary["by_channel"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## By Target")
    for k, v in summary["by_target"].items():
        lines.append(f"- {k}: {v}")
    return lines

def main():
    if not os.path.exists(RECONCILED_PATH):
        raise FileNotFoundError("Reconciled dispatch file missing.")
    dispatches = load_json(RECONCILED_PATH)
    summary = summarize_dispatches(dispatches)
    write_json(summary, SUMMARY_PATH)
    write_md(summary_to_md(summary), SUMMARY_MD_PATH)

if __name__ == "__main__":
    main()
