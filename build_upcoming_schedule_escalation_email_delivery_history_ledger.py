"""
build_upcoming_schedule_escalation_email_delivery_history_ledger.py

v68.8: Deterministic escalation email delivery history ledger
- Reads delivery artifact after dispatcher completion
- Appends/updates one row per delivery attempt (exact-once)
- Captures notification_id, escalation_id, delivery_id, delivery_status, recipients, escalation_level, notification_type, attempt count, timestamps, terminal reason
- Emits machine-readable JSON and Markdown history artifacts
"""
import json
from pathlib import Path
from datetime import datetime

DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery.json")
HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_delivery_history_ledger.json")
HISTORY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_delivery_history_ledger.md")


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
    delivery = load_json(DELIVERY_JSON_PATH, [])
    history = load_json(HISTORY_JSON_PATH, [])
    # Index by delivery_id for exact-once update
    history_by_id = {h["delivery_id"]: h for h in history}
    for d in delivery:
        delivery_id = d["delivery_id"]
        attempt_count = history_by_id.get(delivery_id, {}).get("attempt_count", 0) + 1
        entry = {
            "notification_id": d["notification_id"],
            "escalation_id": d["outbox_entry"].get("escalation_id"),
            "delivery_id": delivery_id,
            "delivery_status": d["result"],
            "recipients": d.get("routing", {}).get("recipients", []),
            "escalation_level": d["outbox_entry"].get("escalation_level"),
            "notification_type": d["outbox_entry"].get("notification_type"),
            "attempt_count": attempt_count,
            "timestamp": d["dispatched_at"],
            "reason": d.get("reason", "")
        }
        history_by_id[delivery_id] = entry
    # Deterministic ordering by timestamp, then delivery_id
    history_out = sorted(history_by_id.values(), key=lambda x: (x["timestamp"], x["delivery_id"]))
    save_json(HISTORY_JSON_PATH, history_out)
    # Markdown report
    with open(HISTORY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Email Delivery History Ledger\n\n")
        for h in history_out:
            f.write(f"- Delivery: {h['delivery_id']} | Notification: {h['notification_id']} | Escalation: {h['escalation_id']} | Status: {h['delivery_status']} | Recipients: {', '.join(h['recipients'])} | Level: {h['escalation_level']} | Type: {h['notification_type']} | Attempts: {h['attempt_count']} | Time: {h['timestamp']} | Reason: {h['reason']}\n")

if __name__ == "__main__":
    main()
