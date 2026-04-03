#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake.py

Purpose: Deterministically generate the v41.0 governed operations cycle 2 review intake artifact from the frozen governed operations cycle 2 closeout.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake.md

Rules:
- governed-operations review family only
- do not reopen or mutate v8.8 through v40.3
- intake only
- must reference all frozen cycle 2 slices
- deterministic output
- no timestamps unless explicitly preserved from closeout
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input path
    closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json")

    # Output paths
    review_intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake.json")
    review_intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake.md")

    # Load closeout
    with closeout_path.open("r", encoding="utf-8") as f:
        closeout = json.load(f)
    closeout_rec = closeout["records"][0]

    # Compose review intake record
    record = {
        "governed_operations_cycle_2_review_intake_id": "resolution-wave-packet-review-session-governed-operations-cycle-2-review-intake-0001",
        "review_position": 1,
        "governed_operations_cycle_2_closeout_id": closeout_rec["governed_operations_cycle_2_closeout_id"],
        "frozen_slices": [
            "v40.0-controlled-release-resolution-wave-packet-review-session-governed-operations-cycle-2-intake",
            "v40.1-controlled-release-resolution-wave-packet-review-session-governed-operations-cycle-2-plan",
            "v40.2-controlled-release-resolution-wave-packet-review-session-governed-operations-cycle-2-execution-evidence",
            "v40.3-controlled-release-resolution-wave-packet-review-session-governed-operations-cycle-2-closeout"
        ],
        "lineage_source_layer": "governed_operations_cycle_2_closeout",
        "lineage_source_file": str(closeout_path).replace("\\", "/"),
        "lineage_source_record_id": closeout_rec["governed_operations_cycle_2_closeout_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake",
        "source_file": str(closeout_path).replace("\\", "/"),
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with review_intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_2_review_intake_id",
        "review_position",
        "governed_operations_cycle_2_closeout_id",
        "frozen_slices",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with review_intake_md_path.open("w", encoding="utf-8") as f:
        f.write("# v41.0 Governed Operations Cycle 2 Review Intake\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
