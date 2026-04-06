"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_delivery_summary.py

v77.1: Operator follow-up action resolution closure completion finalization completion finalization delivery summary.
Reads the frozen finalization-dispatch branch and emits a deterministic operator-facing delivery summary (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifacts
FINALIZATION_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_queue.json")
FINALIZATION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch.json")
OUTCOME_LEDGER_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch_outcome_ledger.json")
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch_reconciled.json")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch_reconciliation_audit.json")

# Output artifacts
DELIVERY_SUMMARY_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_delivery_summary.json")
DELIVERY_SUMMARY_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_delivery_summary.md")

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def summarize_delivery(queue, dispatch, outcome, reconciled, audit):
    summary = {}
    summary["finalization_items_queued"] = len(queue)
    summary["finalization_items_dispatched"] = len(dispatch)
    # Delivery state counts from reconciled
    delivery_states = {"sent": 0, "failed": 0, "skipped": 0, "blocked": 0}
    for rec in reconciled:
        state = rec.get("delivery_state")
        if state in delivery_states:
            delivery_states[state] += 1
    summary["delivery_state_counts"] = delivery_states
    # Reconciliation applied count
    reconciliation_applied = sum(1 for a in audit if a.get("reconciliation_applied"))
    summary["reconciliation_applied"] = reconciliation_applied
    # Items still requiring operator attention: not terminal success
    attention = [rec["finalization_queue_item_id"] for rec in reconciled if rec.get("dispatch_state") != "success"]
    summary["finalization_items_requiring_operator_attention"] = sorted(attention)
    return summary

def write_json(obj: Dict[str, Any], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_md(summary: Dict[str, Any], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Completion Finalization Delivery Summary\n\n")
        f.write(f"- Finalization items queued: {summary['finalization_items_queued']}\n")
        f.write(f"- Finalization items dispatched: {summary['finalization_items_dispatched']}\n")
        f.write(f"- Delivery state counts:\n")
        for state, count in summary["delivery_state_counts"].items():
            f.write(f"    - {state}: {count}\n")
        f.write(f"- Reconciliation applied: {summary['reconciliation_applied']}\n")
        f.write(f"- Finalization items requiring operator attention: ")
        if summary["finalization_items_requiring_operator_attention"]:
            f.write(", ".join(summary["finalization_items_requiring_operator_attention"]))
        else:
            f.write("None")
        f.write("\n")

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
    queue = load_json_array(FINALIZATION_QUEUE_JSON)
    dispatch = load_json_array(FINALIZATION_DISPATCH_JSON)
    outcome = load_json_array(OUTCOME_LEDGER_JSON)
    reconciled = load_json_array(RECONCILED_DISPATCH_JSON)
    audit = load_json_array(RECONCILIATION_AUDIT_JSON)
    summary = summarize_delivery(queue, dispatch, outcome, reconciled, audit)
    write_json(summary, DELIVERY_SUMMARY_JSON)
    write_md(summary, DELIVERY_SUMMARY_MD)
    print(f"Wrote delivery summary.")
    print(f"SHA256 (JSON): {sha256_file(DELIVERY_SUMMARY_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(DELIVERY_SUMMARY_MD)}")

if __name__ == "__main__":
    main()
