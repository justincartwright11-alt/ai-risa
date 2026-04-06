# v66.4: Upcoming Schedule Dispatch Consumer
# This script consumes the v66.3 queue sink and emits deterministic dispatch outcome artifacts.
import json
from pathlib import Path

SINK_PATH = Path("ops/events/upcoming_schedule_queue_sink.json")
DISPATCH_OUTCOME_PATH = Path("ops/events/upcoming_schedule_dispatch_outcome.json")
DISPATCH_REPORT_PATH = Path("ops/events/upcoming_schedule_dispatch_report.md")

# Controlled outcome states
DISPATCHED = "dispatched"
SKIPPED = "skipped"
FAILED = "failed"

# Load sink entries
def load_sink_entries():
    with SINK_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def is_eligible(entry):
    return (
        entry.get("queue_write_id")
        and entry.get("dispatch_outcome") == "simulated_success"
        and entry.get("ack_state") != "acked"
        and entry.get("retry_eligible", False)
    )

def dispatch_entry(entry):
    # Deterministic dispatch simulation: always succeed for this slice
    return {
        **entry,
        "dispatch_consumer_outcome": DISPATCHED,
        "dispatch_consumer_attempted": True,
        "dispatch_consumer_acknowledged": True,
        "dispatch_consumer_retry_count": entry.get("dispatch_consumer_retry_count", 0),
    }

def process_entries(entries):
    results = []
    for entry in entries:
        if is_eligible(entry):
            # Only dispatch if not already acknowledged
            if not entry.get("dispatch_consumer_acknowledged", False):
                result = dispatch_entry(entry)
            else:
                # Already acknowledged, do not redispatch
                result = {**entry, "dispatch_consumer_outcome": SKIPPED}
        else:
            # Not eligible, skip
            result = {**entry, "dispatch_consumer_outcome": SKIPPED}
        results.append(result)
    return results

def write_json(path, records):
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_markdown(path, records):
    lines = [
        "# Upcoming Schedule Dispatch Consumer Report",
        "",
        f"## Total Sink Entries: {len(records)}",
        f"## Dispatched: {sum(1 for r in records if r['dispatch_consumer_outcome']==DISPATCHED)}",
        f"## Skipped: {sum(1 for r in records if r['dispatch_consumer_outcome']==SKIPPED)}",
        f"## Failed: {sum(1 for r in records if r['dispatch_consumer_outcome']==FAILED)}",
        "",
        "## Dispatch Outcomes",
    ]
    for rec in records:
        lines.append(
            f"- **ID:** {rec['event_id']} | **Dispatch Outcome:** {rec['dispatch_consumer_outcome']} | "
            f"**Ack:** {rec.get('dispatch_consumer_acknowledged', False)} | "
            f"**Retry Count:** {rec.get('dispatch_consumer_retry_count', 0)}"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

def main():
    entries = load_sink_entries()
    results = process_entries(entries)
    write_json(DISPATCH_OUTCOME_PATH, results)
    write_markdown(DISPATCH_REPORT_PATH, results)

if __name__ == "__main__":
    main()
