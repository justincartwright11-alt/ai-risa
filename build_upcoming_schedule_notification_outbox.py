"""
build_upcoming_schedule_notification_outbox.py

Deterministic notification outbox generator for upcoming schedule alert state.

Reads alert state, emits notification intents only on incident transitions, dedupes, emits outbox artifacts.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

ALERT_PATH = Path("ops/events/upcoming_schedule_alert.json")
ALERT_STATE_PATH = Path("ops/events/upcoming_schedule_alert_state.json")
OUTBOX_JSON_PATH = Path("ops/events/upcoming_schedule_notification_outbox.json")
OUTBOX_MD_PATH = Path("ops/events/upcoming_schedule_notification_outbox.md")
OUTBOX_STATE_PATH = Path("ops/events/upcoming_schedule_notification_outbox_state.json")

def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def stable_id(*args):
    s = ":".join(str(a) for a in args)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def emit_outbox_artifacts(outbox):
    with open(OUTBOX_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(outbox, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(OUTBOX_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Notification Outbox\n\n")
        for n in outbox["notifications"]:
            f.write(f"- Notification ID: {n['notification_id']}\n")
            f.write(f"  Incident ID: {n['incident_id']}\n")
            f.write(f"  Type: {n['notification_type']}\n")
            f.write(f"  Status: {n['notification_status']}\n")
            f.write(f"  Created at: {n['created_at']}\n")
            f.write(f"  Reason: {n['reason']}\n")
            f.write(f"  Dedupe key: {n['dedupe_key']}\n\n")

def main():
    now = datetime.utcnow().isoformat() + "Z"
    alert = load_json(ALERT_PATH, {})
    prev_outbox = load_json(OUTBOX_STATE_PATH, {"notifications": []})
    notifications = prev_outbox["notifications"][:]
    # Only emit on transitions: opened, cleared
    incident_id = alert.get("incident_id")
    incident_status = alert.get("incident_status")
    reason = alert.get("alert_reason")
    opened_at = alert.get("opened_at")
    cleared_at = alert.get("cleared_at")
    # Dedupe key: incident_id + notification_type
    new_notifications = []
    # Open notification
    if incident_status == "opened":
        dedupe_key = f"{incident_id}:opened"
        if not any(n["dedupe_key"] == dedupe_key for n in notifications):
            notification_id = stable_id(incident_id, "opened", opened_at)
            new_notifications.append({
                "notification_id": notification_id,
                "incident_id": incident_id,
                "notification_type": "opened",
                "notification_status": "pending",
                "created_at": now,
                "reason": reason,
                "dedupe_key": dedupe_key
            })
    # Clear notification
    if incident_status == "cleared":
        dedupe_key = f"{incident_id}:cleared"
        if not any(n["dedupe_key"] == dedupe_key for n in notifications):
            notification_id = stable_id(incident_id, "cleared", cleared_at)
            new_notifications.append({
                "notification_id": notification_id,
                "incident_id": incident_id,
                "notification_type": "cleared",
                "notification_status": "pending",
                "created_at": now,
                "reason": reason,
                "dedupe_key": dedupe_key
            })
    # Add new notifications to outbox
    notifications.extend(new_notifications)
    outbox = {"notifications": notifications}
    save_json(OUTBOX_STATE_PATH, outbox)
    emit_outbox_artifacts(outbox)

if __name__ == "__main__":
    main()
