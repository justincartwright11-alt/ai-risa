"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch_outcome_ledger.py

v76.9: Operator follow-up action resolution closure completion finalization completion finalization dispatch outcome ledger.
Reads the frozen v76.8 dispatcher artifact and emits a deterministic outcome ledger (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Input artifact
FINALIZATION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch.json")

# Output artifacts
OUTCOME_LEDGER_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch_outcome_ledger.json")
OUTCOME_LEDGER_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch_outcome_ledger.md")

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def build_outcome_records(dispatches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    for dispatch in dispatches:
        # For v76.9, seed a single outcome per dispatch, attempt_number=1
        # Use deterministic timestamps for auditability
        attempted_at = completed_at = "2026-04-06T00:00:00Z"
        delivery_state = "sent" if dispatch["dispatch_state"] == "dispatch" else "skipped"
        result_code = "success" if delivery_state == "sent" else "noop"
        result_summary = "Dispatched to operator" if delivery_state == "sent" else "No dispatch required"
        records.append({
            "finalization_dispatch_outcome_id": f"FDOID-{dispatch['finalization_dispatch_id']}-1",
            "finalization_dispatch_id": dispatch["finalization_dispatch_id"],
            "finalization_queue_item_id": dispatch["finalization_queue_item_id"],
            "dedupe_key": dispatch["dedupe_key"],
            "dispatch_target": dispatch["dispatch_target"],
            "dispatch_channel": dispatch["dispatch_channel"],
            "dispatch_state": dispatch["dispatch_state"],
            "delivery_state": delivery_state,
            "result_code": result_code,
            "result_summary": result_summary,
            "attempt_number": 1,
            "attempted_at": attempted_at,
            "completed_at": completed_at,
            "suppression_reason": dispatch.get("suppression_reason")
        })
    return records

def deterministic_sort(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Sort by: finalization_dispatch_id, attempt_number
    def sort_key(item):
        return (
            item.get("finalization_dispatch_id", ""),
            item.get("attempt_number", 1)
        )
    return sorted(records, key=sort_key)

def write_json(records: List[Dict[str, Any]]):
    with open(OUTCOME_LEDGER_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md(records: List[Dict[str, Any]]):
    with open(OUTCOME_LEDGER_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Completion Finalization Dispatch Outcome Ledger\n\n")
        if not records:
            f.write("_No dispatch outcomes recorded._\n")
            return
        for rec in records:
            f.write(f"- **Finalization Dispatch Outcome ID:** {rec['finalization_dispatch_outcome_id']}\n")
            f.write(f"  - Finalization Dispatch ID: {rec['finalization_dispatch_id']}\n")
            f.write(f"  - Finalization Queue Item ID: {rec['finalization_queue_item_id']}\n")
            f.write(f"  - Dedupe Key: {rec['dedupe_key']}\n")
            f.write(f"  - Dispatch Target: {rec['dispatch_target']}\n")
            f.write(f"  - Dispatch Channel: {rec['dispatch_channel']}\n")
            f.write(f"  - Dispatch State: {rec['dispatch_state']}\n")
            f.write(f"  - Delivery State: {rec['delivery_state']}\n")
            f.write(f"  - Result Code: {rec['result_code']}\n")
            f.write(f"  - Result Summary: {rec['result_summary']}\n")
            f.write(f"  - Attempt Number: {rec['attempt_number']}\n")
            f.write(f"  - Attempted At: {rec['attempted_at']}\n")
            f.write(f"  - Completed At: {rec['completed_at']}\n")
            if rec["suppression_reason"]:
                f.write(f"  - Suppression Reason: {rec['suppression_reason']}\n")
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
    records = build_outcome_records(dispatches)
    records = deterministic_sort(records)
    write_json(records)
    write_md(records)
    print(f"Wrote finalization dispatch outcome ledger records.")
    print(f"SHA256 (JSON): {sha256_file(OUTCOME_LEDGER_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(OUTCOME_LEDGER_MD)}")

if __name__ == "__main__":
    main()
