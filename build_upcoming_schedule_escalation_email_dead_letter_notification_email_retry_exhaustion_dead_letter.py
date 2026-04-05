"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_retry_exhaustion_dead_letter.py

v71.3: Deterministic dead-letter ledger for escalation email dead-letter notification email deliveries after retry exhaustion
- Reads retry-policy, delivery, and retry-history artifacts
- Classifies terminal deliveries (max attempts, non-retryable, no further retry)
- Emits dead-letter ledger, Markdown report, and state for rerun dedupe
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

RETRY_POLICY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_policy.json")
RETRY_POLICY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_policy_state.json")
DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery_state.json")
RETRY_HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_history_ledger.json")
DEAD_LETTER_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_exhaustion_dead_letter.json")
DEAD_LETTER_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_exhaustion_dead_letter.md")
DEAD_LETTER_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_exhaustion_dead_letter_state.json")

TERMINAL_NONRETRY_REASONS = {"permanent-failure", "invalid-address", "manual-suppression"}

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

def make_dead_letter_id(notification_id, delivery_id):
    base = f"{notification_id}|{delivery_id}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

def main():
    retry_policy = load_json(RETRY_POLICY_JSON_PATH, [])
    delivery = load_json(DELIVERY_JSON_PATH, [])
    retry_history = load_json(RETRY_HISTORY_JSON_PATH, [])
    state = load_json(DEAD_LETTER_STATE_PATH, {"dead_lettered": {}})
    dead_lettered = dict(state.get("dead_lettered", {}))
    ledger = []
    delivery_by_id = {d["delivery_id"]: d for d in delivery}
    retry_history_by_delivery = {}
    for h in retry_history:
        retry_history_by_delivery.setdefault(h["delivery_id"], []).append(h)
    for entry in retry_policy:
        notification_id = entry["notification_id"]
        delivery_id = entry["delivery_id"]
        status = entry["status"]
        eligible = entry["eligible"]
        reason = entry["reason"]
        d = delivery_by_id.get(delivery_id, {})
        if status == "sent":
            continue  # never dead-letter sent
        if eligible:
            continue  # not dead-lettered if still retry-eligible
        # Only dead-letter if max attempts or non-retryable
        terminal = False
        terminal_reason = reason
        if "max attempts" in reason.lower() or any(r in reason for r in TERMINAL_NONRETRY_REASONS):
            terminal = True
        if not terminal:
            continue
        dead_letter_id = make_dead_letter_id(notification_id, delivery_id)
        if dead_letter_id in dead_lettered:
            continue  # dedupe
        # Find last retry attempt if any
        last_retry = None
        if delivery_id in retry_history_by_delivery:
            last_retry = max(retry_history_by_delivery[delivery_id], key=lambda h: h["retried_at"])
        entry_obj = {
            "dead_letter_id": dead_letter_id,
            "notification_id": notification_id,
            "delivery_id": delivery_id,
            "terminal_reason": terminal_reason,
            "last_retry_attempt": last_retry["retry_attempt_id"] if last_retry else None,
            "last_retry_status": last_retry["retry_status"] if last_retry else None,
            "last_retry_time": last_retry["retried_at"] if last_retry else None,
            "recorded_at": datetime.utcnow().isoformat() + "Z"
        }
        ledger.append(entry_obj)
        dead_lettered[dead_letter_id] = entry_obj
    # Save artifacts
    save_json(DEAD_LETTER_JSON_PATH, ledger)
    save_json(DEAD_LETTER_STATE_PATH, {"dead_lettered": dead_lettered, "generated_at": datetime.utcnow().isoformat() + "Z"})
    # Markdown report
    with open(DEAD_LETTER_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Dead-Letter Notification Email Retry-Exhaustion Dead-Letter Ledger\n\n")
        for e in ledger:
            f.write(f"- DeadLetter: {e['dead_letter_id']} | Notification: {e['notification_id']} | Delivery: {e['delivery_id']} | Terminal: {e['terminal_reason']} | LastRetry: {e['last_retry_attempt']} | Status: {e['last_retry_status']} | Time: {e['last_retry_time']} | Recorded: {e['recorded_at']}\n")

if __name__ == "__main__":
    main()
