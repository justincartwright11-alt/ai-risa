"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.md
- Contract: Consumer family only, do not mutate v8.8–v16.0, one queue record per intake, preserve order, deterministic 4-digit IDs, exact-once coverage, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.md"

MD_COLUMNS = [
    "consumer_queue_id",
    "consumer_intake_id",
    "queue_position",
    "consumer_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    with open(INTAKE_FILE, "r", encoding="utf-8") as f:
        intake = json.load(f)
    intake_records = intake["records"]

    queue_records = []
    for i, intake_record in enumerate(intake_records):
        queue_id = f"resolution-wave-packet-review-session-consumer-queue-{i+1:04d}"
        queue_record = {
            "consumer_queue_id": queue_id,
            "consumer_intake_id": intake_record["consumer_intake_id"],
            "queue_position": i+1,
            "consumer_ready": True,
            "lineage_source_layer": "consumer_intake",
            "lineage_source_file": INTAKE_FILE,
            "lineage_source_record_id": intake_record["consumer_intake_id"],
        }
        queue_records.append(queue_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_queue",
        "source_file": INTAKE_FILE,
        "source_record_count": len(intake_records),
        "record_count": len(queue_records),
        "records": queue_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v16.1 Controlled Release Resolution Wave Packet Review Session Consumer Queue\n\n")
        f.write("## Source File\n")
        f.write(f"- {INTAKE_FILE}\n\n")
        f.write("## Queue Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        for record in queue_records:
            row = [
                str(record[col]) if not isinstance(record[col], bool) else str(record[col]).lower()
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
