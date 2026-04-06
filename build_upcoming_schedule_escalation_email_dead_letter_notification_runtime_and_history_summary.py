import json
from pathlib import Path
from datetime import datetime

DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery.json")
HISTORY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_delivery_history_ledger.json")
SUMMARY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_runtime_and_history_summary.json")
SUMMARY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_runtime_and_history_summary.md")

def main():
    delivery = json.load(open(DELIVERY_JSON_PATH, encoding="utf-8")) if DELIVERY_JSON_PATH.exists() else []
    history = json.load(open(HISTORY_JSON_PATH, encoding="utf-8")) if HISTORY_JSON_PATH.exists() else []
    now = datetime.utcnow().isoformat() + "Z"
    # Count outcomes
    sent = sum(1 for d in history if d["delivery_status"] == "sent")
    failed = sum(1 for d in history if d["delivery_status"] == "failed")
    skipped = sum(1 for d in history if d["delivery_status"] == "skipped")
    dedupe = len(history) == len(set((d["notification_id"], d["delivery_id"], d["delivery_status"]) for d in history))
    isolation = all("terminal_reason" in d for d in history)
    status = "ok" if dedupe and isolation else "error"
    summary = {
        "generated_at": now,
        "sent_count": sent,
        "failed_count": failed,
        "skipped_count": skipped,
        "dedupe": dedupe,
        "isolation": isolation,
        "status": status,
        "history_len": len(history),
        "delivery_len": len(delivery),
        "history": history,
        "delivery": delivery
    }
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Dead-Letter Notification Email Delivery-History Runtime Summary\n\n")
        f.write(f"Generated: {now}\n\n")
        f.write(f"- Sent: {sent}\n- Failed: {failed}\n- Skipped: {skipped}\n- Dedupe: {dedupe}\n- Isolation: {isolation}\n- Status: {status}\n\n")
        f.write("| notification_id | delivery_id | status | terminal_reason |\n")
        f.write("|-----------------|-------------|--------|-----------------|")
        for d in history:
            f.write(f"\n| {d['notification_id']} | {d['delivery_id']} | {d['delivery_status']} | {d['terminal_reason']} |")

if __name__ == "__main__":
    main()
