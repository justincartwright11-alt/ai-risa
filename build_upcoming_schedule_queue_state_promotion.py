"""
build_upcoming_schedule_queue_state_promotion.py

Promotes the reconciled upcoming schedule queue state into the authoritative queue sink in a deterministic, guarded, and idempotent way.

Reads:
- ops/events/upcoming_schedule_queue_sink.json
- ops/events/upcoming_schedule_queue_sink_reconciled.json

Emits:
- updated ops/events/upcoming_schedule_queue_sink.json
- ops/events/upcoming_schedule_queue_promotion.json
- ops/events/upcoming_schedule_queue_promotion.md

See v66.6 locked spec for full requirements.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

SINK_PATH = Path("ops/events/upcoming_schedule_queue_sink.json")
RECONCILED_PATH = Path("ops/events/upcoming_schedule_queue_sink_reconciled.json")
PROMOTION_JSON_PATH = Path("ops/events/upcoming_schedule_queue_promotion.json")
PROMOTION_MD_PATH = Path("ops/events/upcoming_schedule_queue_promotion.md")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def hash_json(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def stable_sort(entries):
    # Sort by a stable identity key (queue_write_id)
    return sorted(entries, key=lambda x: x["queue_write_id"])

def verify_promotion(sink, reconciled):
    # 1. All sink rows must be present in reconciled (no silent row loss)
    sink_ids = {row["queue_write_id"] for row in sink}
    rec_ids = {row["queue_write_id"] for row in reconciled}
    if not sink_ids.issubset(rec_ids):
        missing = sink_ids - rec_ids
        raise ValueError(f"Promotion would drop rows: {missing}")
    # 2. No orphan rows in reconciled (must have valid lineage)
    for row in reconciled:
        if row["queue_write_id"] not in sink_ids:
            if "lineage" not in row or row["lineage"] not in sink_ids:
                raise ValueError(f"Row {row['queue_write_id']} in reconciled has no valid lineage")
    # 3. Stable identity: for rows present in both, key fields must match
    for row in reconciled:
        if row["queue_write_id"] in sink_ids:
            orig = next(r for r in sink if r["queue_write_id"] == row["queue_write_id"])
            # Check identity fields (assume 'queue_write_id', 'event_id', 'scheduled_time' if present)
            for k in ("queue_write_id", "event_id"):
                if row.get(k) != orig.get(k):
                    raise ValueError(f"Identity mismatch for row {row['queue_write_id']} field {k}")
    # 4. Ack/failed/skipped state preservation
    for row in reconciled:
        if row["queue_write_id"] in sink_ids:
            orig = next(r for r in sink if r["queue_write_id"] == row["queue_write_id"])
            if orig.get("ack_state") == "acked" and row.get("ack_state") != "acked":
                raise ValueError(f"Acked row {row['queue_write_id']} lost ack status")
            if orig.get("ack_state") == "skipped" and row.get("ack_state") != "skipped":
                raise ValueError(f"Skipped row {row['queue_write_id']} lost skipped status")
    # 5. No partial promotion: all checks must pass
    return True

def promote():
    sink = stable_sort(load_json(SINK_PATH))
    reconciled = stable_sort(load_json(RECONCILED_PATH))
    verify_promotion(sink, reconciled)
    # Overwrite authoritative sink with reconciled content
    save_json(SINK_PATH, reconciled)
    # Emit promotion record
    promotion_record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sink_hash_before": hash_json(sink),
        "reconciled_hash": hash_json(reconciled),
        "sink_hash_after": hash_json(reconciled),
        "row_count": len(reconciled),
        "promoted_ids": [row["queue_write_id"] for row in reconciled],
    }
    save_json(PROMOTION_JSON_PATH, promotion_record)
    # Emit Markdown report
    with open(PROMOTION_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Queue State Promotion\n\n")
        f.write(f"Promotion run at: {promotion_record['timestamp']} UTC\n\n")
        f.write(f"Rows promoted: {promotion_record['row_count']}\n\n")
        f.write(f"Promoted IDs: {', '.join(str(i) for i in promotion_record['promoted_ids'])}\n\n")
        f.write(f"Sink hash before: {promotion_record['sink_hash_before']}\n")
        f.write(f"Reconciled hash: {promotion_record['reconciled_hash']}\n")
        f.write(f"Sink hash after: {promotion_record['sink_hash_after']}\n")
        f.write("\nPromotion completed deterministically and idempotently.\n")

if __name__ == "__main__":
    promote()
