"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_runtime_summary.py

v71.9: Deterministic runtime summary for manual-intervention assignment for escalation email dead-letter notification email path
- Reads assignment artifact and state
- Emits runtime summary (JSON) and Markdown report
"""
import json
from pathlib import Path
from datetime import datetime

ASSIGN_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment.json")
ASSIGN_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_state.json")
SUMMARY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_runtime_summary.json")
SUMMARY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_assignment_runtime_summary.md")

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
    assignments = load_json(ASSIGN_JSON_PATH, [])
    assign_state = load_json(ASSIGN_STATE_PATH, {})
    now = datetime.utcnow().isoformat() + "Z"

    open_assignments = [a for a in assignments]
    owners = set(a["owner"] for a in assignments)
    priorities = set(a["priority"] for a in assignments)
    dedupe_keys = set(a["dedupe_key"] for a in assignments)

    summary = {
        "generated_at": now,
        "assignment_count": len(open_assignments),
        "owners": sorted(list(owners)),
        "priorities": sorted(list(priorities)),
        "dedupe_count": len(dedupe_keys),
        "assignment_ids": [a["assignment_id"] for a in open_assignments],
    }
    save_json(SUMMARY_JSON_PATH, summary)

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention Assignment Runtime Summary\n\n")
        f.write(f"- Generated: {now}\n")
        f.write(f"- Assignment Count: {len(open_assignments)}\n")
        f.write(f"- Owners: {', '.join(summary['owners']) if summary['owners'] else 'None'}\n")
        f.write(f"- Priorities: {', '.join(summary['priorities']) if summary['priorities'] else 'None'}\n")
        f.write(f"- Dedupe Keys: {len(dedupe_keys)}\n")
        f.write(f"- Assignment IDs: {', '.join(summary['assignment_ids']) if summary['assignment_ids'] else 'None'}\n")

if __name__ == "__main__":
    main()
