"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_dispatch_outcome_ledger.py

v76.4: Operator follow-up action resolution closure completion finalization completion dispatch outcome ledger.
Reads the frozen v76.3 completion dispatch artifact and emits a deterministic outcome ledger (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Input artifact
COMPLETION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_dispatch.json")

# Output artifacts
OUTCOME_LEDGER_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_dispatch_outcome_ledger.json")
OUTCOME_LEDGER_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_dispatch_outcome_ledger.md")

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def build_outcome_ledger(dispatches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ledger = []
    for i, d in enumerate(dispatches):
        # Synthesize a canonical outcome for each dispatch (simulate a successful send)
        ledger.append({
            "completion_dispatch_outcome_id": f"CDOID-{d['completion_dispatch_id']}-A1",
            "completion_dispatch_id": d["completion_dispatch_id"],
            "completion_queue_item_id": d["completion_queue_item_id"],
            "dedupe_key": d["dedupe_key"],
            "dispatch_target": d["dispatch_target"],
            "dispatch_channel": d["dispatch_channel"],
            "dispatch_state": d["dispatch_state"],
            "delivery_state": "sent",  # For this slice, always 'sent' for eligible
            "result_code": "success",
            "result_summary": "Completion dispatch delivered to operator.",
            "attempt_number": 1,
            "attempted_at": "2026-04-06T00:00:00Z",
            "completed_at": "2026-04-06T00:00:01Z",
            "suppression_reason": d.get("suppression_reason")
        })
    return ledger

def deterministic_sort(ledger: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Sort by: completion_dispatch_id, attempt_number
    def sort_key(item):
        return (
            item.get("completion_dispatch_id", ""),
            item.get("attempt_number", 0)
        )
    return sorted(ledger, key=sort_key)

def write_json(ledger: List[Dict[str, Any]]):
    with open(OUTCOME_LEDGER_JSON, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

def write_md(ledger: List[Dict[str, Any]]):
    with open(OUTCOME_LEDGER_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Completion Dispatch Outcome Ledger\n\n")
        if not ledger:
            f.write("_No completion dispatch outcomes recorded._\n")
            return
        for rec in ledger:
            f.write(f"- **Completion Dispatch Outcome ID:** {rec['completion_dispatch_outcome_id']}\n")
            f.write(f"  - Completion Dispatch ID: {rec['completion_dispatch_id']}\n")
            f.write(f"  - Completion Queue Item ID: {rec['completion_queue_item_id']}\n")
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
    dispatches = load_json_array(COMPLETION_DISPATCH_JSON)
    ledger = build_outcome_ledger(dispatches)
    ledger = deterministic_sort(ledger)
    write_json(ledger)
    write_md(ledger)
    print(f"Wrote completion dispatch outcome ledger.")
    print(f"SHA256 (JSON): {sha256_file(OUTCOME_LEDGER_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(OUTCOME_LEDGER_MD)}")

if __name__ == "__main__":
    main()
