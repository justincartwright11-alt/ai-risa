"""
build_upcoming_schedule_escalation_email_retry_history_ledger.py

v69.4: Deterministic escalation email retry-attempt history ledger
- Reads retry dispatch, delivery, and state artifacts
- Records one history entry per retry attempt
- Captures retry_attempt_id, delivery_id, notification_id, escalation_id, retry_status, attempt_number, recipients, escalation level, notification type, timestamps, and reason
- Emits machine-readable retry-history ledger and Markdown report
"""
import json
from pathlib import Path

RETRY_DISPATCH_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_dispatch.json")
RETRY_DISPATCH_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_dispatch_state.json")
DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery_state.json")
RETRY_HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_history_ledger.json")
RETRY_HISTORY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_history_ledger.md")


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
    retry_dispatch = load_json(RETRY_DISPATCH_JSON_PATH, [])
    retry_dispatch_state = load_json(RETRY_DISPATCH_STATE_PATH, {"attempts": {}})
    delivery = load_json(DELIVERY_JSON_PATH, [])
    delivery_by_id = {d["delivery_id"]: d for d in delivery}
    # Index by retry_attempt_id for exact-once update
    history = load_json(RETRY_HISTORY_JSON_PATH, [])
    history_by_id = {h["retry_attempt_id"]: h for h in history}
    out = []
    for r in retry_dispatch:
        delivery_id = r["delivery_id"]
        attempt_number = r["attempt"]
        retry_attempt_id = f"{delivery_id}:{attempt_number}"
        d = delivery_by_id.get(delivery_id, {})
        outbox_entry = r.get("outbox_entry", {})
        entry = {
            "retry_attempt_id": retry_attempt_id,
            "delivery_id": delivery_id,
            "notification_id": r["notification_id"],
            "escalation_id": outbox_entry.get("escalation_id", d.get("outbox_entry", {}).get("escalation_id")),
            "retry_status": r["result"],
            "attempt_number": attempt_number,
            "recipients": r.get("routing", {}).get("recipients", []),
            "escalation_level": outbox_entry.get("escalation_level", d.get("outbox_entry", {}).get("escalation_level")),
            "notification_type": outbox_entry.get("notification_type", d.get("outbox_entry", {}).get("notification_type")),
            "timestamp": r["retried_at"],
            "reason": r.get("reason", "")
        }
        history_by_id[retry_attempt_id] = entry
    # Deterministic ordering by timestamp, then retry_attempt_id
    history_out = sorted(history_by_id.values(), key=lambda x: (x["timestamp"], x["retry_attempt_id"]))
    save_json(RETRY_HISTORY_JSON_PATH, history_out)
    # Markdown report
    with open(RETRY_HISTORY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Email Retry-Attempt History Ledger\n\n")
        for h in history_out:
            f.write(f"- RetryAttempt: {h['retry_attempt_id']} | Delivery: {h['delivery_id']} | Notification: {h['notification_id']} | Escalation: {h['escalation_id']} | Status: {h['retry_status']} | Attempt: {h['attempt_number']} | Recipients: {', '.join(h['recipients'])} | Level: {h['escalation_level']} | Type: {h['notification_type']} | Time: {h['timestamp']} | Reason: {h['reason']}\n")

if __name__ == "__main__":
    main()
