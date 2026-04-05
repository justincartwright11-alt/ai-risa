"""
generate_model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.py

- Inputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_intake.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_queue.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_dispatch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_batch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_audit.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.md
- Contract: Handoff only, deterministic output, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_intake.json"
QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_queue.json"
DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_dispatch.json"
BATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_batch.json"
AUDIT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_audit.json"

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.md"

FROZEN_SLICES = [
    "v12.0-controlled-release-resolution-wave-packet-review-session-delivery-intake",
    "v12.1-controlled-release-resolution-wave-packet-review-session-delivery-queue",
    "v12.2-controlled-release-resolution-wave-packet-review-session-delivery-dispatch",
    "v12.3-controlled-release-resolution-wave-packet-review-session-delivery-batch",
    "v12.4-controlled-release-resolution-wave-packet-review-session-delivery-audit",
]

MD_COLUMNS = [
    "delivery_handoff_id",
    "handoff_position",
    "terminal_delivery_batch_file",
    "terminal_delivery_audit_file",
    "delivery_chain_complete",
    "delivery_audit_complete",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]


def main():
    # Load audit file to get the first audit record
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)
    audit_record = audit_data["records"][0]

    handoff_record = {
        "delivery_handoff_id": "resolution-wave-packet-review-session-delivery-handoff-0001",
        "handoff_position": 1,
        "terminal_delivery_batch_file": BATCH_FILE,
        "terminal_delivery_audit_file": AUDIT_FILE,
        "delivery_chain_complete": True,
        "delivery_audit_complete": True,
        "lineage_source_layer": "delivery_audit",
        "lineage_source_file": AUDIT_FILE,
        "lineage_source_record_id": audit_record["delivery_audit_id"],
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff",
        "source_files": [INTAKE_FILE, QUEUE_FILE, DISPATCH_FILE, BATCH_FILE, AUDIT_FILE],
        "frozen_slices": FROZEN_SLICES,
        "delivery_chain_complete": True,
        "delivery_audit_complete": True,
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
        f.write("# v12.5 Controlled Release Resolution Wave Packet Review Session Delivery Handoff\n\n")
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n## Frozen Slices\n")
        for s in output["frozen_slices"]:
            f.write(f"- {s}\n")
        f.write("\n## Status Flags\n")
        f.write(f"- delivery_chain_complete: {str(output['delivery_chain_complete']).lower()}\n")
        f.write(f"- delivery_audit_complete: {str(output['delivery_audit_complete']).lower()}\n")
        f.write(f"- merge_performed: {str(output['merge_performed']).lower()}\n")
        f.write(f"- tag_performed: {str(output['tag_performed']).lower()}\n")
        f.write(f"- push_performed: {str(output['push_performed']).lower()}\n")
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
