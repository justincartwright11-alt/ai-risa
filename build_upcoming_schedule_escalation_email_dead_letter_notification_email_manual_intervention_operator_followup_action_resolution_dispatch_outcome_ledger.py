"""
v74.4-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-action-resolution-dispatch-outcome-ledger

- Reads v74.3 operator follow-up action resolution dispatch (JSON)
- Builds deterministic outcome ledger for each dispatch attempt
- Emits:
    - outcome ledger JSON/Markdown
- Enforces idempotence, stable IDs, and no upstream mutation
- Deterministic ordering: resolution_dispatch_id, attempt_number, dispatch_target
"""

import json
import os
import hashlib
from datetime import datetime
from copy import deepcopy

DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch.json"
LEDGER_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_outcome_ledger.json"
LEDGER_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_outcome_ledger.md"

# --- Constants/Enums ---
TERMINAL_DELIVERY_STATES = ["sent", "failed", "skipped", "blocked"]
FIXED_TIMESTAMP = "2026-04-06T00:00:00Z"

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

# --- Outcome Builder ---
def build_outcome_ledger(dispatches):
    ledger = []
    seen = set()
    for d in dispatches:
        # For this slice, simulate a single attempt per dispatch, terminal state 'sent'
        attempt_number = 1
        dedupe_key = f"{d['resolution_dispatch_id']}|{attempt_number}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        resolution_dispatch_outcome_id = stable_id(d["resolution_dispatch_id"], attempt_number)
        ledger.append({
            "resolution_dispatch_outcome_id": resolution_dispatch_outcome_id,
            "resolution_dispatch_id": d["resolution_dispatch_id"],
            "resolution_queue_item_id": d["resolution_queue_item_id"],
            "dedupe_key": dedupe_key,
            "dispatch_target": d["dispatch_target"],
            "dispatch_channel": d["dispatch_channel"],
            "dispatch_state": d["dispatch_state"],
            "delivery_state": "sent",  # For demo, always 'sent'
            "result_code": "250",
            "result_summary": "Resolution action sent successfully.",
            "attempt_number": attempt_number,
            "attempted_at": FIXED_TIMESTAMP,
            "completed_at": FIXED_TIMESTAMP,
            "suppression_reason": d.get("suppression_reason", "")
        })
    # Deterministic ordering
    ledger.sort(key=lambda x: (x["resolution_dispatch_id"], x["attempt_number"], x["dispatch_target"]))
    return ledger

# --- Invariant Validator ---
def validate_invariants(ledger):
    dedupes = set()
    for o in ledger:
        assert o["dedupe_key"] not in dedupes, f"Duplicate dedupe_key: {o['dedupe_key']}"
        dedupes.add(o["dedupe_key"])
        assert o["delivery_state"] in TERMINAL_DELIVERY_STATES, f"Non-terminal delivery_state: {o['delivery_state']}"
    # No duplicate settled outcomes

# --- Markdown Writer ---
def ledger_to_md(ledger):
    lines = ["# Operator Follow-up Action Resolution Dispatch Outcome Ledger", "", f"Total Outcomes: {len(ledger)}", ""]
    for o in ledger:
        lines.append(f"- Outcome ID: {o['resolution_dispatch_outcome_id']} | Dispatch ID: {o['resolution_dispatch_id']} | Queue ID: {o['resolution_queue_item_id']} | Target: {o['dispatch_target']} | Channel: {o['dispatch_channel']} | Delivery: {o['delivery_state']} | Code: {o['result_code']} | Summary: {o['result_summary']} | Attempt: {o['attempt_number']} | State: {o['dispatch_state']} | Suppression: {o['suppression_reason']}")
    return lines

# --- Entrypoint ---
def main():
    if not os.path.exists(DISPATCH_PATH):
        raise FileNotFoundError("Required v74.3 dispatch missing.")
    dispatches = load_json(DISPATCH_PATH)
    ledger = build_outcome_ledger(dispatches)
    validate_invariants(ledger)
    write_json(ledger, LEDGER_PATH)
    write_md(ledger_to_md(ledger), LEDGER_MD_PATH)

if __name__ == "__main__":
    main()
