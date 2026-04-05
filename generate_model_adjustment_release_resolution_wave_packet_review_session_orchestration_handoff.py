import json

# Input file paths
INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_intake.json"
QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_queue.json"
DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_dispatch.json"
BATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_batch.json"
AUDIT_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_audit.json"

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_handoff.md"

FROZEN_SLICES = [
    "v11.0-controlled-release-resolution-wave-packet-review-session-orchestration-intake",
    "v11.1-controlled-release-resolution-wave-packet-review-session-orchestration-queue",
    "v11.2-controlled-release-resolution-wave-packet-review-session-orchestration-dispatch",
    "v11.3-controlled-release-resolution-wave-packet-review-session-orchestration-batch",
    "v11.4-controlled-release-resolution-wave-packet-review-session-orchestration-audit",
]

MD_COLUMNS = [
    "orchestration_handoff_id",
    "handoff_position",
    "terminal_orchestration_batch_file",
    "terminal_orchestration_audit_file",
    "orchestration_chain_complete",
    "orchestration_audit_complete",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    # Load audit file to get the first audit record
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)
    audit_record = audit_data["records"][0] if audit_data["records"] else None

    handoff_record = {
        "orchestration_handoff_id": "resolution-wave-packet-review-session-orchestration-handoff-0001",
        "handoff_position": 1,
        "terminal_orchestration_batch_file": BATCH_FILE,
        "terminal_orchestration_audit_file": AUDIT_FILE,
        "orchestration_chain_complete": True,
        "orchestration_audit_complete": True,
        "lineage_source_layer": "orchestration_audit",
        "lineage_source_file": AUDIT_FILE,
        "lineage_source_record_id": audit_record["orchestration_audit_id"] if audit_record else None,
    }

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_orchestration_handoff",
        "source_files": [INTAKE_FILE, QUEUE_FILE, DISPATCH_FILE, BATCH_FILE, AUDIT_FILE],
        "frozen_slices": FROZEN_SLICES,
        "orchestration_chain_complete": True,
        "orchestration_audit_complete": True,
        "merge_performed": False,
        "tag_performed": False,
        "push_performed": False,
        "record_count": 1,
        "records": [handoff_record],
    }

    # Write JSON output
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Write Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        # Title
        f.write("# Model Adjustment Release Resolution Wave Packet Review Session Orchestration Handoff\n\n")
        # Source files
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n")
        # Frozen slices
        f.write("## Frozen Slices\n")
        for s in output["frozen_slices"]:
            f.write(f"- {s}\n")
        f.write("\n")
        # Status flags
        f.write("## Status Flags\n")
        f.write(f"- orchestration_chain_complete: {str(output['orchestration_chain_complete']).lower()}\n")
        f.write(f"- orchestration_audit_complete: {str(output['orchestration_audit_complete']).lower()}\n")
        f.write(f"- merge_performed: {str(output['merge_performed']).lower()}\n")
        f.write(f"- tag_performed: {str(output['tag_performed']).lower()}\n")
        f.write(f"- push_performed: {str(output['push_performed']).lower()}\n\n")
        # Handoff table
        f.write("## Handoff Record\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        rec = handoff_record
        row = [
            str(rec[col]) if not isinstance(rec[col], bool) else ("true" if rec[col] else "false")
            for col in MD_COLUMNS
        ]
        f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
