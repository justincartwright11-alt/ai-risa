"""
v74.3-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-action-resolution-dispatcher

- Reads v74.2 operator follow-up action resolution queue (JSON)
- Produces deterministic dispatch-intent records for each actionable resolution item
- Emits:
    - resolution dispatch JSON/Markdown
- Enforces idempotence, stable IDs, and no upstream mutation
- Deterministic ordering: high > normal > low, blocked > failed > unresolved, resolution_queue_item_id, dispatch_target
"""

import json
import os
import hashlib
from copy import deepcopy

QUEUE_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_queue.json"
DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch.json"
DISPATCH_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch.md"

# --- Constants/Enums ---
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
RESOLUTION_STATES = ["blocked", "failed", "unresolved"]
DISPATCH_CHANNEL = "operator_manual"

# --- Helpers ---
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_md(lines, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def stable_id(*fields):
    s = "|".join(str(f) for f in fields)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

# --- Dispatch Eligibility Filter ---
def build_dispatch_records(queue):
    records = []
    seen = set()
    for q in queue:
        # Only actionable items (not suppressed, not already resolved)
        # For this slice, all queue items are actionable unless a suppression reason is set
        suppression_reason = ""
        dispatch_state = "dispatch"
        dedupe_key = f"{q['resolution_queue_item_id']}|{q['dispatch_target']}|{DISPATCH_CHANNEL}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        resolution_dispatch_id = stable_id(q['resolution_queue_item_id'], q['dispatch_target'], DISPATCH_CHANNEL)
        records.append({
            "resolution_dispatch_id": resolution_dispatch_id,
            "resolution_queue_item_id": q["resolution_queue_item_id"],
            "dedupe_key": dedupe_key,
            "dispatch_state": dispatch_state,
            "dispatch_target": q["dispatch_target"],
            "dispatch_channel": DISPATCH_CHANNEL,
            "resolution_priority": q["resolution_priority"],
            "next_resolution_action": q["next_resolution_action"],
            "suppression_reason": suppression_reason
        })
    # Deterministic ordering
    records.sort(key=lambda x: (
        PRIORITY_ORDER.get(x["resolution_priority"], 99),
        RESOLUTION_STATES.index(queue[[q["resolution_queue_item_id"] for q in queue].index(x["resolution_queue_item_id"])] ["resolution_state"]),
        x["resolution_queue_item_id"],
        x["dispatch_target"]
    ))
    return records

# --- Invariant Validator ---
def validate_invariants(records):
    dedupes = set()
    for r in records:
        assert r["dedupe_key"] not in dedupes, f"Duplicate dedupe_key: {r['dedupe_key']}"
        dedupes.add(r["dedupe_key"])
        assert r["dispatch_state"] == "dispatch", f"Invalid dispatch_state: {r['dispatch_state']}"
    # No upstream mutation, no suppressed or resolved items

# --- Markdown Writer ---
def dispatch_to_md(records):
    lines = ["# Operator Follow-up Action Resolution Dispatch", "", f"Total Dispatches: {len(records)}", ""]
    for r in records:
        lines.append(f"- Dispatch ID: {r['resolution_dispatch_id']} | Queue ID: {r['resolution_queue_item_id']} | Target: {r['dispatch_target']} | Channel: {r['dispatch_channel']} | Priority: {r['resolution_priority']} | State: {r['dispatch_state']} | Next: {r['next_resolution_action']} | Suppression: {r['suppression_reason']}")
    return lines

# --- Entrypoint ---
def main():
    if not os.path.exists(QUEUE_PATH):
        raise FileNotFoundError("Required v74.2 queue missing.")
    queue = load_json(QUEUE_PATH)
    records = build_dispatch_records(queue)
    validate_invariants(records)
    write_json(records, DISPATCH_PATH)
    write_md(dispatch_to_md(records), DISPATCH_MD_PATH)

if __name__ == "__main__":
    main()
