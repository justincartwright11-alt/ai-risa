"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla_runtime_summary.py

v72.1: Deterministic runtime summary for manual-intervention SLA path for escalation email dead-letter notification email
- Reads SLA artifact and state
- Emits runtime summary (JSON) and Markdown report
"""
import json
from pathlib import Path
from datetime import datetime

SLA_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla.json")
SLA_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla_state.json")
SUMMARY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla_runtime_summary.json")
SUMMARY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_sla_runtime_summary.md")

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
    sla = load_json(SLA_JSON_PATH, [])
    sla_state = load_json(SLA_STATE_PATH, {})
    now = datetime.utcnow().isoformat() + "Z"

    within_window = [s for s in sla if s["sla_status"] == "within_window"]
    due_soon = [s for s in sla if s["sla_status"] == "due_soon"]
    overdue = [s for s in sla if s["sla_status"] == "overdue"]
    cleared = [s for s in sla if s["sla_status"] == "cleared"]
    dedupe_keys = set(s["sla_id"] for s in sla)
    failure_isolation = any(s.get("sla_reason") == "failure-isolation" for s in sla)
    terminal_statuses = set(s["sla_status"] for s in sla)

    summary = {
        "generated_at": now,
        "within_window_count": len(within_window),
        "due_soon_count": len(due_soon),
        "overdue_count": len(overdue),
        "cleared_count": len(cleared),
        "dedupe_count": len(dedupe_keys),
        "failure_isolation": failure_isolation,
        "terminal_statuses": list(terminal_statuses),
    }
    save_json(SUMMARY_JSON_PATH, summary)

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention SLA Runtime Summary\n\n")
        f.write(f"- Generated: {now}\n")
        f.write(f"- Within SLA Window: {len(within_window)}\n")
        f.write(f"- Due Soon: {len(due_soon)}\n")
        f.write(f"- Overdue: {len(overdue)}\n")
        f.write(f"- Cleared: {len(cleared)}\n")
        f.write(f"- Dedupe Keys: {len(dedupe_keys)}\n")
        f.write(f"- Failure Isolation: {failure_isolation}\n")
        f.write(f"- Terminal Statuses: {', '.join(terminal_statuses) if terminal_statuses else 'None'}\n")

if __name__ == "__main__":
    main()
