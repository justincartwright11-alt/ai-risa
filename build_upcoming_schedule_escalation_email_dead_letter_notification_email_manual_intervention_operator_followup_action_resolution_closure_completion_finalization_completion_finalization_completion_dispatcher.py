"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatcher.py

v77.3: Operator follow-up action resolution closure completion finalization completion finalization completion dispatcher.
Reads the frozen v77.2 completion queue and emits deterministic dispatch intent artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifact
COMPLETION_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_queue.json")

# Output artifacts
COMPLETION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch.json")
COMPLETION_DISPATCH_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch.md")

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
        dispatch_state = "dispatch"
        suppression_reason = None
        records.append({
            "completion_dispatch_id": f"CDID-{item['completion_queue_item_id']}",
            "completion_queue_item_id": item["completion_queue_item_id"],
            "dedupe_key": item["dedupe_key"],
            "dispatch_state": dispatch_state,
            "dispatch_target": item["dispatch_target"],
            "dispatch_channel": "operator-ui",
            "completion_priority": item["completion_priority"],
            "next_completion_action": item["next_completion_action"],
            "suppression_reason": suppression_reason
        })
    return records

def deterministic_sort(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    priority_order = {"high": 0, "normal": 1, "low": 2}
    def sort_key(item):
        return (
            priority_order.get(item.get("completion_priority", "normal"), 1),
            item.get("completion_queue_item_id", ""),
            item.get("dispatch_target", ""),
            item.get("dispatch_channel", "")
        )
    return sorted(records, key=sort_key)

def write_json(records: List[Dict[str, Any]]):
    with open(COMPLETION_DISPATCH_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md(records: List[Dict[str, Any]]):
    with open(COMPLETION_DISPATCH_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Completion Finalization Completion Dispatch\n\n")
        if not records:
            f.write("_No completion dispatches required._\n")
            return
        for rec in records:
            f.write(f"- **Completion Dispatch ID:** {rec['completion_dispatch_id']}\n")
            f.write(f"  - Completion Queue Item ID: {rec['completion_queue_item_id']}\n")
            f.write(f"  - Dedupe Key: {rec['dedupe_key']}\n")
            f.write(f"  - Dispatch State: {rec['dispatch_state']}\n")
            f.write(f"  - Dispatch Target: {rec['dispatch_target']}\n")
            f.write(f"  - Dispatch Channel: {rec['dispatch_channel']}\n")
            f.write(f"  - Completion Priority: {rec['completion_priority']}\n")
            f.write(f"  - Next Completion Action: {rec['next_completion_action']}\n")
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
    queue = load_json_array(COMPLETION_QUEUE_JSON)
    records = build_dispatch_records(queue)
    records = deterministic_sort(records)
    write_json(records)
    write_md(records)
    print(f"Wrote completion dispatch records.")
    print(f"SHA256 (JSON): {sha256_file(COMPLETION_DISPATCH_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(COMPLETION_DISPATCH_MD)}")

if __name__ == "__main__":
    main()
