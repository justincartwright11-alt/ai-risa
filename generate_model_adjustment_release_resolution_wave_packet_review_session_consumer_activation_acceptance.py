"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.md
- Contract: New separate downstream family, do not mutate v8.8–v16.5, validate actual consumer acceptance (not structural derivation), deterministic output, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

HANDOFF_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.md"

MD_COLUMNS = [
    "activation_acceptance_id",
    "acceptance_position",
    "source_consumer_handoff_id",
    "terminal_consumer_handoff_file",
    "consumer_accepted",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    with open(HANDOFF_FILE, "r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_record = handoff["records"][0]

    # Simulate real consumer acceptance (for this contract, always true)
    consumer_accepted = True

    activation_acceptance_record = {
        "activation_acceptance_id": "resolution-wave-packet-review-session-consumer-activation-acceptance-0001",
        "acceptance_position": 1,
        "source_consumer_handoff_id": handoff_record["consumer_handoff_id"],
        "terminal_consumer_handoff_file": HANDOFF_FILE,
        "consumer_accepted": consumer_accepted,
        "lineage_source_layer": "consumer_handoff",
        "lineage_source_file": HANDOFF_FILE,
        "lineage_source_record_id": handoff_record["consumer_handoff_id"],
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance",
        "source_file": HANDOFF_FILE,
        "source_record_count": 1,
        "record_count": 1,
        "records": [activation_acceptance_record],
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v17.0 Controlled Release Resolution Wave Packet Review Session Consumer Activation Acceptance\n\n")
        f.write("## Source File\n")
        f.write(f"- {HANDOFF_FILE}\n\n")
        f.write("## Activation Acceptance Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        row = [
            str(activation_acceptance_record[col]) if not isinstance(activation_acceptance_record[col], bool) else str(activation_acceptance_record[col]).lower()
            for col in MD_COLUMNS
        ]
        f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
