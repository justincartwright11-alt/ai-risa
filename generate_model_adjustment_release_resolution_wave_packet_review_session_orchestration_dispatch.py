import json

# Input and output file paths
INPUT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_queue.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_dispatch.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_dispatch.md"

MD_COLUMNS = [
    "orchestration_dispatch_id",
    "orchestration_queue_id",
    "dispatch_position",
    "dispatch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Read orchestration queue input
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        queue_data = json.load(f)
    queue_records = queue_data["records"]

    dispatch_records = []
    for i, queue_record in enumerate(queue_records, 1):
        dispatch_record = {
            "orchestration_dispatch_id": f"resolution-wave-packet-review-session-orchestration-dispatch-{i:04d}",
            "orchestration_queue_id": queue_record["orchestration_queue_id"],
            "dispatch_position": i,
            "dispatch_ready": queue_record["orchestration_ready"],
            "lineage_source_layer": "orchestration_queue",
            "lineage_source_file": INPUT_FILE,
            "lineage_source_record_id": queue_record["orchestration_queue_id"],
        }
        dispatch_records.append(dispatch_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_orchestration_dispatch",
        "source_file": INPUT_FILE,
        "source_record_count": len(dispatch_records),
        "record_count": len(dispatch_records),
        "records": dispatch_records,
    }

    # Write JSON output
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Write Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        # Header
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        # Rows
        for rec in dispatch_records:
            row = [
                str(rec[col]) if not isinstance(rec[col], bool) else ("true" if rec[col] else "false")
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
