"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.md
- Contract: New external-consumer family, do not mutate v8.8–v15.2, deterministic ordering, one intake per handoff, stable lineage, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

HANDOFF_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.md"

MD_COLUMNS = [
    "consumer_intake_id",
    "intake_position",
    "source_runtime_handoff_id",
    "terminal_runtime_handoff_file",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    with open(HANDOFF_FILE, "r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_record = handoff["records"][0]

    consumer_intake_record = {
        "consumer_intake_id": "resolution-wave-packet-review-session-consumer-intake-0001",
        "intake_position": 1,
        "source_runtime_handoff_id": handoff_record["runtime_handoff_id"],
        "terminal_runtime_handoff_file": HANDOFF_FILE,
        "lineage_source_layer": "runtime_handoff",
        "lineage_source_file": HANDOFF_FILE,
        "lineage_source_record_id": handoff_record["runtime_handoff_id"],
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_intake",
        "source_file": HANDOFF_FILE,
        "source_record_count": 1,
        "record_count": 1,
        "records": [consumer_intake_record],
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v16.0 Controlled Release Resolution Wave Packet Review Session Consumer Intake\n\n")
        f.write("## Source File\n")
        f.write(f"- {HANDOFF_FILE}\n\n")
        f.write("## Intake Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        row = [
            str(consumer_intake_record[col]) if not isinstance(consumer_intake_record[col], bool) else str(consumer_intake_record[col]).lower()
            for col in MD_COLUMNS
        ]
        f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
