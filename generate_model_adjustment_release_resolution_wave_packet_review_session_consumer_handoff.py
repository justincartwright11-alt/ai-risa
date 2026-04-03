"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff.py

- Inputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_audit.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff.md
- Contract: Consumer family only, do not mutate v8.8–v16.4, handoff only, deterministic output, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json"
QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json"
DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json"
BATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json"
AUDIT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_audit.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff.md"

MD_COLUMNS = [
    "consumer_handoff_id",
    "handoff_position",
    "terminal_consumer_batch_file",
    "terminal_consumer_audit_file",
    "consumer_chain_complete",
    "consumer_audit_complete",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Only one record in each file for this disciplined chain
    handoff_record = {
        "consumer_handoff_id": "resolution-wave-packet-review-session-consumer-handoff-0001",
        "handoff_position": 1,
        "terminal_consumer_batch_file": BATCH_FILE,
        "terminal_consumer_audit_file": AUDIT_FILE,
        "consumer_chain_complete": True,
        "consumer_audit_complete": True,
        "lineage_source_layer": "consumer_audit",
        "lineage_source_file": AUDIT_FILE,
        "lineage_source_record_id": "resolution-wave-packet-review-session-consumer-audit-0001",
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_handoff",
        "source_files": [
            INTAKE_FILE, QUEUE_FILE, DISPATCH_FILE, BATCH_FILE, AUDIT_FILE
        ],
        "frozen_slices": [
            "v16.0-controlled-release-resolution-wave-packet-review-session-consumer-intake",
            "v16.1-controlled-release-resolution-wave-packet-review-session-consumer-queue",
            "v16.2-controlled-release-resolution-wave-packet-review-session-consumer-dispatch",
            "v16.3-controlled-release-resolution-wave-packet-review-session-consumer-batch",
            "v16.4-controlled-release-resolution-wave-packet-review-session-consumer-audit"
        ],
        "consumer_chain_complete": True,
        "consumer_audit_complete": True,
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
        f.write("# v16.5 Controlled Release Resolution Wave Packet Review Session Consumer Handoff\n\n")
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n## Frozen Slices\n")
        for s in output["frozen_slices"]:
            f.write(f"- {s}\n")
        f.write("\n## Status Flags\n")
        for flag in [
            "consumer_chain_complete",
            "consumer_audit_complete",
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
