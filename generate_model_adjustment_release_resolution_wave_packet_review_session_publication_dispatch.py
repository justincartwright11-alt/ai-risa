"""
generate_model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.md
- Contract: Publication workstream only, do not mutate v8.8–v13.1, one dispatch record per queue record, preserve source order, deterministic 4-digit IDs, exact-once coverage, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.md"

DISPATCH_ID_PREFIX = "resolution-wave-packet-review-session-publication-dispatch-"

MD_COLUMNS = [
    "publication_dispatch_id",
    "publication_queue_id",
    "dispatch_position",
    "dispatch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]


def main():
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue_data = json.load(f)
    queue_records = queue_data["records"]

    dispatch_records = []
    for i, queue_record in enumerate(queue_records, 1):
        dispatch_record = {
            "publication_dispatch_id": f"{DISPATCH_ID_PREFIX}{i:04d}",
            "publication_queue_id": queue_record["publication_queue_id"],
            "dispatch_position": i,
            "dispatch_ready": True,
            "lineage_source_layer": "publication_queue",
            "lineage_source_file": QUEUE_FILE,
            "lineage_source_record_id": queue_record["publication_queue_id"],
        }
        dispatch_records.append(dispatch_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch",
        "source_file": QUEUE_FILE,
        "source_record_count": len(dispatch_records),
        "record_count": len(dispatch_records),
        "records": dispatch_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        for record in dispatch_records:
            row = [
                str(record[col]) if not isinstance(record[col], bool) else str(record[col]).lower()
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
