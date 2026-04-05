import json
from pathlib import Path
from datetime import datetime, timedelta

DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery_state.json")
HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_delivery_history_ledger.json")
RETRY_POLICY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_policy.json")
RETRY_POLICY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_policy.md")
RETRY_POLICY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_policy_state.json")

# Policy parameters
MAX_ATTEMPTS = 3
MIN_RETRY_SPACING_MINUTES = 60
TERMINAL_NONRETRY_REASONS = {"permanent-failure", "invalid-address", "manual-suppression"}


def main():
    delivery = json.load(open(DELIVERY_JSON_PATH, encoding="utf-8")) if DELIVERY_JSON_PATH.exists() else []
    history = json.load(open(HISTORY_JSON_PATH, encoding="utf-8")) if HISTORY_JSON_PATH.exists() else []
    now = datetime.utcnow()
    retry_policy = []
    state = {}
    for d in delivery:
        notification_id = d["notification_id"]
        delivery_id = d["delivery_id"]
        status = d["result"]
        terminal_reason = d.get("terminal_reason", "")
        # Find all history for this delivery
        attempts = [h for h in history if h["delivery_id"] == delivery_id]
        attempt_count = len(attempts)
        last_attempt_time = None
        if attempts:
            last_attempt_time = max(datetime.fromisoformat(a["timestamp"].replace("Z", "")) for a in attempts)
        eligible = False
        reason = ""
        if status == "sent":
            eligible = False
            reason = "Already sent, never retry"
        elif status == "failed":
            if terminal_reason in TERMINAL_NONRETRY_REASONS:
                eligible = False
                reason = f"Terminal non-retryable reason: {terminal_reason}"
            elif attempt_count >= MAX_ATTEMPTS:
                eligible = False
                reason = f"Max attempts reached ({attempt_count})"
            elif last_attempt_time and (now - last_attempt_time) < timedelta(minutes=MIN_RETRY_SPACING_MINUTES):
                eligible = False
                reason = f"Not yet due for retry (last attempt at {last_attempt_time.isoformat()})"
            else:
                eligible = True
                reason = "Eligible for retry"
        elif status == "skipped":
            eligible = False
            reason = "Skipped notifications are not retried by policy"
        else:
            eligible = False
            reason = f"Unknown or unhandled status: {status}"
        entry = {
            "notification_id": notification_id,
            "delivery_id": delivery_id,
            "status": status,
            "attempt_count": attempt_count,
            "last_attempt_time": last_attempt_time.isoformat() if last_attempt_time else None,
            "eligible": eligible,
            "reason": reason
        }
        retry_policy.append(entry)
        state[notification_id] = entry
    # Save machine-readable artifact
    with open(RETRY_POLICY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(retry_policy, f, indent=2, ensure_ascii=False)
        f.write("\n")
    # Save Markdown report
    with open(RETRY_POLICY_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Dead-Letter Notification Email Retry Policy\n\n")
        f.write(f"Max Attempts: {MAX_ATTEMPTS}\nMin Retry Spacing: {MIN_RETRY_SPACING_MINUTES} min\nTerminal Non-Retry Reasons: {', '.join(TERMINAL_NONRETRY_REASONS)}\n\n")
        f.write("| notification_id | delivery_id | status | attempts | last_attempt | eligible | reason |\n")
        f.write("|-----------------|-------------|--------|----------|--------------|----------|--------|\n")
        for e in retry_policy:
            f.write(f"| {e['notification_id']} | {e['delivery_id']} | {e['status']} | {e['attempt_count']} | {e['last_attempt_time'] or ''} | {e['eligible']} | {e['reason']} |\n")
    # Save state
    with open(RETRY_POLICY_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"policy": state, "generated_at": now.isoformat() + "Z"}, f, indent=2, ensure_ascii=False)
        f.write("\n")

if __name__ == "__main__":
    main()
