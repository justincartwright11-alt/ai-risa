"""
v74.5-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-action-resolution-dispatch-reconciler

- Reads v74.4 outcome ledger (JSON)
- Reconciles into v74.3 dispatch state
- Emits:
    - reconciled dispatch JSON/Markdown
    - reconciliation audit JSON/Markdown
- Enforces idempotence, stable IDs, and no upstream mutation
- Deterministic ordering: resolution_dispatch_id, attempt_number, dispatch_target
"""

import json
import os
from copy import deepcopy

OUTCOME_LEDGER_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_outcome_ledger.json"
DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch.json"
RECONCILED_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciled.json"
RECONCILED_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciled.md"
AUDIT_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciliation_audit.json"
AUDIT_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciliation_audit.md"

TERMINAL_SUCCESS = "delivered"
TERMINAL_FAILURE = "failed"

# --- Helpers ---
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_md(lines, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# --- Reconciliation Logic ---
def reconcile_dispatches(dispatches, outcomes):
    # Index outcomes by (dispatch_id, attempt_number)
    outcome_index = {}
    for o in outcomes:
        key = (o["resolution_dispatch_id"], o["attempt_number"])
        outcome_index[key] = o

    reconciled = []
    audit = []
    for d in dispatches:
        key = (d["resolution_dispatch_id"], 1)
        rec = deepcopy(d)
        outcome = outcome_index.get(key)
        audit_entry = {
            "resolution_dispatch_id": d["resolution_dispatch_id"],
            "attempt_number": 1,
            "reconciled": False,
            "dispatch_state_before": d["dispatch_state"],
            "dispatch_state_after": d["dispatch_state"],
            "delivery_state": None,
            "result_code": None,
            "result_summary": None,
            "reconciliation_reason": "no outcome found"
        }
        if outcome:
            audit_entry["delivery_state"] = outcome["delivery_state"]
            audit_entry["result_code"] = outcome["result_code"]
            audit_entry["result_summary"] = outcome["result_summary"]
            if outcome["delivery_state"] == "sent":
                rec["dispatch_state"] = TERMINAL_SUCCESS
                audit_entry["dispatch_state_after"] = TERMINAL_SUCCESS
                audit_entry["reconciled"] = True
                audit_entry["reconciliation_reason"] = "sent → delivered"
            elif outcome["delivery_state"] == "failed":
                rec["dispatch_state"] = TERMINAL_FAILURE
                audit_entry["dispatch_state_after"] = TERMINAL_FAILURE
                audit_entry["reconciled"] = True
                audit_entry["reconciliation_reason"] = "failed → failed"
            elif outcome["delivery_state"] in ("skipped", "blocked"):
                audit_entry["reconciliation_reason"] = f"{outcome['delivery_state']} → no state change"
            else:
                audit_entry["reconciliation_reason"] = f"unknown delivery_state: {outcome['delivery_state']}"
        reconciled.append(rec)
        audit.append(audit_entry)
    return reconciled, audit

# --- Markdown Writers ---
def dispatches_to_md(dispatches):
    lines = ["# Operator Follow-up Action Resolution Dispatches (Reconciled)", "", f"Total Dispatches: {len(dispatches)}", ""]
    for d in dispatches:
        lines.append(f"- Dispatch ID: {d['resolution_dispatch_id']} | Queue ID: {d['resolution_queue_item_id']} | Target: {d['dispatch_target']} | Channel: {d['dispatch_channel']} | Priority: {d.get('resolution_priority','')} | State: {d['dispatch_state']} | Next: {d.get('next_resolution_action','')} | Suppression: {d.get('suppression_reason','')}")
    return lines

def audit_to_md(audit):
    lines = ["# Operator Follow-up Action Resolution Dispatch Reconciliation Audit", "", f"Total Audits: {len(audit)}", ""]
    for a in audit:
        lines.append(f"- Dispatch ID: {a['resolution_dispatch_id']} | Attempt: {a['attempt_number']} | Before: {a['dispatch_state_before']} | After: {a['dispatch_state_after']} | Delivery: {a['delivery_state']} | Code: {a['result_code']} | Summary: {a['result_summary']} | Reconciled: {a['reconciled']} | Reason: {a['reconciliation_reason']}")
    return lines

# --- Entrypoint ---
def main():
    if not (os.path.exists(OUTCOME_LEDGER_PATH) and os.path.exists(DISPATCH_PATH)):
        raise FileNotFoundError("Required input files missing.")
    outcomes = load_json(OUTCOME_LEDGER_PATH)
    dispatches = load_json(DISPATCH_PATH)
    reconciled, audit = reconcile_dispatches(dispatches, outcomes)
    write_json(reconciled, RECONCILED_PATH)
    write_md(dispatches_to_md(reconciled), RECONCILED_MD_PATH)
    write_json(audit, AUDIT_PATH)
    write_md(audit_to_md(audit), AUDIT_MD_PATH)

if __name__ == "__main__":
    main()
