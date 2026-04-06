"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatcher.py

v76.8: Operator follow-up action resolution closure completion finalization completion finalization dispatcher.
Reads the frozen v76.7 finalization queue and emits a deterministic dispatch intent artifact (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifact
FINALIZATION_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_queue.json")

# Output artifacts
FINALIZATION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch.json")
FINALIZATION_DISPATCH_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_dispatch.md")

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def build_dispatch_records(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    for item in queue:
        # Only dispatch for eligible items (should be all in the queue)
        dispatch_state = "dispatch"
        suppression_reason = None
        # Synthesize a canonical dispatch record
        records.append({
            "finalization_dispatch_id": f"FDID-{item['finalization_queue_item_id']}",
            "finalization_queue_item_id": item["finalization_queue_item_id"],
            "dedupe_key": item["dedupe_key"],
            "dispatch_state": dispatch_state,
            "dispatch_target": item["dispatch_target"],
            "dispatch_channel": "operator-ui",
            "finalization_priority": item["finalization_priority"],
            "next_finalization_action": item["next_finalization_action"],
            "suppression_reason": suppression_reason
        })
    return records

def deterministic_sort(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Sort by: finalization_priority, finalization_queue_item_id, dispatch_target, dispatch_channel
    priority_order = {"high": 0, "normal": 1, "low": 2}
    def sort_key(item):
        return (
            priority_order.get(item.get("finalization_priority", "normal"), 1),
            item.get("finalization_queue_item_id", ""),
            item.get("dispatch_target", ""),
            item.get("dispatch_channel", "")
        )
    return sorted(records, key=sort_key)

def write_json(records: List[Dict[str, Any]]):
    with open(FINALIZATION_DISPATCH_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md(records: List[Dict[str, Any]]):
    with open(FINALIZATION_DISPATCH_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Completion Finalization Dispatch\n\n")
        if not records:
            f.write("_No finalization dispatches required._\n")
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
    queue = load_json_array(FINALIZATION_QUEUE_JSON)
    records = build_dispatch_records(queue)
    records = deterministic_sort(records)
    write_json(records)
    write_md(records)
    print(f"Wrote finalization completion finalization dispatch records.")
    print(f"SHA256 (JSON): {sha256_file(FINALIZATION_DISPATCH_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(FINALIZATION_DISPATCH_MD)}")

if __name__ == "__main__":
    main()
