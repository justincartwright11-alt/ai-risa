import json

# Input and output file paths
INPUT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_execution_handoff.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_intake.md"

MD_COLUMNS = [
    "orchestration_intake_id",
    "intake_position",
    "execution_handoff_id",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Read execution handoff input
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        handoff_data = json.load(f)
    handoff_records = handoff_data["records"]

    orchestration_records = []
    for i, handoff_record in enumerate(handoff_records, 1):
        orchestration_record = {
            "orchestration_intake_id": f"resolution-wave-packet-review-session-orchestration-intake-{i:04d}",
            "intake_position": i,
            "execution_handoff_id": handoff_record["execution_handoff_id"],
            "lineage_source_layer": "execution_handoff",
            "lineage_source_file": INPUT_FILE,
            "lineage_source_record_id": handoff_record["execution_handoff_id"],
        }
        orchestration_records.append(orchestration_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_orchestration_intake",
        "source_file": INPUT_FILE,
        "source_record_count": len(handoff_records),
        "record_count": len(orchestration_records),
        "records": orchestration_records,
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
        for rec in orchestration_records:
            row = [str(rec[col]) for col in MD_COLUMNS]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
