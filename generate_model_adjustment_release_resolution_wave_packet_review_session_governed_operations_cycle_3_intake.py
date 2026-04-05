#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake.py

Purpose: Deterministically generate the v42.0 governed operations cycle 3 intake artifact from the frozen governed operations cycle 2 review handoff.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake.md

Rules:
- governed-operations family only
- do not reopen or mutate v8.8 through v41.2
- intake only
- must reference all frozen cycle 2 review slices
- deterministic output
- no timestamps unless explicitly preserved from review handoff
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input path
    handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_handoff.json")

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake.md")

    # Load handoff
    with handoff_path.open("r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_rec = handoff["records"][0]

    # Compose intake record
    record = {
        "governed_operations_cycle_3_intake_id": "resolution-wave-packet-review-session-governed-operations-cycle-3-intake-0001",
        "intake_position": 1,
        "governed_operations_cycle_2_review_handoff_id": handoff_rec["governed_operations_cycle_2_review_handoff_id"],
        "frozen_slices": handoff["frozen_slices"],
        "recommended_disposition": handoff_rec["recommended_disposition"],
        "lineage_source_layer": "governed_operations_cycle_2_review_handoff",
        "lineage_source_file": str(handoff_path).replace("\\", "/"),
        "lineage_source_record_id": handoff_rec["governed_operations_cycle_2_review_handoff_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake",
        "source_file": str(handoff_path).replace("\\", "/"),
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_3_intake_id",
        "intake_position",
        "governed_operations_cycle_2_review_handoff_id",
        "frozen_slices",
        "recommended_disposition",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write("# v42.0 Governed Operations Cycle 3 Intake\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
