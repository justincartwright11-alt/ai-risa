"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_reconciler.py

v77.5: Operator follow-up action resolution closure completion finalization completion finalization completion dispatch reconciler.
Reads the frozen v77.4 outcome ledger and v77.3 dispatcher artifacts, and emits deterministic reconciled dispatch and reconciliation audit artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifacts
COMPLETION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch.json")
OUTCOME_LEDGER_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_outcome_ledger.json")

# Output artifacts
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_reconciled.json")
RECONCILED_DISPATCH_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_reconciled.md")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_reconciliation_audit.json")
RECONCILIATION_AUDIT_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_reconciliation_audit.md")

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def reconcile_dispatch(dispatches: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]):
    # Map outcomes by (completion_dispatch_id, attempt_number)
    outcome_map = {}
    for o in outcomes:
        key = (o["completion_dispatch_id"], o["attempt_number"])
        outcome_map[key] = o
    reconciled = []
    audit = []
    for d in dispatches:
        key = (d["completion_dispatch_id"], 1)
        outcome = outcome_map.get(key)
        rec = d.copy()
        audit_entry = {
            "completion_dispatch_id": d["completion_dispatch_id"],
            "attempt_number": 1,
            "pre_state": d["dispatch_state"],
            "post_state": None,
            "delivery_state": None,
            "result_code": None,
            "result_summary": None,
            "reconciliation_applied": False
        }
        if outcome:
            # Apply reconciliation policy
            rec["delivery_state"] = outcome["delivery_state"]
            rec["result_code"] = outcome["result_code"]
            rec["result_summary"] = outcome["result_summary"]
            rec["attempt_number"] = 1
            rec["attempted_at"] = outcome["attempted_at"]
            rec["completed_at"] = outcome["completed_at"]
            rec["suppression_reason"] = outcome.get("suppression_reason")
            # State transitions
            if outcome["delivery_state"] == "sent":
                rec["dispatch_state"] = "success"
            elif outcome["delivery_state"] == "failed":
                rec["dispatch_state"] = "failure"
            elif outcome["delivery_state"] in ("skipped", "blocked"):
                rec["dispatch_state"] = d["dispatch_state"]  # never false success
            else:
                rec["dispatch_state"] = d["dispatch_state"]
            audit_entry["post_state"] = rec["dispatch_state"]
            audit_entry["delivery_state"] = outcome["delivery_state"]
            audit_entry["result_code"] = outcome["result_code"]
            audit_entry["result_summary"] = outcome["result_summary"]
            audit_entry["reconciliation_applied"] = True
        else:
            audit_entry["post_state"] = d["dispatch_state"]
        reconciled.append(rec)
        audit.append(audit_entry)
    return reconciled, audit

def deterministic_sort(records: List[Dict[str, Any]], keys: list) -> List[Dict[str, Any]]:
    def sort_key(item):
        return tuple(item.get(k, "") for k in keys)
    return sorted(records, key=sort_key)

def write_json(records: List[Dict[str, Any]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md_dispatch(records: List[Dict[str, Any]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Reconciled Operator Follow-Up Action Resolution Closure Completion Finalization Completion Finalization Completion Dispatch\n\n")
        if not records:
            f.write("_No reconciled completion dispatch records._\n")
            return
        for rec in records:
            f.write(f"- **Completion Dispatch ID:** {rec['completion_dispatch_id']}\n")
            f.write(f"  - Completion Queue Item ID: {rec['completion_queue_item_id']}\n")
            f.write(f"  - Dedupe Key: {rec['dedupe_key']}\n")
            f.write(f"  - Dispatch Target: {rec['dispatch_target']}\n")
            f.write(f"  - Dispatch Channel: {rec['dispatch_channel']}\n")
            f.write(f"  - Dispatch State: {rec['dispatch_state']}\n")
            if 'delivery_state' in rec:
                f.write(f"  - Delivery State: {rec['delivery_state']}\n")
            if 'result_code' in rec:
                f.write(f"  - Result Code: {rec['result_code']}\n")
            if 'result_summary' in rec:
                f.write(f"  - Result Summary: {rec['result_summary']}\n")
            if 'attempt_number' in rec:
                f.write(f"  - Attempt Number: {rec['attempt_number']}\n")
            if 'attempted_at' in rec:
                f.write(f"  - Attempted At: {rec['attempted_at']}\n")
            if 'completed_at' in rec:
                f.write(f"  - Completed At: {rec['completed_at']}\n")
            if rec.get("suppression_reason"):
                f.write(f"  - Suppression Reason: {rec['suppression_reason']}\n")
            f.write("\n")

def write_md_audit(records: List[Dict[str, Any]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Completion Dispatch Reconciliation Audit\n\n")
        if not records:
            f.write("_No reconciliation audit records._\n")
            return
        for rec in records:
            f.write(f"- **Completion Dispatch ID:** {rec['completion_dispatch_id']}\n")
            f.write(f"  - Attempt Number: {rec['attempt_number']}\n")
            f.write(f"  - Pre-State: {rec['pre_state']}\n")
            f.write(f"  - Post-State: {rec['post_state']}\n")
            f.write(f"  - Delivery State: {rec['delivery_state']}\n")
            f.write(f"  - Result Code: {rec['result_code']}\n")
            f.write(f"  - Result Summary: {rec['result_summary']}\n")
            f.write(f"  - Reconciliation Applied: {rec['reconciliation_applied']}\n\n")

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
    dispatches = load_json_array(COMPLETION_DISPATCH_JSON)
    outcomes = load_json_array(OUTCOME_LEDGER_JSON)
    reconciled, audit = reconcile_dispatch(dispatches, outcomes)
    reconciled = deterministic_sort(reconciled, ["completion_dispatch_id", "attempt_number"])
    audit = deterministic_sort(audit, ["completion_dispatch_id", "attempt_number"])
    write_json(reconciled, RECONCILED_DISPATCH_JSON)
    write_md_dispatch(reconciled, RECONCILED_DISPATCH_MD)
    write_json(audit, RECONCILIATION_AUDIT_JSON)
    write_md_audit(audit, RECONCILIATION_AUDIT_MD)
    print(f"Wrote reconciled completion dispatch and audit records.")
    print(f"SHA256 (Reconciled JSON): {sha256_file(RECONCILED_DISPATCH_JSON)}")
    print(f"SHA256 (Reconciled MD):   {sha256_file(RECONCILED_DISPATCH_MD)}")
    print(f"SHA256 (Audit JSON):      {sha256_file(RECONCILIATION_AUDIT_JSON)}")
    print(f"SHA256 (Audit MD):        {sha256_file(RECONCILIATION_AUDIT_MD)}")

if __name__ == "__main__":
    main()
