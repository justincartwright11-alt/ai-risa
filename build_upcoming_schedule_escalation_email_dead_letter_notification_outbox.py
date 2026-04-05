"""
build_upcoming_schedule_escalation_email_dead_letter_notification_outbox.py

v69.8: Deterministic notification outbox for escalation email dead-letter lifecycle
- Reads dead-letter ledger and state
- Emits notification intents for dead-letter opened/cleared transitions
- Deduplicates repeated terminal state
- Emits machine-readable outbox, Markdown report, and state for rerun dedupe
"""
import json
from pathlib import Path
from datetime import datetime

DEAD_LETTER_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_ledger.json")
DEAD_LETTER_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_ledger_state.json")
OUTBOX_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_outbox.json")
OUTBOX_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_outbox.md")
OUTBOX_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_outbox_state.json")


def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def main():
    dead_letter = load_json(DEAD_LETTER_JSON_PATH, [])
    dead_letter_state = load_json(DEAD_LETTER_STATE_PATH, {"dead_letters": {}})
    prev_outbox_state = load_json(OUTBOX_STATE_PATH, {"notifications": {}})
    prev_notifications = prev_outbox_state.get("notifications", {})
    now = datetime.utcnow().isoformat() + "Z"
    # Index by dead_letter_id
    dead_letter_by_id = {d["dead_letter_id"]: d for d in dead_letter}
    prev_dead_letters = dead_letter_state.get("dead_letters", {})
    outbox = []
    notifications = dict(prev_notifications)
    # Detect opened transitions
    for dead_letter_id, entry in dead_letter_by_id.items():
        dedupe_key = f"{dead_letter_id}:opened"
        if dedupe_key not in notifications:
            notification = {
                "notification_id": dedupe_key,
                "dead_letter_id": dead_letter_id,
                "delivery_id": entry["delivery_id"],
                "notification_type": "opened",
                "notification_status": "pending",
                "created_at": now,
                "terminal_reason": entry["terminal_reason"],
                "escalation_level": entry.get("escalation_level"),
                "dedupe_key": dedupe_key
            }
            notifications[dedupe_key] = notification
    # Detect cleared transitions (if a dead-letter previously existed but is now gone)
    for dead_letter_id in prev_dead_letters:
        if dead_letter_id not in dead_letter_by_id:
            dedupe_key = f"{dead_letter_id}:cleared"
            if dedupe_key not in notifications:
                prev_entry = prev_dead_letters[dead_letter_id]
                notification = {
                    "notification_id": dedupe_key,
                    "dead_letter_id": dead_letter_id,
                    "delivery_id": prev_entry["delivery_id"],
                    "notification_type": "cleared",
                    "notification_status": "pending",
                    "created_at": now,
                    "terminal_reason": prev_entry["terminal_reason"],
                    "escalation_level": prev_entry.get("escalation_level"),
                    "dedupe_key": dedupe_key
                }
                notifications[dedupe_key] = notification
    # Output
    outbox = list(notifications.values())
    save_json(OUTBOX_JSON_PATH, outbox)
    save_json(OUTBOX_STATE_PATH, {"notifications": notifications, "generated_at": now})
    # Markdown report
    with open(OUTBOX_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Escalation Email Dead-Letter Notification Outbox\n\n")
        for n in outbox:
            f.write(f"- Notification: {n['notification_id']} | DeadLetter: {n['dead_letter_id']} | Delivery: {n['delivery_id']} | Type: {n['notification_type']} | Status: {n['notification_status']} | Reason: {n['terminal_reason']} | Level: {n['escalation_level']} | Created: {n['created_at']}\n")

if __name__ == "__main__":
    main()
