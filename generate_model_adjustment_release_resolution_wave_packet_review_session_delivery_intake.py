import json

# Input and output file paths
EXECUTION_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_execution_handoff.json"
ORCHESTRATION_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_handoff.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_intake.md"

MD_COLUMNS = [
    "delivery_intake_id",
    "intake_position",
    "orchestration_handoff_id",
    "execution_handoff_id",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Read orchestration handoff input
    with open(ORCHESTRATION_HANDOFF, "r", encoding="utf-8") as f:
        orch_handoff_data = json.load(f)
    orch_handoff_records = orch_handoff_data["records"]

    # Read execution handoff input
    with open(EXECUTION_HANDOFF, "r", encoding="utf-8") as f:
        exec_handoff_data = json.load(f)
    exec_handoff_records = exec_handoff_data["records"]

    # For this contract, one delivery intake record per orchestration handoff record
    delivery_records = []
    for i, orch_record in enumerate(orch_handoff_records, 1):
        # Find matching execution handoff record (assume 1:1 by position)
        exec_record = exec_handoff_records[i-1] if i-1 < len(exec_handoff_records) else None
        delivery_record = {
            "delivery_intake_id": f"resolution-wave-packet-review-session-delivery-intake-{i:04d}",
            "intake_position": i,
            "orchestration_handoff_id": orch_record["orchestration_handoff_id"],
            "execution_handoff_id": exec_record["execution_handoff_id"] if exec_record else None,
            "lineage_source_layer": "orchestration_handoff",
            "lineage_source_file": ORCHESTRATION_HANDOFF,
            "lineage_source_record_id": orch_record["orchestration_handoff_id"],
        }
        delivery_records.append(delivery_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_delivery_intake",
        "source_files": [EXECUTION_HANDOFF, ORCHESTRATION_HANDOFF],
        "source_record_counts": {
            "execution_handoff": len(exec_handoff_records),
            "orchestration_handoff": len(orch_handoff_records),
        },
        "record_count": len(delivery_records),
        "records": delivery_records,
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
        for rec in delivery_records:
            row = [str(rec[col]) for col in MD_COLUMNS]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
