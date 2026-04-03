import json

# Input and output file paths
INPUT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_intake.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_queue.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_queue.md"

MD_COLUMNS = [
    "delivery_queue_id",
    "delivery_intake_id",
    "queue_position",
    "delivery_ready",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Read delivery intake input
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        intake_data = json.load(f)
    intake_records = intake_data["records"]

    queue_records = []
    for i, intake_record in enumerate(intake_records, 1):
        queue_record = {
            "delivery_queue_id": f"resolution-wave-packet-review-session-delivery-queue-{i:04d}",
            "delivery_intake_id": intake_record["delivery_intake_id"],
            "queue_position": i,
            "delivery_ready": True,
            "lineage_source_layer": "delivery_intake",
            "lineage_source_file": INPUT_FILE,
            "lineage_source_record_id": intake_record["delivery_intake_id"],
        }
        queue_records.append(queue_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_delivery_queue",
        "source_file": INPUT_FILE,
        "source_record_count": len(queue_records),
        "record_count": len(queue_records),
        "records": queue_records,
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
        for rec in queue_records:
            row = [
                str(rec[col]) if not isinstance(rec[col], bool) else ("true" if rec[col] else "false")
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
