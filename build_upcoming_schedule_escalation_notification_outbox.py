"""
build_upcoming_schedule_escalation_notification_outbox.py

Deterministic notification outbox for escalation lifecycle transitions (v68.2).
Reads escalation state, emits notification intents only on real transitions.
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

ESCALATION_JSON = Path("ops/events/upcoming_schedule_escalation.json")
ESCALATION_STATE_JSON = Path("ops/events/upcoming_schedule_escalation_state.json")
OUTBOX_JSON = Path("ops/events/upcoming_schedule_escalation_notification_outbox.json")
OUTBOX_MD = Path("ops/events/upcoming_schedule_escalation_notification_outbox.md")
OUTBOX_STATE_JSON = Path("ops/events/upcoming_schedule_escalation_notification_outbox_state.json")

# State model for notification outbox entries
def stable_id(*args):
    s = ":".join(str(a) for a in args)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def detect_transition(prev, curr):
    # Returns (transition_type, escalation_id, escalation_level, reason) or None
    if not prev or not prev.get("escalation_active"):
        if curr.get("escalation_active"):
            return ("opened", curr["escalation_id"], curr["escalation_level"], curr["escalation_reason"])
    if prev and prev.get("escalation_active"):
        if not curr.get("escalation_active"):
            return ("cleared", prev["escalation_id"], prev["escalation_level"], prev["escalation_reason"])
    return None

def main():
    curr = load_json(ESCALATION_STATE_JSON, {})
    prev = load_json(OUTBOX_STATE_JSON, {})
    outbox = load_json(OUTBOX_JSON, {"notifications": []})
    notifications = outbox["notifications"]
    transition = detect_transition(prev, curr)
    now = datetime.utcnow().isoformat() + "Z"
    if transition:
        notification_type, escalation_id, escalation_level, reason = transition
        dedupe_key = f"{escalation_id}:{notification_type}"
        notification_id = stable_id(escalation_id, notification_type)
        # Dedupe: only add if not present
        if not any(n["dedupe_key"] == dedupe_key for n in notifications):
            notifications.append({
                "notification_id": notification_id,
                "escalation_id": escalation_id,
                "notification_type": notification_type,
                "notification_status": "pending",
                "created_at": now,
                "reason": reason,
                "dedupe_key": dedupe_key,
                "escalation_level": escalation_level
            })
    # Save outbox and state
    save_json(OUTBOX_JSON, {"notifications": notifications})
    save_json(OUTBOX_STATE_JSON, curr)
    # Emit Markdown
    with open(OUTBOX_MD, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Notification Outbox\n\n")
        if notifications:
            for n in notifications:
                f.write(f"- ID: {n['notification_id']} | Escalation: {n['escalation_id']} | Type: {n['notification_type']} | Status: {n['notification_status']} | Level: {n['escalation_level']} | Created: {n['created_at']} | Reason: {n['reason']}\n")
        else:
            f.write("No escalation notifications pending.\n")

if __name__ == "__main__":
    main()
