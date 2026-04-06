"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_queue.py

v75.2: Operator follow-up action resolution closure completion queue.
Reads the frozen v75.1 closure delivery summary and emits canonical completion queue artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input: v75.1 closure delivery summary artifact
SUMMARY_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_delivery_summary.json")
# Outputs: v75.2 completion queue artifacts
COMPLETION_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_queue.json")
COMPLETION_QUEUE_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_queue.md")

COMPLETION_PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
COMPLETION_STATE_ORDER = {"completed-success": 0, "pending-complete": 1}

REQUIRED_FIELDS = [
    "completion_queue_item_id",
    "closure_queue_item_id",
    "closure_dispatch_id",
    "dispatch_target",
    "delivery_state",
    "completion_state",
    "completion_priority",
    "next_completion_action",
    "completion_reason",
    "dedupe_key",
]

def load_summary_object() -> Dict[str, Any]:
    if not SUMMARY_JSON.exists():
        return {}
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def is_completion_eligible(item: Dict[str, Any]) -> bool:
    # Only include items that are completion-eligible
    # Example logic: delivered successfully, reconciliation complete, no outstanding work, no blocked/failed/unresolved
    return (
        item.get("delivery_state") == "delivered-success"
        and item.get("completion_state", "completed-success") in ("completed-success", "pending-complete")
        and not item.get("blocked", False)
        and not item.get("failed", False)
        and not item.get("unresolved", False)
        and not item.get("has_open_dependency", False)
    )

def build_completion_queue(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Assume summary has a key 'outstanding_items' or similar for item-level context
    items = summary.get("outstanding_items", [])
    queue = []
    seen_dedupe = set()
    for item in items:
        if not is_completion_eligible(item):
            continue
        dedupe_key = item["dedupe_key"]
        if dedupe_key in seen_dedupe:
            continue
        seen_dedupe.add(dedupe_key)
        # Deterministic completion_queue_item_id: SHA256 of dedupe_key
        completion_queue_item_id = hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest()
        queue_item = {field: item.get(field) for field in REQUIRED_FIELDS}
        queue_item["completion_queue_item_id"] = completion_queue_item_id
        queue.append(queue_item)
    # Deterministic ordering
    queue.sort(key=lambda x: (
        COMPLETION_PRIORITY_ORDER.get(x["completion_priority"], 99),
        COMPLETION_STATE_ORDER.get(x.get("completion_state", "completed-success"), 99),
        x["closure_queue_item_id"],
        x["dispatch_target"]
    ))
    return queue

def write_json(queue: List[Dict[str, Any]]):
    with open(COMPLETION_QUEUE_JSON, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def write_md(queue: List[Dict[str, Any]]):
    with open(COMPLETION_QUEUE_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Queue\n\n")
        if not queue:
            f.write("_No completion-eligible items found._\n")
            return
        headers = REQUIRED_FIELDS
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "---|" * len(headers) + "\n")
        for item in queue:
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
    summary = load_summary_object()
    queue = build_completion_queue(summary)
    write_json(queue)
    write_md(queue)
    print(f"Wrote {len(queue)} completion-eligible items.")
    print(f"SHA256 (JSON): {sha256_file(COMPLETION_QUEUE_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(COMPLETION_QUEUE_MD)}")

if __name__ == "__main__":
    main()
