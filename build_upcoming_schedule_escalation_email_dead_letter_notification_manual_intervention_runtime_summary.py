"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_runtime_summary.py

v71.7: Deterministic runtime summary for manual intervention queue for escalation email dead-letter notification email path
- Reads manual intervention queue and state
- Emits runtime summary (JSON) and Markdown report
"""
import json
from pathlib import Path
from datetime import datetime

QUEUE_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue.json")
QUEUE_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_queue_state.json")
SUMMARY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_runtime_summary.json")
SUMMARY_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_runtime_summary.md")

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
    queue = load_json(QUEUE_JSON_PATH, [])
    queue_state = load_json(QUEUE_STATE_PATH, {"interventions": {}})
    now = datetime.utcnow().isoformat() + "Z"

    open_items = [i for i in queue if i["intervention_status"] in ("open", "active")]
    cleared_items = [i for i in queue if i["intervention_status"] == "cleared"]
    dedupe_keys = set(i["dedupe_key"] for i in queue)
    failure_isolation = any(i.get("terminal_reason") == "failure-isolation" for i in queue)

    summary = {
        "generated_at": now,
        "open_count": len(open_items),
        "cleared_count": len(cleared_items),
        "dedupe_count": len(dedupe_keys),
        "failure_isolation": failure_isolation,
        "open_interventions": [i["intervention_id"] for i in open_items],
        "cleared_interventions": [i["intervention_id"] for i in cleared_items],
    }
    save_json(SUMMARY_JSON_PATH, summary)

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Manual Intervention Queue Runtime Summary\n\n")
        f.write(f"- Generated: {now}\n")
        f.write(f"- Open Interventions: {len(open_items)}\n")
        f.write(f"- Cleared Interventions: {len(cleared_items)}\n")
        f.write(f"- Dedupe Keys: {len(dedupe_keys)}\n")
        f.write(f"- Failure Isolation: {failure_isolation}\n")
        f.write(f"- Open IDs: {', '.join(summary['open_interventions']) if summary['open_interventions'] else 'None'}\n")
        f.write(f"- Cleared IDs: {', '.join(summary['cleared_interventions']) if summary['cleared_interventions'] else 'None'}\n")

if __name__ == "__main__":
    main()
