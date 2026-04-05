# v10.2 execution dispatch generator for AI-RISA review-session chain
# Contract: downstream execution workstream, do not mutate v8.8–v10.1, deterministic, one dispatch record per queue, source order, 4-digit IDs, no timestamps, no policy/release logic

import json
import os
from pathlib import Path

INPUT_PATH = os.path.join("ops", "model_adjustments")
QUEUE = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_queue.json")
OUTPUT_JSON = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_dispatch.json")
OUTPUT_MD = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_dispatch.md")

COLS = [
    "execution_dispatch_id",
    "execution_queue_id",
    "dispatch_position",
    "dispatch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id"
]

def main():
    # Load queue records
    with open(QUEUE, "r", encoding="utf-8") as f:
        queue = json.load(f)["records"]
    dispatch_records = []
    for i, queue_record in enumerate(queue, 1):
        dispatch_records.append({
            "execution_dispatch_id": f"resolution-wave-packet-review-session-execution-dispatch-{i:04d}",
            "execution_queue_id": queue_record["execution_queue_id"],
            "dispatch_position": i,
            "dispatch_ready": queue_record["execution_ready"],
            "lineage_source_layer": "execution_queue",
            "lineage_source_file": QUEUE,
            "lineage_source_record_id": queue_record["execution_queue_id"]
        })
    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_execution_dispatch",
        "source_file": QUEUE,
        "source_record_count": len(dispatch_records),
        "record_count": len(dispatch_records),
        "records": dispatch_records
    }
    # Write JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    # Write Markdown
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(COLS) + " |\n")
        f.write("|" + "---|" * len(COLS) + "\n")
        for r in dispatch_records:
            f.write("| " + " | ".join(str(r[c]) for c in COLS) + " |\n")

if __name__ == "__main__":
    main()
