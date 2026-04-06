"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_delivery_summary.py

v76.1: Operator follow-up action resolution closure completion finalization delivery summary.
Reads the frozen finalization branch artifacts and emits a deterministic summary (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifacts
FINALIZATION_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_queue.json")
FINALIZATION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch.json")
OUTCOME_LEDGER_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_outcome_ledger.json")
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciled.json")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciliation_audit.json")

# Output artifacts
SUMMARY_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_delivery_summary.json")
SUMMARY_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_delivery_summary.md")

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def build_summary():
    queue = load_json_array(FINALIZATION_QUEUE_JSON)
    dispatch = load_json_array(FINALIZATION_DISPATCH_JSON)
    outcome = load_json_array(OUTCOME_LEDGER_JSON)
    reconciled = load_json_array(RECONCILED_DISPATCH_JSON)
    audit = load_json_array(RECONCILIATION_AUDIT_JSON)
    # Totals
    total_queued = len(queue)
    total_dispatched = len(dispatch)
    total_outcomes = len(outcome)
    total_reconciled = len(reconciled)
    total_audits = len(audit)
    # By delivery state
    by_delivery_state = {}
    for o in outcome:
        state = o.get("delivery_state", "unknown")
        by_delivery_state[state] = by_delivery_state.get(state, 0) + 1
    # By dispatch state
    by_dispatch_state = {}
    for r in reconciled:
        state = r.get("dispatch_state", "unknown")
        by_dispatch_state[state] = by_dispatch_state.get(state, 0) + 1
    # Outstanding finalization items (not completed-success, failed, skipped, or blocked)
    completed_ids = {r.get("finalization_queue_item_id") for r in reconciled}
    outstanding_items = [q for q in queue if q.get("finalization_queue_item_id") not in completed_ids]
    summary = {
        "total_queued": total_queued,
        "total_dispatched": total_dispatched,
        "total_outcomes": total_outcomes,
        "total_reconciled": total_reconciled,
        "total_audits": total_audits,
        "by_delivery_state": by_delivery_state,
        "by_dispatch_state": by_dispatch_state,
        "reconciliation_applied": sum(1 for a in audit if a.get("reconciled")),
        "outstanding_finalization_items": len(outstanding_items),
        "outstanding_items": outstanding_items,
    }
    return summary

def write_json(summary: Dict[str, Any]):
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

def write_md(summary: Dict[str, Any]):
    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Delivery Summary\n\n")
        f.write(f"**Total queued:** {summary['total_queued']}\n\n")
        f.write(f"**Total dispatched:** {summary['total_dispatched']}\n\n")
        f.write(f"**Total outcomes:** {summary['total_outcomes']}\n\n")
        f.write(f"**Total reconciled:** {summary['total_reconciled']}\n\n")
        f.write(f"**Total audits:** {summary['total_audits']}\n\n")
        f.write(f"**Reconciliation applied:** {summary['reconciliation_applied']}\n\n")
        f.write("## By delivery state\n")
        for k, v in summary["by_delivery_state"].items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## By dispatch state\n")
        for k, v in summary["by_dispatch_state"].items():
            f.write(f"- {k}: {v}\n")
        f.write(f"\n**Outstanding finalization items:** {summary['outstanding_finalization_items']}\n\n")
        if summary["outstanding_items"]:
            f.write("### Outstanding Items\n")
            for item in summary["outstanding_items"]:
                f.write(f"- {item.get('finalization_queue_item_id', '')} ({item.get('dedupe_key', '')})\n")
        else:
            f.write("_No outstanding finalization items._\n")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    summary = build_summary()
    write_json(summary)
    write_md(summary)
    print(f"Wrote finalization delivery summary.")
    print(f"SHA256 (JSON): {sha256_file(SUMMARY_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(SUMMARY_MD)}")

if __name__ == "__main__":
    main()
