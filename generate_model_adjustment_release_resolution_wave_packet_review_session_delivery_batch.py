"""
generate_model_adjustment_release_resolution_wave_packet_review_session_delivery_batch.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_dispatch.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_batch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_batch.md
- Contract: One batch record per dispatch record, deterministic 4-digit IDs, exact-once coverage, source order preserved, no timestamps/policy/release logic.
"""
import json
import os

INPUT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_dispatch.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_batch.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_batch.md"

BATCH_ID_PREFIX = "resolution-wave-packet-review-session-delivery-batch-"

MD_COLUMNS = [
    "delivery_batch_id",
    "delivery_dispatch_id",
    "batch_position",
    "batch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dispatch_data = json.load(f)
    dispatch_records = dispatch_data["records"]

    batch_records = []
    for i, dispatch_record in enumerate(dispatch_records, 1):
        batch_record = {
            "delivery_batch_id": f"{BATCH_ID_PREFIX}{i:04d}",
            "delivery_dispatch_id": dispatch_record["delivery_dispatch_id"],
            "batch_position": i,
            "batch_ready": dispatch_record["dispatch_ready"],
            "lineage_source_layer": "delivery_dispatch",
            "lineage_source_file": INPUT_FILE,
            "lineage_source_record_id": dispatch_record["delivery_dispatch_id"],
        }
        batch_records.append(batch_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_delivery_batch",
        "source_file": INPUT_FILE,
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
