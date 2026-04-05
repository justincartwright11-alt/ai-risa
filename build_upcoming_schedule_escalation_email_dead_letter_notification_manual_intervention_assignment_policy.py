"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_policy.py

v71.8: Deterministic assignment policy for manual-intervention queue for escalation email dead-letter notification email path
- Reads manual intervention queue and state
- Emits assignment artifact (JSON), Markdown report, and assignment state for rerun dedupe
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

QUEUE_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.json")
QUEUE_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue_state.json")
ASSIGN_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment.json")
ASSIGN_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment.md")
ASSIGN_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_state.json")

# Example deterministic owner/team mapping
OWNER_MAP = {
    "A": "Ops-Team-A",
    "B": "Ops-Team-B",
    "C": "Ops-Team-C",
}
DEFAULT_OWNER = "Ops-Default"

# Example deterministic priority banding
def compute_priority(item):
    reason = item.get("terminal_reason", "")
    if "permanent" in reason:
        return "P1"
    if "invalid" in reason:
        return "P2"
    return "P3"

def compute_owner(item):
    # Use first char of dedupe_key for demo; real logic could hash or use escalation_id, etc.
    key = (item.get("dedupe_key") or "").upper()
    if key and key[0] in OWNER_MAP:
        return OWNER_MAP[key[0]]
    return DEFAULT_OWNER

def compute_assignment_id(intervention_id):
    return hashlib.sha256(intervention_id.encode("utf-8")).hexdigest()[:16]

def main():
    queue = []
    if QUEUE_JSON_PATH.exists():
        with open(QUEUE_JSON_PATH, "r", encoding="utf-8") as f:
            queue = json.load(f)
    queue_state = {}
    if QUEUE_STATE_PATH.exists():
        with open(QUEUE_STATE_PATH, "r", encoding="utf-8") as f:
            queue_state = json.load(f)
    interventions = {i["intervention_id"]: i for i in queue}
    assignments = {}
    now = datetime.utcnow().isoformat() + "Z"
    assignment_rows = []
    for i in queue:
        if i["intervention_status"] not in ("open", "active"):
            continue
        assignment_id = compute_assignment_id(i["intervention_id"])
        owner = compute_owner(i)
        priority = compute_priority(i)
        row = {
            "assignment_id": assignment_id,
            "intervention_id": i["intervention_id"],
            "owner": owner,
            "priority": priority,
            "assignment_reason": f"Policy: {i['terminal_reason']}",
            "assigned_at": now,
            "dedupe_key": i.get("dedupe_key"),
        }
        assignments[assignment_id] = row
        assignment_rows.append(row)
    # Save artifacts
    with open(ASSIGN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(assignment_rows, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(ASSIGN_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(ASSIGN_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention Assignment Policy\n\n")
        for row in assignment_rows:
            f.write(f"- Assignment: {row['assignment_id']} | Intervention: {row['intervention_id']} | Owner: {row['owner']} | Priority: {row['priority']} | Reason: {row['assignment_reason']} | Assigned: {row['assigned_at']}\n")

if __name__ == "__main__":
    main()
