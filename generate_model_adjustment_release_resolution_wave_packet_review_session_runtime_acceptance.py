"""
generate_model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.md
- Contract: New family, no mutation of v8.8–v14.0, validate terminal completeness, deterministic output, no timestamps/merge/tag/push.
"""
import json
import os

CLOSEOUT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance.md"

MD_COLUMNS = [
    "runtime_acceptance_id",
    "acceptance_position",
    "program_closeout_file",
    "routing_catalog_complete",
    "execution_complete",
    "orchestration_complete",
    "delivery_complete",
    "publication_complete",
    "program_closeout_complete",
    "acceptance_ready",
]


def main():
    with open(CLOSEOUT_FILE, "r", encoding="utf-8") as f:
        closeout = json.load(f)
    record = closeout["records"][0]

    # Validate terminal completeness
    routing_catalog_complete = bool(record.get("routing_catalog_complete", False))
    execution_complete = bool(record.get("execution_complete", False))
    orchestration_complete = bool(record.get("orchestration_complete", False))
    delivery_complete = bool(record.get("delivery_complete", False))
    publication_complete = bool(record.get("publication_complete", False))
    program_closeout_complete = True  # This artifact exists
    acceptance_ready = all([
        routing_catalog_complete,
        execution_complete,
        orchestration_complete,
        delivery_complete,
        publication_complete,
        program_closeout_complete,
    ])

    acceptance_record = {
        "runtime_acceptance_id": "resolution-wave-packet-review-session-runtime-acceptance-0001",
        "acceptance_position": 1,
        "program_closeout_file": CLOSEOUT_FILE,
        "routing_catalog_complete": routing_catalog_complete,
        "execution_complete": execution_complete,
        "orchestration_complete": orchestration_complete,
        "delivery_complete": delivery_complete,
        "publication_complete": publication_complete,
        "program_closeout_complete": program_closeout_complete,
        "acceptance_ready": acceptance_ready,
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_runtime_acceptance",
        "source_file": CLOSEOUT_FILE,
        "record_count": 1,
        "records": [acceptance_record],
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v15.0 Controlled Release Resolution Wave Packet Review Session Runtime Acceptance\n\n")
        f.write("## Source File\n")
        f.write(f"- {CLOSEOUT_FILE}\n\n")
        f.write("## Acceptance Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        row = [
            str(acceptance_record[col]) if not isinstance(acceptance_record[col], bool) else str(acceptance_record[col]).lower()
            for col in MD_COLUMNS
        ]
        f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
