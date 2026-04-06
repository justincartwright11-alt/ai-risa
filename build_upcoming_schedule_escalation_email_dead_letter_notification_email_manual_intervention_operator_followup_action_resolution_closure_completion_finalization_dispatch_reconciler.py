"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciler.py

v76.0: Operator follow-up action resolution closure completion finalization dispatch reconciler.
Reads the v75.9 finalization dispatch outcome ledger and reconciles it into the v75.8 finalization dispatch artifact.
Emits reconciled dispatch and reconciliation audit artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifacts
FINALIZATION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch.json")
OUTCOME_LEDGER_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_outcome_ledger.json")

# Output artifacts
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciled.json")
RECONCILED_DISPATCH_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciled.md")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciliation_audit.json")
RECONCILIATION_AUDIT_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciliation_audit.md")

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def reconcile_dispatch(dispatches: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]):
    # Map outcomes by (finalization_dispatch_id, attempt_number)
    outcome_map = {}
    for o in outcomes:
        key = (o["finalization_dispatch_id"], o["attempt_number"])
        outcome_map[key] = o
    reconciled = []
    audit = []
    for d in dispatches:
        # Find matching outcome (only attempt_number=1 for this slice)
        key = (d["finalization_dispatch_id"], 1)
        outcome = outcome_map.get(key)
        rec = d.copy()
        audit_entry = {
            "finalization_dispatch_id": d["finalization_dispatch_id"],
            "attempt_number": 1,
            "reconciled": False,
            "dispatch_state_before": d["dispatch_state"],
            "dispatch_state_after": d["dispatch_state"],
            "delivery_state": None,
            "result_code": None,
            "result_summary": None
        }
        if outcome:
            # Apply reconciliation rules
            audit_entry["reconciled"] = True
            audit_entry["delivery_state"] = outcome["delivery_state"]
            audit_entry["result_code"] = outcome["result_code"]
            audit_entry["result_summary"] = outcome["result_summary"]
            if outcome["delivery_state"] == "sent":
                rec["dispatch_state"] = "completed-success"
            elif outcome["delivery_state"] == "failed":
                rec["dispatch_state"] = "failed"
            elif outcome["delivery_state"] in ("skipped", "blocked"):
                rec["dispatch_state"] = outcome["delivery_state"]
            audit_entry["dispatch_state_after"] = rec["dispatch_state"]
        reconciled.append(rec)
        audit.append(audit_entry)
    return reconciled, audit

def write_json(obj: Any, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_md_dispatch(records: List[Dict[str, Any]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Dispatch (Reconciled)\n\n")
        if not records:
            f.write("_No reconciled dispatch records._\n")
            return
        for rec in records:
            f.write(f"- **Finalization Dispatch ID:** {rec['finalization_dispatch_id']}\n")
            f.write(f"  - Finalization Queue Item ID: {rec['finalization_queue_item_id']}\n")
            f.write(f"  - Dedupe Key: {rec['dedupe_key']}\n")
            f.write(f"  - Dispatch State: {rec['dispatch_state']}\n")
            f.write(f"  - Dispatch Target: {rec['dispatch_target']}\n")
            f.write(f"  - Dispatch Channel: {rec['dispatch_channel']}\n")
            f.write(f"  - Finalization Priority: {rec['finalization_priority']}\n")
            f.write(f"  - Next Finalization Action: {rec['next_finalization_action']}\n")
            if rec.get("suppression_reason"):
                f.write(f"  - Suppression Reason: {rec['suppression_reason']}\n")
            f.write("\n")

def write_md_audit(audit: List[Dict[str, Any]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Dispatch Reconciliation Audit\n\n")
        if not audit:
            f.write("_No reconciliation audit records._\n")
            return
        for entry in audit:
            f.write(f"- **Finalization Dispatch ID:** {entry['finalization_dispatch_id']}\n")
            f.write(f"  - Attempt Number: {entry['attempt_number']}\n")
            f.write(f"  - Reconciled: {entry['reconciled']}\n")
            f.write(f"  - Dispatch State Before: {entry['dispatch_state_before']}\n")
            f.write(f"  - Dispatch State After: {entry['dispatch_state_after']}\n")
            if entry["reconciled"]:
                f.write(f"  - Delivery State: {entry['delivery_state']}\n")
                f.write(f"  - Result Code: {entry['result_code']}\n")
                f.write(f"  - Result Summary: {entry['result_summary']}\n")
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
    dispatches = load_json_array(FINALIZATION_DISPATCH_JSON)
    outcomes = load_json_array(OUTCOME_LEDGER_JSON)
    reconciled, audit = reconcile_dispatch(dispatches, outcomes)
    write_json(reconciled, RECONCILED_DISPATCH_JSON)
    write_json(audit, RECONCILIATION_AUDIT_JSON)
    write_md_dispatch(reconciled, RECONCILED_DISPATCH_MD)
    write_md_audit(audit, RECONCILIATION_AUDIT_MD)
    print(f"Wrote reconciled dispatch and reconciliation audit.")
    print(f"SHA256 (Reconciled JSON): {sha256_file(RECONCILED_DISPATCH_JSON)}")
    print(f"SHA256 (Reconciled MD):   {sha256_file(RECONCILED_DISPATCH_MD)}")
    print(f"SHA256 (Audit JSON):      {sha256_file(RECONCILIATION_AUDIT_JSON)}")
    print(f"SHA256 (Audit MD):        {sha256_file(RECONCILIATION_AUDIT_MD)}")

if __name__ == "__main__":
    main()
