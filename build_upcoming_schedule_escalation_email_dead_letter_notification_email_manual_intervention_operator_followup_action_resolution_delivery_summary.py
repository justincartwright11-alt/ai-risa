"""
v74.6-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-action-resolution-delivery-summary

- Reads v74.2 queue, v74.3 dispatch, v74.4 outcome ledger, v74.5 reconciled dispatch & audit
- Produces deterministic operator-facing delivery summary for the resolution branch
- Emits:
    - delivery summary JSON/Markdown
- Enforces idempotence, stable counts, and no upstream mutation
"""

import json
import os
from collections import Counter

QUEUE_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_queue.json"
DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch.json"
OUTCOME_LEDGER_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_outcome_ledger.json"
RECONCILED_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciled.json"
AUDIT_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciliation_audit.json"
SUMMARY_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_delivery_summary.json"
SUMMARY_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_delivery_summary.md"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_md(lines, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def summarize_resolution_delivery():
    queue = load_json(QUEUE_PATH) if os.path.exists(QUEUE_PATH) else []
    dispatch = load_json(DISPATCH_PATH) if os.path.exists(DISPATCH_PATH) else []
    outcome = load_json(OUTCOME_LEDGER_PATH) if os.path.exists(OUTCOME_LEDGER_PATH) else []
    reconciled = load_json(RECONCILED_PATH) if os.path.exists(RECONCILED_PATH) else []
    audit = load_json(AUDIT_PATH) if os.path.exists(AUDIT_PATH) else []

    summary = {
        "total_queued": len(queue),
        "total_dispatched": len(dispatch),
        "total_outcomes": len(outcome),
        "total_reconciled": len(reconciled),
        "total_audits": len(audit),
        "by_delivery_state": Counter(),
        "by_dispatch_state": Counter(),
        "outstanding_resolution": 0,
        "outstanding_items": []
    }
    for o in outcome:
        summary["by_delivery_state"][o.get("delivery_state", "unknown")] += 1
    for r in reconciled:
        summary["by_dispatch_state"][r.get("dispatch_state", "unknown")] += 1
        # Outstanding = not delivered
        if r.get("dispatch_state") != "delivered":
            summary["outstanding_resolution"] += 1
            summary["outstanding_items"].append(r.get("resolution_queue_item_id"))
    summary["by_delivery_state"] = dict(summary["by_delivery_state"])
    summary["by_dispatch_state"] = dict(summary["by_dispatch_state"])
    return summary

def summary_to_md(summary):
    lines = ["# Operator Follow-up Action Resolution Delivery Summary", ""]
    lines.append(f"Total Queued: {summary['total_queued']}")
    lines.append(f"Total Dispatched: {summary['total_dispatched']}")
    lines.append(f"Total Outcomes: {summary['total_outcomes']}")
    lines.append(f"Total Reconciled: {summary['total_reconciled']}")
    lines.append(f"Total Audits: {summary['total_audits']}")
    lines.append("")
    lines.append("## By Delivery State")
    for k, v in summary["by_delivery_state"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## By Dispatch State")
    for k, v in summary["by_dispatch_state"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append(f"Outstanding Resolution: {summary['outstanding_resolution']}")
    if summary["outstanding_items"]:
        lines.append("Outstanding Items:")
        for item in summary["outstanding_items"]:
            lines.append(f"- {item}")
    return lines

def main():
    summary = summarize_resolution_delivery()
    write_json(summary, SUMMARY_PATH)
    write_md(summary_to_md(summary), SUMMARY_MD_PATH)

if __name__ == "__main__":
    main()
