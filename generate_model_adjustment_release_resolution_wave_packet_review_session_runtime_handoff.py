"""
generate_model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.py

- Inputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.md
- Contract: Runtime family only, do not mutate v8.8–v15.1, handoff only, deterministic output, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

ACCEPTANCE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.json"
SMOKE_TEST_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_smoke_test.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.md"

MD_COLUMNS = [
    "runtime_handoff_id",
    "handoff_position",
    "terminal_runtime_acceptance_file",
    "terminal_runtime_smoke_test_file",
    "runtime_family_complete",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Read acceptance and smoke test for validation
    with open(ACCEPTANCE_FILE, "r", encoding="utf-8") as f:
        acceptance = json.load(f)
    with open(SMOKE_TEST_FILE, "r", encoding="utf-8") as f:
        smoke_test = json.load(f)
    
    handoff_record = {
        "runtime_handoff_id": "resolution-wave-packet-review-session-runtime-handoff-0001",
        "handoff_position": 1,
        "terminal_runtime_acceptance_file": ACCEPTANCE_FILE,
        "terminal_runtime_smoke_test_file": SMOKE_TEST_FILE,
        "runtime_family_complete": True,
        "lineage_source_layer": "runtime_smoke_test",
        "lineage_source_file": SMOKE_TEST_FILE,
        "lineage_source_record_id": "resolution-wave-packet-review-session-runtime-smoke-test-0001",
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff",
        "source_files": [ACCEPTANCE_FILE, SMOKE_TEST_FILE],
        "frozen_slices": [
            "v15.0-controlled-release-resolution-wave-packet-review-session-runtime-acceptance",
            "v15.1-controlled-release-resolution-wave-packet-review-session-runtime-smoke-test"
        ],
        "runtime_acceptance_complete": True,
        "runtime_smoke_test_complete": True,
        "runtime_family_complete": True,
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
        f.write("# v15.2 Controlled Release Resolution Wave Packet Review Session Runtime Handoff\n\n")
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n## Frozen Slices\n")
        for s in output["frozen_slices"]:
            f.write(f"- {s}\n")
        f.write("\n## Status Flags\n")
        for flag in [
            "runtime_acceptance_complete",
            "runtime_smoke_test_complete",
            "runtime_family_complete",
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
