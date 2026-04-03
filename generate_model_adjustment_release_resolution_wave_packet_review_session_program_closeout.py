"""
generate_model_adjustment_release_resolution_wave_packet_review_session_program_closeout.py

- Inputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_closeout.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_execution_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_handoff.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.md
- Contract: Top-level closeout only, do not mutate v8.8–v13.5, deterministic output, record all terminal workstreams as complete, explicitly record completion flags, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

ROUTING_CLOSEOUT = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_closeout.json"
EXECUTION_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_execution_handoff.json"
ORCH_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_handoff.json"
DELIVERY_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.json"
PUBLICATION_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_handoff.json"

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.md"

MD_COLUMNS = [
    "program_closeout_id",
    "closeout_position",
    "routing_catalog_closeout_file",
    "execution_handoff_file",
    "orchestration_handoff_file",
    "delivery_handoff_file",
    "publication_handoff_file",
    "routing_catalog_complete",
    "execution_complete",
    "orchestration_complete",
    "delivery_complete",
    "publication_complete",
    "merge_performed",
    "tag_performed",
    "push_performed",
]


def main():
    program_closeout_id = "resolution-wave-packet-review-session-program-closeout-0001"
    closeout_record = {
        "program_closeout_id": program_closeout_id,
        "closeout_position": 1,
        "routing_catalog_closeout_file": ROUTING_CLOSEOUT,
        "execution_handoff_file": EXECUTION_HANDOFF,
        "orchestration_handoff_file": ORCH_HANDOFF,
        "delivery_handoff_file": DELIVERY_HANDOFF,
        "publication_handoff_file": PUBLICATION_HANDOFF,
        "routing_catalog_complete": True,
        "execution_complete": True,
        "orchestration_complete": True,
        "delivery_complete": True,
        "publication_complete": True,
        "merge_performed": False,
        "tag_performed": False,
        "push_performed": False,
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_program_closeout",
        "source_files": [
            ROUTING_CLOSEOUT,
            EXECUTION_HANDOFF,
            ORCH_HANDOFF,
            DELIVERY_HANDOFF,
            PUBLICATION_HANDOFF,
        ],
        "record_count": 1,
        "routing_catalog_complete": True,
        "execution_complete": True,
        "orchestration_complete": True,
        "delivery_complete": True,
        "publication_complete": True,
        "merge_performed": False,
        "tag_performed": False,
        "push_performed": False,
        "records": [closeout_record],
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v14.0 Controlled Release Resolution Wave Packet Review Session Program Closeout\n\n")
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n## Status Flags\n")
        f.write(f"- routing_catalog_complete: {str(output['routing_catalog_complete']).lower()}\n")
        f.write(f"- execution_complete: {str(output['execution_complete']).lower()}\n")
        f.write(f"- orchestration_complete: {str(output['orchestration_complete']).lower()}\n")
        f.write(f"- delivery_complete: {str(output['delivery_complete']).lower()}\n")
        f.write(f"- publication_complete: {str(output['publication_complete']).lower()}\n")
        f.write(f"- merge_performed: {str(output['merge_performed']).lower()}\n")
        f.write(f"- tag_performed: {str(output['tag_performed']).lower()}\n")
        f.write(f"- push_performed: {str(output['push_performed']).lower()}\n")
        f.write("\n## Program Closeout Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        row = [
            str(closeout_record[col]) if not isinstance(closeout_record[col], bool) else str(closeout_record[col]).lower()
            for col in MD_COLUMNS
        ]
        f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
