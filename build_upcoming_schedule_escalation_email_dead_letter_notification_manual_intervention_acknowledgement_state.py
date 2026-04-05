"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state.py

v72.2: Deterministic acknowledgement-state tracking for manual-intervention queue for escalation email dead-letter notification email path
- Reads manual intervention queue, assignment, and state
- Emits acknowledgement-state artifact (JSON), Markdown report, and state for rerun dedupe
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

QUEUE_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.json")
QUEUE_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue_state.json")
ASSIGN_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment.json")
ASSIGN_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_state.json")
ACK_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state.json")
ACK_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state.md")
ACK_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state_state.json")

# Helper functions
def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def make_ack_id(intervention_id):
    return hashlib.sha256(intervention_id.encode("utf-8")).hexdigest()[:16]

def main():
    queue = load_json(QUEUE_JSON_PATH, [])
    assignments = load_json(ASSIGN_JSON_PATH, [])
    now = datetime.utcnow().isoformat() + "Z"
    ack_rows = []
    ack_state = {}
    assignment_by_intervention = {a["intervention_id"]: a for a in assignments}
    for item in queue:
        intervention_id = item["intervention_id"]
        ack_id = make_ack_id(intervention_id)
        assignment = assignment_by_intervention.get(intervention_id)
        owner = assignment["owner"] if assignment else None
        if item["intervention_status"] == "cleared":
            ack_status = "cleared"
            ack_owner = None
            ack_at = None
            ack_reason = "Cleared intervention"
        else:
            ack_status = "unacknowledged"
            ack_owner = owner
            ack_at = None
            ack_reason = "Unacknowledged (projection only)"
        row = {
            "ack_id": ack_id,
            "intervention_id": intervention_id,
            "ack_status": ack_status,
            "ack_owner": ack_owner,
            "ack_at": ack_at,
            "ack_reason": ack_reason,
        }
        ack_rows.append(row)
        ack_state[ack_id] = row
    # Save artifacts
    save_json(ACK_JSON_PATH, ack_rows)
    save_json(ACK_STATE_PATH, ack_state)
    with open(ACK_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention Acknowledgement State\n\n")
        for row in ack_rows:
            f.write(f"- Ack: {row['ack_id']} | Intervention: {row['intervention_id']} | Status: {row['ack_status']} | Owner: {row['ack_owner']} | AckAt: {row['ack_at']} | Reason: {row['ack_reason']}\n")

if __name__ == "__main__":
    main()
