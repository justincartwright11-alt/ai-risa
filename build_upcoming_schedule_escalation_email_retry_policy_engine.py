"""
build_upcoming_schedule_escalation_email_retry_policy_engine.py

v69.0: Deterministic escalation email retry policy engine
- Reads delivery, delivery state, and delivery history artifacts
- Computes retry eligibility for escalation email deliveries
- Emits machine-readable retry-policy artifact and Markdown report
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery_state.json")
HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_delivery_history_ledger.json")
RETRY_POLICY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_policy.json")
RETRY_POLICY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_policy.md")
RETRY_POLICY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_policy_state.json")

# Policy constants
MAX_ATTEMPTS = 3
MIN_RETRY_SPACING_MINUTES = 30
TERMINAL_FAILURE_REASONS = [
    "permanent failure", "invalid address", "blocked", "blacklisted"
]


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
    delivery_state = load_json(DELIVERY_STATE_PATH, {})
    history = load_json(HISTORY_JSON_PATH, [])
    now = datetime.utcnow()
    # Index history by delivery_id
    history_by_id = {h["delivery_id"]: h for h in history}
    policy = []
    for d in delivery:
        delivery_id = d["delivery_id"]
        notification_id = d["notification_id"]
        status = d["result"]
        reason = d.get("reason", "")
        attempts = history_by_id.get(delivery_id, {}).get("attempt_count", 1)
        last_time = history_by_id.get(delivery_id, {}).get("timestamp", d.get("dispatched_at"))
        eligible = False
        terminal = False
        next_eligible_time = None
        # Never retry sent
        if status == "sent":
            eligible = False
            terminal = True
        # Retryable failed
        elif status == "failed":
            if any(term in reason.lower() for term in TERMINAL_FAILURE_REASONS):
                eligible = False
                terminal = True
            elif attempts >= MAX_ATTEMPTS:
                eligible = False
                terminal = True
            else:
                # Check retry spacing
                last_dt = datetime.fromisoformat(last_time.replace("Z", ""))
                next_eligible_time = last_dt + timedelta(minutes=MIN_RETRY_SPACING_MINUTES)
                if now >= next_eligible_time:
                    eligible = True
                else:
                    eligible = False
        # Skipped: only retry if explicitly allowed (here: never)
        elif status == "skipped":
            eligible = False
            terminal = True
        else:
            eligible = False
            terminal = True
        policy.append({
            "delivery_id": delivery_id,
            "notification_id": notification_id,
            "status": status,
            "attempts": attempts,
            "last_time": last_time,
            "eligible": eligible,
            "terminal": terminal,
            "next_eligible_time": next_eligible_time.isoformat() + "Z" if next_eligible_time else None,
            "reason": reason
        })
    save_json(RETRY_POLICY_JSON_PATH, policy)
    # Markdown report
    with open(RETRY_POLICY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Email Retry Policy\n\n")
        for p in policy:
            f.write(f"- Delivery: {p['delivery_id']} | Notification: {p['notification_id']} | Status: {p['status']} | Attempts: {p['attempts']} | Eligible: {p['eligible']} | Terminal: {p['terminal']} | Next: {p['next_eligible_time']} | Reason: {p['reason']}\n")
    # State artifact for dedupe
    save_json(RETRY_POLICY_STATE_PATH, {"policy": policy, "generated_at": now.isoformat() + "Z"})

if __name__ == "__main__":
    main()
