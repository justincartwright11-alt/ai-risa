"""
build_upcoming_schedule_escalation_email_dead_letter_ledger.py

v69.6: Deterministic dead-letter ledger for terminal escalation email deliveries
- Reads retry policy, delivery, delivery state, and retry history artifacts
- Identifies terminal (exhausted or non-retryable) escalation email deliveries
- Emits machine-readable dead-letter artifact, Markdown report, and state for dedupe
"""
import json
from pathlib import Path
from datetime import datetime

RETRY_POLICY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_policy.json")
RETRY_POLICY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_policy_state.json")
DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery_state.json")
RETRY_HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_history_ledger.json")
DEAD_LETTER_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_ledger.json")
DEAD_LETTER_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_ledger.md")
DEAD_LETTER_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_ledger_state.json")


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
    retry_policy = load_json(RETRY_POLICY_JSON_PATH, [])
    retry_policy_state = load_json(RETRY_POLICY_STATE_PATH, {})
    delivery = load_json(DELIVERY_JSON_PATH, [])
    delivery_state = load_json(DELIVERY_STATE_PATH, {})
    retry_history = load_json(RETRY_HISTORY_JSON_PATH, [])
    now = datetime.utcnow().isoformat() + "Z"
    # Index for lookups
    delivery_by_id = {d["delivery_id"]: d for d in delivery}
    retry_history_by_delivery = {}
    for h in retry_history:
        retry_history_by_delivery.setdefault(h["delivery_id"], []).append(h)
    # Load previous dead-letter state for dedupe
    dead_letter_state = load_json(DEAD_LETTER_STATE_PATH, {"dead_letters": {}})
    dead_letters = dead_letter_state.get("dead_letters", {})
    out = []
    for p in retry_policy:
        delivery_id = p["delivery_id"]
        notification_id = p["notification_id"]
        eligible = p.get("eligible", False)
        status = p.get("status", "")
        attempts = p.get("attempts", 1)
        max_attempts = p.get("max_attempts", 3)
        terminal_reason = p.get("terminal_reason", "")
        # Never dead-letter sent or retry-eligible
        if status == "sent" or eligible:
            continue
        # Only dead-letter if terminal (max attempts or non-retryable)
        if status == "failed" and (attempts >= max_attempts or terminal_reason):
            entry = {
                "dead_letter_id": f"{delivery_id}",
                "delivery_id": delivery_id,
                "notification_id": notification_id,
                "escalation_id": delivery_by_id.get(delivery_id, {}).get("outbox_entry", {}).get("escalation_id"),
                "terminal_reason": terminal_reason or "max attempts reached",
                "final_status": status,
                "attempt_count": attempts,
                "last_attempt_at": retry_history_by_delivery.get(delivery_id, [{}])[-1].get("timestamp"),
                "dead_lettered_at": now
            }
            dead_letters[entry["dead_letter_id"]] = entry
    # Save artifacts
    out = list(dead_letters.values())
    save_json(DEAD_LETTER_JSON_PATH, out)
    save_json(DEAD_LETTER_STATE_PATH, {"dead_letters": dead_letters, "generated_at": now})
    # Markdown report
    with open(DEAD_LETTER_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Escalation Email Dead-Letter Ledger\n\n")
        for e in out:
            f.write(f"- DeadLetter: {e['dead_letter_id']} | Delivery: {e['delivery_id']} | Notification: {e['notification_id']} | Escalation: {e['escalation_id']} | Status: {e['final_status']} | Attempts: {e['attempt_count']} | Last Attempt: {e['last_attempt_at']} | Reason: {e['terminal_reason']} | Dead-Lettered: {e['dead_lettered_at']}\n")

if __name__ == "__main__":
    main()
