"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_retry_history_ledger.py

v71.1: Deterministic retry-attempt history ledger for escalation email dead-letter notification email delivery
- Reads retry-dispatch, delivery, and state artifacts
- Records one history entry per retry attempt
- Emits retry-history ledger, Markdown report, and state for rerun dedupe
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

RETRY_DISPATCH_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_dispatch.json")
RETRY_DISPATCH_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_dispatch_state.json")
DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery_state.json")
HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_history_ledger.json")
HISTORY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_history_ledger.md")
HISTORY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_history_ledger_state.json")

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

def make_retry_attempt_id(notification_id, delivery_id, retried_at):
    # Deterministic hash for retry attempt
    base = f"{notification_id}|{delivery_id}|{retried_at}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

def main():
    retry_dispatch = load_json(RETRY_DISPATCH_JSON_PATH, [])
    delivery = load_json(DELIVERY_JSON_PATH, [])
    delivery_by_id = {d["delivery_id"]: d for d in delivery}
    history = load_json(HISTORY_JSON_PATH, [])
    history_state = load_json(HISTORY_STATE_PATH, {"attempts": {}})
    attempts = dict(history_state.get("attempts", {}))
    ledger = []
    for r in retry_dispatch:
        notification_id = r["notification_id"]
        delivery_id = r["delivery_id"]
        retried_at = r["retried_at"]
        retry_status = r["result"]
        reason = r.get("reason", "")
        d = delivery_by_id.get(delivery_id, {})
        dead_letter_id = d.get("dead_letter_id", "")
        notification_type = d.get("notification_type", "dead_letter")
        routed_recipients = d.get("routed_recipients", [])
        attempt_number = d.get("attempt_number", 1)
        terminal_reason = d.get("terminal_reason", "")
        retry_attempt_id = make_retry_attempt_id(notification_id, delivery_id, retried_at)
        if retry_attempt_id in attempts:
            continue  # dedupe
        entry = {
            "retry_attempt_id": retry_attempt_id,
            "delivery_id": delivery_id,
            "notification_id": notification_id,
            "dead_letter_id": dead_letter_id,
            "retry_status": retry_status,
            "attempt_number": attempt_number,
            "routed_recipients": routed_recipients,
            "notification_type": notification_type,
            "retried_at": retried_at,
            "retry_reason": reason,
            "terminal_reason": terminal_reason
        }
        ledger.append(entry)
        attempts[retry_attempt_id] = entry
    # Save artifacts
    save_json(HISTORY_JSON_PATH, ledger)
    save_json(HISTORY_STATE_PATH, {"attempts": attempts, "generated_at": datetime.utcnow().isoformat() + "Z"})
    # Markdown report
    with open(HISTORY_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Dead-Letter Notification Email Retry-Attempt History Ledger\n\n")
        for e in ledger:
            f.write(f"- RetryAttempt: {e['retry_attempt_id']} | Notification: {e['notification_id']} | Delivery: {e['delivery_id']} | Status: {e['retry_status']} | Attempt: {e['attempt_number']} | Recipients: {e['routed_recipients']} | Retried: {e['retried_at']} | Reason: {e['retry_reason']} | Terminal: {e['terminal_reason']}\n")

if __name__ == "__main__":
    main()
