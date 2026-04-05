#!/usr/bin/env python3
"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.py

Deterministically computes and emits the resolution-state for manual-intervention items in the upcoming schedule escalation email dead-letter notification pipeline.

Reads:
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.json
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue_state.json
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment.json
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_state.json
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state.json

Emits:
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.json
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.md

Constraints:
- v66.3 through v72.3 interfaces are frozen
- No schema redesign, new transport/channel, or daemon/service changes
- Resolution-state only
"""
import json
import os
from datetime import datetime
from collections import OrderedDict

# File paths
QUEUE_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.json"
QUEUE_STATE_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue_state.json"
ASSIGNMENT_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment.json"
ASSIGNMENT_STATE_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_state.json"
ACK_STATE_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state.json"
RESOLUTION_STATE_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.json"
RESOLUTION_STATE_MD = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.md"

# Helper: load JSON

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load all required state
queue = load_json(QUEUE_JSON)
queue_state = load_json(QUEUE_STATE_JSON)
assignment = load_json(ASSIGNMENT_JSON)
assignment_state = load_json(ASSIGNMENT_STATE_JSON)
ack_state = load_json(ACK_STATE_JSON)

# Build lookup tables for deterministic linkage
assignment_by_id = {a["intervention_id"]: a for a in assignment}
assignment_state_by_id = {a["intervention_id"]: a for a in assignment_state}
ack_by_id = {a["intervention_id"]: a for a in ack_state}

# Compute deterministic resolution state
resolution_rows = []
now_iso = datetime.utcnow().isoformat() + "Z"
for item in queue:
    intervention_id = item["intervention_id"]
    # Link assignment, assignment_state, ack_state
    assign = assignment_by_id.get(intervention_id, {})
    assign_state = assignment_state_by_id.get(intervention_id, {})
    ack = ack_by_id.get(intervention_id, {})

    # Default: unresolved
    resolution_status = "unresolved"
    resolution_owner = assign.get("assignee") or assign_state.get("assignee")
    resolved_at = None
    resolution_reason = None

    # If item is cleared (not present in queue_state), mark as cleared
    if not any(q["intervention_id"] == intervention_id for q in queue_state):
        resolution_status = "cleared"
        resolution_owner = None
        resolved_at = now_iso
        resolution_reason = "intervention_cleared"
    # If item is acknowledged and resolved (future: human input), mark as resolved
    elif ack.get("acknowledgement_status") == "acknowledged" and ack.get("resolution_status") == "resolved":
        resolution_status = "resolved"
        resolution_owner = ack.get("resolution_owner") or resolution_owner
        resolved_at = ack.get("resolved_at") or now_iso
        resolution_reason = ack.get("resolution_reason") or "manual_resolution"
    # If item is acknowledged but not resolved
    elif ack.get("acknowledgement_status") == "acknowledged":
        resolution_status = "unresolved"
        resolution_owner = resolution_owner
        resolved_at = None
        resolution_reason = None
    # If item is new/unacknowledged
    else:
        resolution_status = "unresolved"
        resolution_owner = resolution_owner
        resolved_at = None
        resolution_reason = None

    row = OrderedDict([
        ("intervention_id", intervention_id),
        ("resolution_status", resolution_status),
        ("resolution_owner", resolution_owner),
        ("resolved_at", resolved_at),
        ("resolution_reason", resolution_reason),
        ("assignment_id", assign.get("assignment_id")),
        ("acknowledgement_id", ack.get("acknowledgement_id")),
    ])
    resolution_rows.append(row)

# Deduplicate by intervention_id (deterministic order)
seen = set()
deduped_rows = []
for row in resolution_rows:
    if row["intervention_id"] not in seen:
        deduped_rows.append(row)
        seen.add(row["intervention_id"])

# Emit machine-readable JSON
with open(RESOLUTION_STATE_JSON, "w", encoding="utf-8") as f:
    json.dump(deduped_rows, f, indent=2, ensure_ascii=False)

# Emit Markdown report
def row_md(row):
    return (
        f"- **Intervention ID:** {row['intervention_id']}\n"
        f"  - Status: `{row['resolution_status']}`\n"
        f"  - Owner: `{row['resolution_owner']}`\n"
        f"  - Resolved At: `{row['resolved_at']}`\n"
        f"  - Reason: `{row['resolution_reason']}`\n"
        f"  - Assignment ID: `{row['assignment_id']}`\n"
        f"  - Acknowledgement ID: `{row['acknowledgement_id']}`\n"
    )

with open(RESOLUTION_STATE_MD, "w", encoding="utf-8") as f:
    f.write("# Manual-Intervention Resolution State\n\n")
    if not deduped_rows:
        f.write("_No manual-intervention items present._\n")
    else:
        for row in deduped_rows:
            f.write(row_md(row) + "\n")
