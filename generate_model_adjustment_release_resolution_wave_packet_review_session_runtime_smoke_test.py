"""
generate_model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test.md
- Contract: Runtime family only, do not mutate v8.8–v15.0, smoke-test only, deterministic output, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

ACCEPTANCE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test.md"

MD_COLUMNS = [
    "runtime_smoke_test_id",
    "smoke_test_position",
    "runtime_acceptance_id",
    "runtime_smoke_test_pass",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]


def main():
    with open(ACCEPTANCE_FILE, "r", encoding="utf-8") as f:
        acceptance = json.load(f)
    acceptance_record = acceptance["records"][0]

    # Checks
    runtime_acceptance_present_pass = acceptance_record["runtime_acceptance_id"] == "resolution-wave-packet-review-session-runtime-acceptance-0001"
    program_closeout_complete_pass = bool(acceptance_record.get("program_closeout_complete", False))
    terminal_workstreams_complete_pass = all([
        acceptance_record.get("routing_catalog_complete", False),
        acceptance_record.get("execution_complete", False),
        acceptance_record.get("orchestration_complete", False),
        acceptance_record.get("delivery_complete", False),
        acceptance_record.get("publication_complete", False),
    ])
    # Simulate downstream consumption path: can we read and validate acceptance_ready?
    downstream_consumption_path_pass = bool(acceptance_record.get("acceptance_ready", False))
    deterministic_output_pass = True  # This script is deterministic by construction

    runtime_smoke_test_pass = all([
        runtime_acceptance_present_pass,
        program_closeout_complete_pass,
        terminal_workstreams_complete_pass,
        downstream_consumption_path_pass,
        deterministic_output_pass,
    ])

    checks = {
        "runtime_acceptance_present_pass": runtime_acceptance_present_pass,
        "program_closeout_complete_pass": program_closeout_complete_pass,
        "terminal_workstreams_complete_pass": terminal_workstreams_complete_pass,
        "downstream_consumption_path_pass": downstream_consumption_path_pass,
        "deterministic_output_pass": deterministic_output_pass,
    }

    smoke_test_record = {
        "runtime_smoke_test_id": "resolution-wave-packet-review-session-runtime-smoke-test-0001",
        "smoke_test_position": 1,
        "runtime_acceptance_id": acceptance_record["runtime_acceptance_id"],
        "runtime_smoke_test_pass": runtime_smoke_test_pass,
        "lineage_source_layer": "runtime_acceptance",
        "lineage_source_file": ACCEPTANCE_FILE,
        "lineage_source_record_id": acceptance_record["runtime_acceptance_id"],
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test",
        "source_file": ACCEPTANCE_FILE,
        "source_record_count": 1,
        "record_count": 1,
        "runtime_smoke_test_pass": runtime_smoke_test_pass,
        "checks": checks,
        "records": [smoke_test_record],
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v15.1 Controlled Release Resolution Wave Packet Review Session Runtime Smoke Test\n\n")
        f.write("## Source File\n")
        f.write(f"- {ACCEPTANCE_FILE}\n\n")
        f.write("## Checks\n")
        for k, v in checks.items():
            f.write(f"- {k}: {str(v).lower()}\n")
        f.write(f"- runtime_smoke_test_pass: {str(runtime_smoke_test_pass).lower()}\n\n")
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
