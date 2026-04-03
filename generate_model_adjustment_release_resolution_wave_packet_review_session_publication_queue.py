"""
generate_model_adjustment_release_resolution_wave_packet_review_session_publication_queue.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.md
- Contract: Publication workstream only, do not mutate v8.8–v13.0, one queue record per intake record, preserve source order, deterministic 4-digit IDs, exact-once coverage, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.md"

QUEUE_ID_PREFIX = "resolution-wave-packet-review-session-publication-queue-"

MD_COLUMNS = [
    "publication_queue_id",
    "publication_intake_id",
    "queue_position",
    "publication_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]


def main():
    with open(INTAKE_FILE, "r", encoding="utf-8") as f:
        intake_data = json.load(f)
    intake_records = intake_data["records"]

    queue_records = []
    for i, intake_record in enumerate(intake_records, 1):
        queue_record = {
            "publication_queue_id": f"{QUEUE_ID_PREFIX}{i:04d}",
            "publication_intake_id": intake_record["publication_intake_id"],
            "queue_position": i,
            "publication_ready": True,
            "lineage_source_layer": "publication_intake",
            "lineage_source_file": INTAKE_FILE,
            "lineage_source_record_id": intake_record["publication_intake_id"],
        }
        queue_records.append(queue_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_publication_queue",
        "source_file": INTAKE_FILE,
        "source_record_count": len(queue_records),
        "record_count": len(queue_records),
        "records": queue_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
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
