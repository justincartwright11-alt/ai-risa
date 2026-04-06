"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_dispatch_reconciler.py

v75.0: Operator follow-up action resolution closure dispatch reconciler.
Reads the frozen v74.9 closure dispatch outcome ledger and v74.8 closure dispatch, emits reconciled closure dispatch and reconciliation audit artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Inputs
CLOSURE_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch.json")
OUTCOME_LEDGER_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch_outcome_ledger.json")
# Outputs
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch_reconciled.json")
RECONCILED_DISPATCH_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch_reconciled.md")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch_reconciliation_audit.json")
RECONCILIATION_AUDIT_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch_reconciliation_audit.md")

REQUIRED_DISPATCH_FIELDS = [
    "closure_dispatch_id",
    "closure_queue_item_id",
    "dedupe_key",
    "dispatch_state",
    "dispatch_target",
    "dispatch_channel",
    "closure_priority",
    "next_closure_action",
    "suppression_reason",
]
REQUIRED_AUDIT_FIELDS = [
    "closure_dispatch_id",
    "attempt_number",
    "dispatch_state_before",
    "dispatch_state_after",
    "delivery_state",
    "result_code",
    "result_summary",
    "reconciliation_reason",
]

TERMINAL_SUCCESS = "sent"
TERMINAL_FAILURE = "failed"
TERMINAL_SKIPPED = "skipped"
TERMINAL_BLOCKED = "blocked"

# For deterministic test runs, use a fixed timestamp
FIXED_TIMESTAMP = "2026-04-06T12:00:00Z"

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def reconcile_dispatch(dispatches: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]):
    # Build lookup for outcome by closure_dispatch_id
    outcome_by_id = {(o["closure_dispatch_id"], o["attempt_number"]): o for o in outcomes}
    reconciled = []
    audit = []
    for d in dispatches:
        key = (d["closure_dispatch_id"], 1)  # Only attempt_number=1 for now
        before_state = d["dispatch_state"]
        if key in outcome_by_id:
            o = outcome_by_id[key]
            # Reconcile state
            if o["delivery_state"] == TERMINAL_SUCCESS:
                after_state = "delivered"
                reason = "sent → delivered"
            elif o["delivery_state"] == TERMINAL_FAILURE:
                after_state = "failed"
                reason = "failed outcome"
            elif o["delivery_state"] == TERMINAL_SKIPPED:
                after_state = "skipped"
                reason = "skipped outcome"
            elif o["delivery_state"] == TERMINAL_BLOCKED:
                after_state = "blocked"
                reason = "blocked outcome"
            else:
                after_state = before_state
                reason = "no terminal outcome"
            # Copy and update dispatch record
            rec = dict(d)
            rec["dispatch_state"] = after_state
            reconciled.append(rec)
            # Audit record
            audit.append({
                "closure_dispatch_id": d["closure_dispatch_id"],
                "attempt_number": 1,
                "dispatch_state_before": before_state,
                "dispatch_state_after": after_state,
                "delivery_state": o["delivery_state"],
                "result_code": o["result_code"],
                "result_summary": o["result_summary"],
                "reconciliation_reason": reason,
            })
        else:
            # No outcome, carry forward unchanged
            rec = dict(d)
            reconciled.append(rec)
    # Deterministic ordering
    reconciled.sort(key=lambda x: (x["closure_dispatch_id"]))
    audit.sort(key=lambda x: (x["closure_dispatch_id"], x["attempt_number"]))
    return reconciled, audit

def write_json(records: List[Dict[str, Any]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md(records: List[Dict[str, Any]], path: Path, headers: list, title: str, empty_msg: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        if not records:
            f.write(f"_{empty_msg}_\n")
            return
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "---|" * len(headers) + "\n")
        for item in records:
            row = [str(item.get(h, "")) for h in headers]
            f.write("| " + " | ".join(row) + " |\n")

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
    dispatches = load_json_array(CLOSURE_DISPATCH_JSON)
    outcomes = load_json_array(OUTCOME_LEDGER_JSON)
    reconciled, audit = reconcile_dispatch(dispatches, outcomes)
    write_json(reconciled, RECONCILED_DISPATCH_JSON)
    write_json(audit, RECONCILIATION_AUDIT_JSON)
    write_md(reconciled, RECONCILED_DISPATCH_MD, REQUIRED_DISPATCH_FIELDS, "Operator Follow-Up Action Resolution Closure Dispatch Reconciled", "No reconciled closure dispatch records found.")
    write_md(audit, RECONCILIATION_AUDIT_MD, REQUIRED_AUDIT_FIELDS, "Operator Follow-Up Action Resolution Closure Dispatch Reconciliation Audit", "No reconciliation audit records found.")
    print(f"Wrote {len(reconciled)} reconciled dispatch records, {len(audit)} audit records.")
    print(f"SHA256 (Reconciled JSON): {sha256_file(RECONCILED_DISPATCH_JSON)}")
    print(f"SHA256 (Reconciled MD):   {sha256_file(RECONCILED_DISPATCH_MD)}")
    print(f"SHA256 (Audit JSON):      {sha256_file(RECONCILIATION_AUDIT_JSON)}")
    print(f"SHA256 (Audit MD):        {sha256_file(RECONCILIATION_AUDIT_MD)}")

if __name__ == "__main__":
    main()
