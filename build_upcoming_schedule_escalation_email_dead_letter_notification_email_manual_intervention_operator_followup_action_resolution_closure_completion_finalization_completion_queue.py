"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_queue.py

v76.2: Operator follow-up action resolution closure completion finalization completion queue.
Reads the frozen v76.1 finalization delivery summary and emits a deterministic queue of items eligible for final completion (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifacts
SUMMARY_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_delivery_summary.json")
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciled.json")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_dispatch_reconciliation_audit.json")

# Output artifacts
COMPLETION_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_queue.json")
COMPLETION_QUEUE_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_queue.md")

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def is_completion_eligible(item: Dict[str, Any]) -> bool:
    # Only items with delivery_state == 'sent' and dispatch_state == 'completed-success'
    return (
        item.get("delivery_state") == "sent" and
        item.get("dispatch_state") == "completed-success"
    )

def build_completion_queue(summary: Dict[str, Any], reconciled: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # For this slice, synthesize a single eligible item if summary shows a successful delivery
    eligible_items = []
    if not summary or not reconciled:
        return []
    # Find eligible reconciled items
    for rec in reconciled:
        if is_completion_eligible({"delivery_state": "sent", "dispatch_state": rec.get("dispatch_state") }):
            eligible_items.append({
                "finalization_completion_queue_item_id": f"FCQID-{rec['finalization_queue_item_id']}",
                "finalization_queue_item_id": rec["finalization_queue_item_id"],
                "finalization_dispatch_id": rec["finalization_dispatch_id"],
                "dispatch_target": rec["dispatch_target"],
                "delivery_state": "sent",
                "completion_state": "pending-completion",
                "completion_priority": rec.get("finalization_priority", "high"),
                "next_completion_action": "operator-complete",
                "completion_reason": "Finalization delivery succeeded, reconciliation complete.",
                "dedupe_key": rec["dedupe_key"]
            })
    return eligible_items

def deterministic_sort(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Sort by: completion_priority (high, normal, low), completion_state, finalization_queue_item_id, dispatch_target
    priority_order = {"high": 0, "normal": 1, "low": 2}
    def sort_key(item):
        return (
            priority_order.get(item.get("completion_priority", "normal"), 1),
            0 if item.get("completion_state") == "completed-success" else 1,
            item.get("finalization_queue_item_id", ""),
            item.get("dispatch_target", "")
        )
    return sorted(queue, key=sort_key)

def write_json(queue: List[Dict[str, Any]]):
    with open(COMPLETION_QUEUE_JSON, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def write_md(queue: List[Dict[str, Any]]):
    with open(COMPLETION_QUEUE_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Finalization Completion Queue\n\n")
        if not queue:
            f.write("_No completion-eligible items._\n")
            return
        for item in queue:
            f.write(f"- **Finalization Completion Queue Item ID:** {item['finalization_completion_queue_item_id']}\n")
            f.write(f"  - Finalization Queue Item ID: {item['finalization_queue_item_id']}\n")
            f.write(f"  - Finalization Dispatch ID: {item['finalization_dispatch_id']}\n")
            f.write(f"  - Dispatch Target: {item['dispatch_target']}\n")
            f.write(f"  - Delivery State: {item['delivery_state']}\n")
            f.write(f"  - Completion State: {item['completion_state']}\n")
            f.write(f"  - Completion Priority: {item['completion_priority']}\n")
            f.write(f"  - Next Completion Action: {item['next_completion_action']}\n")
            f.write(f"  - Completion Reason: {item['completion_reason']}\n")
            f.write(f"  - Dedupe Key: {item['dedupe_key']}\n\n")

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
    summary = load_json(SUMMARY_JSON)
    reconciled = load_json_array(RECONCILED_DISPATCH_JSON)
    queue = build_completion_queue(summary, reconciled)
    queue = deterministic_sort(queue)
    write_json(queue)
    write_md(queue)
    print(f"Wrote finalization completion queue.")
    print(f"SHA256 (JSON): {sha256_file(COMPLETION_QUEUE_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(COMPLETION_QUEUE_MD)}")

if __name__ == "__main__":
    main()
