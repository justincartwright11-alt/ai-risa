"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_handoff.py

- Inputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_handoff.md
- Contract: Activation family only, do not mutate v8.8–v17.1, handoff only, deterministic output, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

ACCEPTANCE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.json"
SMOKE_TEST_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_handoff.md"

MD_COLUMNS = [
    "activation_handoff_id",
    "handoff_position",
    "terminal_activation_acceptance_file",
    "terminal_activation_smoke_test_file",
    "activation_family_complete",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Only one record in each file for this disciplined chain
    handoff_record = {
        "activation_handoff_id": "resolution-wave-packet-review-session-consumer-activation-handoff-0001",
        "handoff_position": 1,
        "terminal_activation_acceptance_file": ACCEPTANCE_FILE,
        "terminal_activation_smoke_test_file": SMOKE_TEST_FILE,
        "activation_family_complete": True,
        "lineage_source_layer": "consumer_activation_smoke_test",
        "lineage_source_file": SMOKE_TEST_FILE,
        "lineage_source_record_id": "resolution-wave-packet-review-session-consumer-activation-smoke-test-0001",
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_handoff",
        "source_files": [ACCEPTANCE_FILE, SMOKE_TEST_FILE],
        "activation_family_complete": True,
        "merge_performed": False,
        "tag_performed": False,
        "push_performed": False,
        "record_count": 1,
        "records": [handoff_record],
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v17.2 Controlled Release Resolution Wave Packet Review Session Consumer Activation Handoff\n\n")
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n## Status Flags\n")
        for flag in [
            "activation_family_complete",
            "merge_performed",
            "tag_performed",
            "push_performed"
        ]:
            f.write(f"- {flag}: {str(output[flag]).lower()}\n")
        f.write("\n## Handoff Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        row = [
            str(handoff_record[col]) if not isinstance(handoff_record[col], bool) else str(handoff_record[col]).lower()
            for col in MD_COLUMNS
        ]
        f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
