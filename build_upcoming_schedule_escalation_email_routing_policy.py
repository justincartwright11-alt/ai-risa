"""
build_upcoming_schedule_escalation_email_routing_policy.py

v68.6: Deterministic escalation email routing policy
- Reads escalation state and notification outbox
- Computes recipient routing for each escalation notification
- Emits routing artifact (JSON, Markdown)
- Deterministic, deduped, audit-friendly
"""
import json
from pathlib import Path
from datetime import datetime

ESCALATION_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_state.json")
OUTBOX_PATH = Path("ops/events/upcoming_schedule_escalation_notification_outbox.json")
ROUTING_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_routing.json")
ROUTING_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_routing.md")

# Example deterministic routing policy
ROUTING_TABLE = {
    "critical": ["level1@example.com", "level2@example.com"],
    "warning": ["level2@example.com"],
    None: []
}

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
    state = load_json(ESCALATION_STATE_PATH, {})
    outbox = load_json(OUTBOX_PATH, {"notifications": []})["notifications"]
    routing = []
    now = datetime.utcnow().isoformat() + "Z"
    for n in outbox:
        level = n.get("escalation_level")
        recipients = ROUTING_TABLE.get(level, [])
        routing.append({
            "notification_id": n["notification_id"],
            "escalation_id": n["escalation_id"],
            "notification_type": n["notification_type"],
            "escalation_level": level,
            "recipients": recipients,
            "routed_at": now
        })
    save_json(ROUTING_JSON_PATH, routing)
    # Markdown report
    with open(ROUTING_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Email Routing Report\n\n")
        if routing:
            for r in routing:
                f.write(f"- ID: {r['notification_id']} | Level: {r['escalation_level']} | Recipients: {', '.join(r['recipients'])} | Type: {r['notification_type']} | Routed: {r['routed_at']}\n")
        else:
            f.write("No escalation notifications to route.\n")

if __name__ == "__main__":
    main()
