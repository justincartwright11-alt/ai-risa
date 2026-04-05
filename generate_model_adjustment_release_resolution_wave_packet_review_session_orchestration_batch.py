import json

# Input and output file paths
INPUT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_dispatch.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_batch.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_batch.md"

MD_COLUMNS = [
    "orchestration_batch_id",
    "orchestration_dispatch_id",
    "batch_position",
    "batch_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Read orchestration dispatch input
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dispatch_data = json.load(f)
    dispatch_records = dispatch_data["records"]

    batch_records = []
    for i, dispatch_record in enumerate(dispatch_records, 1):
        batch_record = {
            "orchestration_batch_id": f"resolution-wave-packet-review-session-orchestration-batch-{i:04d}",
            "orchestration_dispatch_id": dispatch_record["orchestration_dispatch_id"],
            "batch_position": i,
            "batch_ready": dispatch_record["dispatch_ready"],
            "lineage_source_layer": "orchestration_dispatch",
            "lineage_source_file": INPUT_FILE,
            "lineage_source_record_id": dispatch_record["orchestration_dispatch_id"],
        }
        batch_records.append(batch_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_orchestration_batch",
        "source_file": INPUT_FILE,
        "source_record_count": len(batch_records),
        "record_count": len(batch_records),
        "records": batch_records,
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
        for rec in batch_records:
            row = [
                str(rec[col]) if not isinstance(rec[col], bool) else ("true" if rec[col] else "false")
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
