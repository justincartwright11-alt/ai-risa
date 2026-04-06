"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.py

v71.6: Deterministic manual-intervention queue for escalation email dead-letter notification email deliveries that are terminal after retry exhaustion
- Reads dead-letter ledger and state
- Emits manual-intervention queue (JSON), Markdown report, and queue state for rerun dedupe
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

DEAD_LETTER_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_exhaustion_dead_letter.json")
DEAD_LETTER_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_exhaustion_dead_letter_state.json")
QUEUE_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.json")
QUEUE_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.md")
QUEUE_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue_state.json")

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

def make_intervention_id(dead_letter_id):
    return hashlib.sha256(dead_letter_id.encode("utf-8")).hexdigest()[:16]

def main():
    dead_letter = load_json(DEAD_LETTER_JSON_PATH, [])
    dead_letter_state = load_json(DEAD_LETTER_STATE_PATH, {"dead_lettered": {}})
    queue_state = load_json(QUEUE_STATE_PATH, {"interventions": {}})
    interventions = dict(queue_state.get("interventions", {}))
    now = datetime.utcnow().isoformat() + "Z"

    # Build index of current terminal dead-lettered deliveries
    current_terminal = {d["dead_letter_id"]: d for d in dead_letter}
    # Track which interventions are still open
    open_interventions = set()
    queue = []

    # Open or update interventions for new terminal dead-lettered deliveries
    for dead_letter_id, d in current_terminal.items():
        intervention_id = make_intervention_id(dead_letter_id)
        prev = interventions.get(intervention_id)
        if prev and prev["intervention_status"] in ("open", "active"):
            # Already open, update last_seen_at and attempt_count
            item = prev.copy()
            item["last_seen_at"] = now
            item["attempt_count"] = d.get("attempt_count", 1)
            queue.append(item)
        else:
            # New intervention
            item = {
                "intervention_id": intervention_id,
                "dead_letter_id": dead_letter_id,
                "delivery_id": d["delivery_id"],
                "notification_id": d["notification_id"],
                "escalation_id": d.get("escalation_id"),
                "intervention_status": "open",
                "terminal_reason": d.get("terminal_reason"),
                "attempt_count": d.get("attempt_count", 1),
                "opened_at": now,
                "last_seen_at": now,
                "cleared_at": None,
                "dedupe_key": d.get("dedupe_key")
            }
            queue.append(item)
        open_interventions.add(intervention_id)

    # Clear interventions for recovered/resolved items
    for intervention_id, prev in interventions.items():
        if intervention_id not in open_interventions and prev["intervention_status"] in ("open", "active"):
            item = prev.copy()
            item["intervention_status"] = "cleared"
            item["cleared_at"] = now
            queue.append(item)

    # Save artifacts
    save_json(QUEUE_JSON_PATH, queue)
    save_json(QUEUE_STATE_PATH, {"interventions": {i["intervention_id"]: i for i in queue}})
    with open(QUEUE_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention Queue for Terminal Dead-Letter Notification Emails\n\n")
        for i in queue:
            f.write(f"- Intervention: {i['intervention_id']} | DeadLetter: {i['dead_letter_id']} | Delivery: {i['delivery_id']} | Notification: {i['notification_id']} | Status: {i['intervention_status']} | Reason: {i['terminal_reason']} | Attempts: {i['attempt_count']} | Opened: {i['opened_at']} | LastSeen: {i['last_seen_at']} | Cleared: {i['cleared_at']}\n")

if __name__ == "__main__":
    main()
