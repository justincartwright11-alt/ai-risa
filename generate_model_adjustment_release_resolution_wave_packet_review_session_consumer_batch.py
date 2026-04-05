"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.md
- Contract: Consumer family only, do not mutate v8.8–v16.2, one batch record per dispatch, preserve order, deterministic 4-digit IDs, exact-once coverage, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.md"

MD_COLUMNS = [
    "consumer_batch_id",
    "consumer_dispatch_id",
    "batch_position",
    "consumer_batch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    with open(DISPATCH_FILE, "r", encoding="utf-8") as f:
        dispatch = json.load(f)
    dispatch_records = dispatch["records"]

    batch_records = []
    for i, dispatch_record in enumerate(dispatch_records):
        batch_id = f"resolution-wave-packet-review-session-consumer-batch-{i+1:04d}"
        batch_record = {
            "consumer_batch_id": batch_id,
            "consumer_dispatch_id": dispatch_record["consumer_dispatch_id"],
            "batch_position": i+1,
            "consumer_batch_ready": True,
            "lineage_source_layer": "consumer_dispatch",
            "lineage_source_file": DISPATCH_FILE,
            "lineage_source_record_id": dispatch_record["consumer_dispatch_id"],
        }
        batch_records.append(batch_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_batch",
        "source_file": DISPATCH_FILE,
        "source_record_count": len(dispatch_records),
        "record_count": len(batch_records),
        "records": batch_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v16.3 Controlled Release Resolution Wave Packet Review Session Consumer Batch\n\n")
        f.write("## Source File\n")
        f.write(f"- {DISPATCH_FILE}\n\n")
        f.write("## Batch Table\n")
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
