"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.md
- Contract: Consumer family only, do not mutate v8.8–v16.1, one dispatch record per queue, preserve order, deterministic 4-digit IDs, exact-once coverage, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.md"

MD_COLUMNS = [
    "consumer_dispatch_id",
    "consumer_queue_id",
    "dispatch_position",
    "consumer_dispatch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = json.load(f)
    queue_records = queue["records"]

    dispatch_records = []
    for i, queue_record in enumerate(queue_records):
        dispatch_id = f"resolution-wave-packet-review-session-consumer-dispatch-{i+1:04d}"
        dispatch_record = {
            "consumer_dispatch_id": dispatch_id,
            "consumer_queue_id": queue_record["consumer_queue_id"],
            "dispatch_position": i+1,
            "consumer_dispatch_ready": True,
            "lineage_source_layer": "consumer_queue",
            "lineage_source_file": QUEUE_FILE,
            "lineage_source_record_id": queue_record["consumer_queue_id"],
        }
        dispatch_records.append(dispatch_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch",
        "source_file": QUEUE_FILE,
        "source_record_count": len(queue_records),
        "record_count": len(dispatch_records),
        "records": dispatch_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v16.2 Controlled Release Resolution Wave Packet Review Session Consumer Dispatch\n\n")
        f.write("## Source File\n")
        f.write(f"- {QUEUE_FILE}\n\n")
        f.write("## Dispatch Table\n")
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
