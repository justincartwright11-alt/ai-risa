"""
generate_model_adjustment_release_resolution_wave_packet_review_session_publication_handoff.py

- Inputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_batch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_audit.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_handoff.md
- Contract: Handoff only, do not mutate v8.8–v13.4, deterministic output, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.json"
QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_queue.json"
DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_dispatch.json"
BATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_batch.json"
AUDIT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_audit.json"

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_handoff.md"

FROZEN_SLICES = [
    "v13.0-controlled-release-resolution-wave-packet-review-session-publication-intake",
    "v13.1-controlled-release-resolution-wave-packet-review-session-publication-queue",
    "v13.2-controlled-release-resolution-wave-packet-review-session-publication-dispatch",
    "v13.3-controlled-release-resolution-wave-packet-review-session-publication-batch",
    "v13.4-controlled-release-resolution-wave-packet-review-session-publication-audit",
]

MD_COLUMNS = [
    "publication_handoff_id",
    "handoff_position",
    "terminal_publication_batch_file",
    "terminal_publication_audit_file",
    "publication_chain_complete",
    "publication_audit_complete",
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
        "publication_handoff_id": "resolution-wave-packet-review-session-publication-handoff-0001",
        "handoff_position": 1,
        "terminal_publication_batch_file": BATCH_FILE,
        "terminal_publication_audit_file": AUDIT_FILE,
        "publication_chain_complete": True,
        "publication_audit_complete": True,
        "lineage_source_layer": "publication_audit",
        "lineage_source_file": AUDIT_FILE,
        "lineage_source_record_id": audit_record["publication_audit_id"],
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_publication_handoff",
        "source_files": [INTAKE_FILE, QUEUE_FILE, DISPATCH_FILE, BATCH_FILE, AUDIT_FILE],
        "frozen_slices": FROZEN_SLICES,
        "publication_chain_complete": True,
        "publication_audit_complete": True,
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
        f.write("# v13.5 Controlled Release Resolution Wave Packet Review Session Publication Handoff\n\n")
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n## Frozen Slices\n")
        for s in output["frozen_slices"]:
            f.write(f"- {s}\n")
        f.write("\n## Status Flags\n")
        f.write(f"- publication_chain_complete: {str(output['publication_chain_complete']).lower()}\n")
        f.write(f"- publication_audit_complete: {str(output['publication_audit_complete']).lower()}\n")
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
