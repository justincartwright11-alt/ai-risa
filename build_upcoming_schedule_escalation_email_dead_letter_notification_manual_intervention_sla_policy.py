"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla_policy.py

v72.0: Deterministic SLA/aging policy for manual-intervention queue for escalation email dead-letter notification email path
- Reads manual intervention queue, assignment, and state
- Emits SLA artifact (JSON), Markdown report, and SLA state for rerun dedupe
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

QUEUE_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.json")
QUEUE_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue_state.json")
ASSIGN_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment.json")
ASSIGN_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_state.json")
SLA_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla.json")
SLA_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla.md")
SLA_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla_state.json")

# Example deterministic SLA windows (in hours)
SLA_WINDOWS = {
    "P1": 4,   # 4 hours for P1
    "P2": 12,  # 12 hours for P2
    "P3": 24,  # 24 hours for P3
}
DUE_SOON_THRESHOLD = 0.8  # 80% of window

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

def parse_iso8601(dt):
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None

def main():
    queue = load_json(QUEUE_JSON_PATH, [])
    assignments = load_json(ASSIGN_JSON_PATH, [])
    now = datetime.utcnow()
    sla_rows = []
    sla_state = {}
    assignment_by_intervention = {a["intervention_id"]: a for a in assignments}
    for item in queue:
        if item["intervention_status"] not in ("open", "active"):
            continue
        intervention_id = item["intervention_id"]
        assignment = assignment_by_intervention.get(intervention_id)
        priority = assignment["priority"] if assignment else "P3"
        window_hours = SLA_WINDOWS.get(priority, 24)
        opened_at = parse_iso8601(item["opened_at"])
        if not opened_at:
            continue
        due_at = opened_at + timedelta(hours=window_hours)
        overdue_at = due_at
        age = (now - opened_at).total_seconds() / 3600.0
        window = window_hours
        sla_status = "within_window"
        if age >= window:
            sla_status = "overdue"
        elif age >= window * DUE_SOON_THRESHOLD:
            sla_status = "due_soon"
        sla_reason = f"Priority {priority} window: {window_hours}h"
        row = {
            "sla_id": hashlib.sha256((intervention_id + priority).encode("utf-8")).hexdigest()[:16],
            "intervention_id": intervention_id,
            "priority_band": priority,
            "sla_status": sla_status,
            "due_at": due_at.isoformat() + "Z",
            "overdue_at": overdue_at.isoformat() + "Z",
            "sla_reason": sla_reason,
        }
        sla_rows.append(row)
        sla_state[row["sla_id"]] = row
    # Save artifacts
    save_json(SLA_JSON_PATH, sla_rows)
    save_json(SLA_STATE_PATH, sla_state)
    with open(SLA_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention SLA Policy\n\n")
        for row in sla_rows:
            f.write(f"- SLA: {row['sla_id']} | Intervention: {row['intervention_id']} | Priority: {row['priority_band']} | Status: {row['sla_status']} | Due: {row['due_at']} | Overdue: {row['overdue_at']} | Reason: {row['sla_reason']}\n")

if __name__ == "__main__":
    main()
