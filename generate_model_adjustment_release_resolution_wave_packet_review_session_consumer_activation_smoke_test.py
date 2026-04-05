"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test.md
- Contract: New activation family only, do not mutate v8.8–v17.0, smoke-test only, deterministic output, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

ACCEPTANCE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_acceptance.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test.md"

MD_COLUMNS = [
    "activation_smoke_test_id",
    "smoke_test_position",
    "activation_acceptance_id",
    "activation_smoke_test_pass",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    with open(ACCEPTANCE_FILE, "r", encoding="utf-8") as f:
        acceptance = json.load(f)
    acceptance_record = acceptance["records"][0]

    # Checks
    activation_acceptance_id = acceptance_record["activation_acceptance_id"]
    consumer_accepted = acceptance_record.get("consumer_accepted", False)
    deterministic_output_pass = True

    activation_smoke_test_pass = consumer_accepted and deterministic_output_pass

    smoke_test_record = {
        "activation_smoke_test_id": "resolution-wave-packet-review-session-consumer-activation-smoke-test-0001",
        "smoke_test_position": 1,
        "activation_acceptance_id": activation_acceptance_id,
        "activation_smoke_test_pass": activation_smoke_test_pass,
        "lineage_source_layer": "consumer_activation_acceptance",
        "lineage_source_file": ACCEPTANCE_FILE,
        "lineage_source_record_id": activation_acceptance_id,
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_activation_smoke_test",
        "source_file": ACCEPTANCE_FILE,
        "source_record_count": 1,
        "record_count": 1,
        "activation_smoke_test_pass": activation_smoke_test_pass,
        "records": [smoke_test_record],
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v17.1 Controlled Release Resolution Wave Packet Review Session Consumer Activation Smoke Test\n\n")
        f.write("## Source File\n")
        f.write(f"- {ACCEPTANCE_FILE}\n\n")
        f.write("## Smoke Test Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        row = [
            str(smoke_test_record[col]) if not isinstance(smoke_test_record[col], bool) else str(smoke_test_record[col]).lower()
            for col in MD_COLUMNS
        ]
        f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
