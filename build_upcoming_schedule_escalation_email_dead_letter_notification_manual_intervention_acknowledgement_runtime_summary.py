"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_runtime_summary.py

v72.3: Deterministic runtime summary for manual-intervention acknowledgement path for escalation email dead-letter notification email
- Reads acknowledgement-state artifact and state
- Emits runtime summary (JSON) and Markdown report
"""
import json
from pathlib import Path
from datetime import datetime

ACK_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state.json")
ACK_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_state_state.json")
SUMMARY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_runtime_summary.json")
SUMMARY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_acknowledgement_runtime_summary.md")

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
    ack = load_json(ACK_JSON_PATH, [])
    ack_state = load_json(ACK_STATE_PATH, {})
    now = datetime.utcnow().isoformat() + "Z"

    unacknowledged = [a for a in ack if a["ack_status"] == "unacknowledged"]
    acknowledged = [a for a in ack if a["ack_status"] == "acknowledged"]
    cleared = [a for a in ack if a["ack_status"] == "cleared"]
    dedupe_keys = set(a["ack_id"] for a in ack)
    failure_isolation = any(a.get("ack_reason") == "failure-isolation" for a in ack)
    terminal_statuses = set(a["ack_status"] for a in ack)

    summary = {
        "generated_at": now,
        "unacknowledged_count": len(unacknowledged),
        "acknowledged_count": len(acknowledged),
        "cleared_count": len(cleared),
        "dedupe_count": len(dedupe_keys),
        "failure_isolation": failure_isolation,
        "terminal_statuses": list(terminal_statuses),
    }
    save_json(SUMMARY_JSON_PATH, summary)

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention Acknowledgement Runtime Summary\n\n")
        f.write(f"- Generated: {now}\n")
        f.write(f"- Unacknowledged: {len(unacknowledged)}\n")
        f.write(f"- Acknowledged: {len(acknowledged)}\n")
        f.write(f"- Cleared: {len(cleared)}\n")
        f.write(f"- Dedupe Keys: {len(dedupe_keys)}\n")
        f.write(f"- Failure Isolation: {failure_isolation}\n")
        f.write(f"- Terminal Statuses: {', '.join(terminal_statuses) if terminal_statuses else 'None'}\n")

if __name__ == "__main__":
    main()
