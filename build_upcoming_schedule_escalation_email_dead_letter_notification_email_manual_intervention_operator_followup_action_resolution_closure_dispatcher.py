"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_dispatcher.py

v74.8: Operator follow-up action resolution closure dispatcher.
Reads the frozen v74.7 closure queue and emits canonical closure dispatch artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input: v74.7 closure queue artifact
CLOSURE_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_queue.json")
# Outputs: v74.8 closure dispatch artifacts
CLOSURE_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch.json")
CLOSURE_DISPATCH_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_dispatch.md")

CLOSURE_PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
CLOSURE_STATE_ORDER = {"completed-success": 0, "pending-close": 1}

REQUIRED_FIELDS = [
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

def load_closure_queue() -> List[Dict[str, Any]]:
    if not CLOSURE_QUEUE_JSON.exists():
        return []
    with open(CLOSURE_QUEUE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def build_closure_dispatch_records(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    seen = set()
    for item in queue:
        # Compose unique key for dispatch
        key = (item["closure_queue_item_id"], item.get("dispatch_target"), item.get("dispatch_channel", "operator_manual"))
        if key in seen:
            continue
        seen.add(key)
        # Decide dispatch intent (for now, always 'dispatch' if eligible)
        dispatch_state = "dispatch"
        suppression_reason = ""
        # Deterministic closure_dispatch_id: SHA256 of closure_queue_item_id + dispatch_target + dispatch_channel
        id_basis = f"{item['closure_queue_item_id']}|{item.get('dispatch_target')}|{item.get('dispatch_channel', 'operator_manual')}"
        closure_dispatch_id = hashlib.sha256(id_basis.encode("utf-8")).hexdigest()
        record = {
            "closure_dispatch_id": closure_dispatch_id,
            "closure_queue_item_id": item["closure_queue_item_id"],
            "dedupe_key": item["dedupe_key"],
            "dispatch_state": dispatch_state,
            "dispatch_target": item.get("dispatch_target"),
            "dispatch_channel": item.get("dispatch_channel", "operator_manual"),
            "closure_priority": item.get("closure_priority"),
            "next_closure_action": item.get("next_closure_action"),
            "suppression_reason": suppression_reason,
        }
        records.append(record)
    # Deterministic ordering
    records.sort(key=lambda x: (
        CLOSURE_PRIORITY_ORDER.get(x["closure_priority"], 99),
        x["closure_queue_item_id"],
        x["dispatch_target"] or ""
    ))
    return records

def write_json(records: List[Dict[str, Any]]):
    with open(CLOSURE_DISPATCH_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md(records: List[Dict[str, Any]]):
    with open(CLOSURE_DISPATCH_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Dispatch\n\n")
        if not records:
            f.write("_No closure dispatch records found._\n")
            return
        headers = REQUIRED_FIELDS
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
    queue = load_closure_queue()
    records = build_closure_dispatch_records(queue)
    write_json(records)
    write_md(records)
    print(f"Wrote {len(records)} closure dispatch records.")
    print(f"SHA256 (JSON): {sha256_file(CLOSURE_DISPATCH_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(CLOSURE_DISPATCH_MD)}")

if __name__ == "__main__":
    main()
