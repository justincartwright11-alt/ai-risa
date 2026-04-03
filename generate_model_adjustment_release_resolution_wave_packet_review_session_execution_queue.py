# v10.1 execution queue generator for AI-RISA review-session chain
# Contract: downstream execution workstream, do not mutate v8.8–v10.0, deterministic, one queue record per intake, source order, 4-digit IDs, no timestamps, no policy/release logic

import json
import os
from pathlib import Path

INPUT_PATH = os.path.join("ops", "model_adjustments")
INTAKE = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_intake.json")
OUTPUT_JSON = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_queue.json")
OUTPUT_MD = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_queue.md")

COLS = [
    "execution_queue_id",
    "execution_intake_id",
    "queue_position",
    "execution_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id"
]

def main():
    # Load intake records
    with open(INTAKE, "r", encoding="utf-8") as f:
        intake = json.load(f)["records"]
    queue_records = []
    for i, intake_record in enumerate(intake, 1):
        queue_records.append({
            "execution_queue_id": f"resolution-wave-packet-review-session-execution-queue-{i:04d}",
            "execution_intake_id": intake_record["execution_intake_id"],
            "queue_position": i,
            "execution_ready": True,
            "lineage_source_layer": "execution_intake",
            "lineage_source_file": INTAKE,
            "lineage_source_record_id": intake_record["execution_intake_id"]
        })
    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_execution_queue",
        "source_file": INTAKE,
        "source_record_count": len(queue_records),
        "record_count": len(queue_records),
        "records": queue_records
    }
    # Write JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    # Write Markdown
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(COLS) + " |\n")
        f.write("|" + "---|" * len(COLS) + "\n")
        for r in queue_records:
            f.write("| " + " | ".join(str(r[c]) for c in COLS) + " |\n")

if __name__ == "__main__":
    main()
