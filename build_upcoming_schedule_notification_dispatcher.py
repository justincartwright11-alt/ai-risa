"""
build_upcoming_schedule_notification_dispatcher.py

Deterministic dispatcher for upcoming schedule notification outbox.

Consumes pending notification intents, attempts delivery, records delivery state, and emits delivery artifacts.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

OUTBOX_PATH = Path("ops/events/upcoming_schedule_notification_outbox.json")
OUTBOX_STATE_PATH = Path("ops/events/upcoming_schedule_notification_outbox_state.json")
DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_notification_delivery.json")
DELIVERY_MD_PATH = Path("ops/events/upcoming_schedule_notification_delivery.md")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_notification_delivery_state.json")

TRANSPORT = "local-log"

# Simulate deterministic delivery: always succeed for 'opened', fail for 'failed', skip for 'cleared'
def deliver(notification):
    # For demo: fail if reason is 'failme', skip if type is 'cleared', else sent
    if notification["notification_type"] == "cleared":
        return "skipped", None
    if notification.get("reason") == "failme":
        return "failed", "Simulated delivery failure"
    return "sent", None

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

def emit_delivery_artifacts(deliveries):
    with open(DELIVERY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(deliveries, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(DELIVERY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Notification Delivery\n\n")
        for d in deliveries["deliveries"]:
            f.write(f"- Delivery ID: {d['delivery_id']}\n")
            f.write(f"  Notification ID: {d['notification_id']}\n")
            f.write(f"  Status: {d['delivery_status']}\n")
            f.write(f"  Transport: {d['transport']}\n")
            f.write(f"  Attempt count: {d['attempt_count']}\n")
            f.write(f"  First attempt: {d['first_attempt_at']}\n")
            f.write(f"  Last attempt: {d['last_attempt_at']}\n")
            f.write(f"  Delivered at: {d['delivered_at']}\n")
            f.write(f"  Failure reason: {d['failure_reason']}\n\n")

def main():
    now = datetime.utcnow().isoformat() + "Z"
    outbox = load_json(OUTBOX_PATH, {"notifications": []})
    prev_delivery = load_json(DELIVERY_STATE_PATH, {"deliveries": []})
    deliveries = prev_delivery["deliveries"][:]
    delivered_ids = {d["notification_id"]: d for d in deliveries if d["delivery_status"] == "sent"}
    # Only process pending, not-yet-delivered
    for n in outbox["notifications"]:
        nid = n["notification_id"]
        # Already sent? Skip
        if nid in delivered_ids:
            continue
        # Find previous delivery record
        prev = next((d for d in deliveries if d["notification_id"] == nid), None)
        attempt_count = prev["attempt_count"] + 1 if prev else 1
        first_attempt_at = prev["first_attempt_at"] if prev else now
        # Attempt delivery
        status, reason = deliver(n)
        delivered_at = now if status == "sent" else None
        delivery_id = stable_id(nid, TRANSPORT, first_attempt_at)
        record = {
            "notification_id": nid,
            "delivery_id": delivery_id,
            "delivery_status": status,
            "transport": TRANSPORT,
            "attempt_count": attempt_count,
            "first_attempt_at": first_attempt_at,
            "last_attempt_at": now,
            "delivered_at": delivered_at,
            "failure_reason": reason
        }
        # Update or append
        if prev:
            deliveries = [d if d["notification_id"] != nid else record for d in deliveries]
        else:
            deliveries.append(record)
    result = {"deliveries": deliveries}
    save_json(DELIVERY_STATE_PATH, result)
    emit_delivery_artifacts(result)

if __name__ == "__main__":
    main()
