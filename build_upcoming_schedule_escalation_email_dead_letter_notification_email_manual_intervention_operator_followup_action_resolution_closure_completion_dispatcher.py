"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_completion_dispatcher.py

v75.3: Operator follow-up action resolution closure completion dispatcher.
Reads the frozen v75.2 completion queue and emits canonical completion dispatch artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input: v75.2 completion queue artifact
COMPLETION_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_queue.json")
# Outputs: v75.3 completion dispatch artifacts
COMPLETION_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_dispatch.json")
COMPLETION_DISPATCH_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_dispatch.md")

COMPLETION_PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
COMPLETION_STATE_ORDER = {"completed-success": 0, "pending-complete": 1}

REQUIRED_FIELDS = [
    "completion_dispatch_id",
    "completion_queue_item_id",
    "dedupe_key",
    "dispatch_state",
    "dispatch_target",
    "dispatch_channel",
    "completion_priority",
    "next_completion_action",
    "suppression_reason",
]

def load_completion_queue() -> List[Dict[str, Any]]:
    if not COMPLETION_QUEUE_JSON.exists():
        return []
    with open(COMPLETION_QUEUE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []

def build_completion_dispatch_records(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    seen = set()
    for item in queue:
        # Compose unique key for dispatch
        key = (item["completion_queue_item_id"], item.get("dispatch_target"), item.get("dispatch_channel", "operator_manual"))
        if key in seen:
            continue
        seen.add(key)
        # Decide dispatch intent (for now, always 'dispatch' if eligible)
        dispatch_state = "dispatch"
        suppression_reason = ""
        # Deterministic completion_dispatch_id: SHA256 of completion_queue_item_id + dispatch_target + dispatch_channel
        id_basis = f"{item['completion_queue_item_id']}|{item.get('dispatch_target')}|{item.get('dispatch_channel', 'operator_manual')}"
        completion_dispatch_id = hashlib.sha256(id_basis.encode("utf-8")).hexdigest()
        record = {
            "completion_dispatch_id": completion_dispatch_id,
            "completion_queue_item_id": item["completion_queue_item_id"],
            "dedupe_key": item["dedupe_key"],
            "dispatch_state": dispatch_state,
            "dispatch_target": item.get("dispatch_target"),
            "dispatch_channel": item.get("dispatch_channel", "operator_manual"),
            "completion_priority": item.get("completion_priority"),
            "next_completion_action": item.get("next_completion_action"),
            "suppression_reason": suppression_reason,
        }
        records.append(record)
    # Deterministic ordering
    records.sort(key=lambda x: (
        COMPLETION_PRIORITY_ORDER.get(x["completion_priority"], 99),
        x["completion_queue_item_id"],
        x["dispatch_target"] or ""
    ))
    return records

def write_json(records: List[Dict[str, Any]]):
    with open(COMPLETION_DISPATCH_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md(records: List[Dict[str, Any]]):
    with open(COMPLETION_DISPATCH_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Completion Dispatch\n\n")
        if not records:
            f.write("_No completion dispatch records found._\n")
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
    queue = load_completion_queue()
    records = build_completion_dispatch_records(queue)
    write_json(records)
    write_md(records)
    print(f"Wrote {len(records)} completion dispatch records.")
    print(f"SHA256 (JSON): {sha256_file(COMPLETION_DISPATCH_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(COMPLETION_DISPATCH_MD)}")

if __name__ == "__main__":
    main()
