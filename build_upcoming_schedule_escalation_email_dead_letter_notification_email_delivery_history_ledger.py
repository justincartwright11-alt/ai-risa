import json
from pathlib import Path
from datetime import datetime

OUTBOX_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_outbox.json")
DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery.json")
HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_delivery_history_ledger.json")
HISTORY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_delivery_history_ledger.md")


def main():
    outbox = json.load(open(OUTBOX_JSON_PATH, encoding="utf-8")) if OUTBOX_JSON_PATH.exists() else []
    delivery = json.load(open(DELIVERY_JSON_PATH, encoding="utf-8")) if DELIVERY_JSON_PATH.exists() else []
    # Index for dedupe
    history = []
    seen = set()
    for d in delivery:
        key = (d["notification_id"], d["delivery_id"], d["result"])
        if key in seen:
            continue
        seen.add(key)
        entry = {
            "notification_id": d["notification_id"],
            "dead_letter_id": d["dead_letter_id"],
            "delivery_id": d["delivery_id"],
            "delivery_status": d["result"],
            "recipients": d.get("recipients", []),
            "notification_type": d["notification_type"],
            "attempt_count": 1,  # v1: always 1 per delivery
            "timestamp": d["dispatched_at"],
            "terminal_reason": d.get("terminal_reason", d.get("reason", "")),
        }
        history.append(entry)
    # Save machine-readable ledger
    with open(HISTORY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        f.write("\n")
    # Save Markdown report
    with open(HISTORY_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Dead-Letter Notification Email Delivery History Ledger\n\n")
        f.write("| notification_id | dead_letter_id | delivery_id | delivery_status | recipients | notification_type | attempt_count | timestamp | terminal_reason |\n")
        f.write("|-----------------|----------------|-------------|----------------|------------|-------------------|---------------|-----------|----------------|\n")
        for e in history:
            f.write(f"| {e['notification_id']} | {e['dead_letter_id']} | {e['delivery_id']} | {e['delivery_status']} | {', '.join(e['recipients'])} | {e['notification_type']} | {e['attempt_count']} | {e['timestamp']} | {e['terminal_reason']} |\n")

if __name__ == "__main__":
    main()
