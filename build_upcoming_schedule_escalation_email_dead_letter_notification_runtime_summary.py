"""
build_upcoming_schedule_escalation_email_dead_letter_notification_runtime_summary.py

v71.5: Deterministic runtime summary for escalation email dead-letter notification email dead-letter path
- Reads delivery, retry, and dead-letter artifacts
- Emits runtime summary (JSON) and Markdown report
"""
import json
from pathlib import Path
from datetime import datetime

DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery.json")
RETRY_POLICY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_policy.json")
DEAD_LETTER_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_retry_exhaustion_dead_letter.json")
SUMMARY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_runtime_summary.json")
SUMMARY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_runtime_summary.md")

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
    retry_policy = load_json(RETRY_POLICY_JSON_PATH, [])
    dead_letter = load_json(DEAD_LETTER_JSON_PATH, [])
    now = datetime.utcnow().isoformat() + "Z"

    sent = [d for d in delivery if d["result"] == "sent"]
    retry_eligible = [r for r in retry_policy if r.get("eligible") and r["status"] != "sent"]
    dead_lettered = [d for d in dead_letter]
    dedupe_keys = set(d["dedupe_key"] for d in delivery)
    failure_isolation = any(d.get("terminal_reason") == "failure-isolation" for d in delivery)
    terminal_statuses = set(d["result"] for d in delivery if d["result"] in ("failed", "skipped"))

    summary = {
        "generated_at": now,
        "sent_count": len(sent),
        "retry_eligible_count": len(retry_eligible),
        "dead_lettered_count": len(dead_lettered),
        "dedupe_count": len(dedupe_keys),
        "failure_isolation": failure_isolation,
        "terminal_statuses": list(terminal_statuses),
        "dead_letter_classification": [d.get("classification") for d in dead_lettered],
    }
    save_json(SUMMARY_JSON_PATH, summary)

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Email Dead-Letter Notification Runtime Summary\n\n")
        f.write(f"- Generated: {now}\n")
        f.write(f"- Sent: {len(sent)}\n")
        f.write(f"- Retry-Eligible: {len(retry_eligible)}\n")
        f.write(f"- Dead-Lettered: {len(dead_lettered)}\n")
        f.write(f"- Dedupe Keys: {len(dedupe_keys)}\n")
        f.write(f"- Failure Isolation: {failure_isolation}\n")
        f.write(f"- Terminal Statuses: {', '.join(terminal_statuses) if terminal_statuses else 'None'}\n")
        f.write(f"- Dead-Letter Classifications: {', '.join(str(c) for c in summary['dead_letter_classification']) if summary['dead_letter_classification'] else 'None'}\n")

if __name__ == "__main__":
    main()
