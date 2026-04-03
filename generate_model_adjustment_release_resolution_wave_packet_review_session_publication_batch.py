"""
generate_model_adjustment_release_resolution_wave_packet_review_session_publication_batch.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_batch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_batch.md
- Contract: Publication workstream only, do not mutate v8.8–v13.2, one batch record per dispatch record, preserve source order, deterministic 4-digit IDs, exact-once coverage, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_batch.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_batch.md"

BATCH_ID_PREFIX = "resolution-wave-packet-review-session-publication-batch-"

MD_COLUMNS = [
    "publication_batch_id",
    "publication_dispatch_id",
    "batch_position",
    "batch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]


def main():
    with open(DISPATCH_FILE, "r", encoding="utf-8") as f:
        dispatch_data = json.load(f)
    dispatch_records = dispatch_data["records"]

    batch_records = []
    for i, dispatch_record in enumerate(dispatch_records, 1):
        batch_record = {
            "publication_batch_id": f"{BATCH_ID_PREFIX}{i:04d}",
            "publication_dispatch_id": dispatch_record["publication_dispatch_id"],
            "batch_position": i,
            "batch_ready": True,
            "lineage_source_layer": "publication_dispatch",
            "lineage_source_file": DISPATCH_FILE,
            "lineage_source_record_id": dispatch_record["publication_dispatch_id"],
        }
        batch_records.append(batch_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_publication_batch",
        "source_file": DISPATCH_FILE,
        "source_record_count": len(batch_records),
        "record_count": len(batch_records),
        "records": batch_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        for record in batch_records:
            row = [
                str(record[col]) if not isinstance(record[col], bool) else str(record[col]).lower()
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
