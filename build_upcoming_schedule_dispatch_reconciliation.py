# v66.5: Upcoming Schedule Dispatch Reconciliation
# Reconcile dispatch outcomes back into the authoritative queue sink state.
import json
from pathlib import Path

SINK_PATH = Path("ops/events/upcoming_schedule_queue_sink.json")
OUTCOME_PATH = Path("ops/events/upcoming_schedule_dispatch_outcome.json")
RECONCILED_SINK_PATH = Path("ops/events/upcoming_schedule_queue_sink_reconciled.json")
RECONCILE_REPORT_PATH = Path("ops/events/upcoming_schedule_reconciliation_report.md")

# Load sink and outcome entries
def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def reconcile_sink(sink, outcomes):
    # Build outcome map by queue_write_id for deterministic matching
    outcome_map = {o["queue_write_id"]: o for o in outcomes if o.get("queue_write_id")}
    reconciled = []
    for entry in sink:
        qid = entry.get("queue_write_id")
        out = outcome_map.get(qid)
        new_entry = dict(entry)
        if out:
            outcome = out.get("dispatch_consumer_outcome")
            if outcome == "dispatched":
                new_entry["ack_state"] = "acked"
            elif outcome == "failed":
                new_entry["ack_state"] = entry.get("ack_state")
                new_entry["dispatch_consumer_retry_count"] = entry.get("dispatch_consumer_retry_count", 0) + 1
            elif outcome == "skipped":
                new_entry["ack_state"] = entry.get("ack_state")
                new_entry["dispatch_consumer_retry_count"] = entry.get("dispatch_consumer_retry_count", 0)
            # preserve all other fields
        # If no outcome, preserve entry unchanged
        reconciled.append(new_entry)
    return reconciled

def write_json(path, records):
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_markdown(path, records):
    lines = [
        "# Upcoming Schedule Dispatch Reconciliation Report",
        "",
        f"## Total Sink Entries: {len(records)}",
        f"## Acked: {sum(1 for r in records if r.get('ack_state')=='acked')}",
        f"## Retry Incremented: {sum(1 for r in records if r.get('dispatch_consumer_retry_count', 0) > 0)}",
        f"## Skipped: {sum(1 for r in records if r.get('ack_state') != 'acked' and r.get('dispatch_consumer_retry_count', 0) == 0)}",
        "",
        "## Reconciled Entries",
    ]
    for rec in records:
        lines.append(
            f"- **ID:** {rec['event_id']} | **Ack:** {rec.get('ack_state')} | "
            f"**Retry Count:** {rec.get('dispatch_consumer_retry_count', 0)}"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

def main():
    sink = load_json(SINK_PATH)
    outcomes = load_json(OUTCOME_PATH)
    reconciled = reconcile_sink(sink, outcomes)
    write_json(RECONCILED_SINK_PATH, reconciled)
    write_markdown(RECONCILE_REPORT_PATH, reconciled)

if __name__ == "__main__":
    main()
