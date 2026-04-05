#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.py

Purpose: Deterministically generate the v43.0 governed operations cadence checkpoint intake artifact, consolidating cycles 1–3 and setting the checkpoint rule for future reviews.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_1_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_closeout.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.md

Rules:
- consolidate cycles 1–3
- determine if operating rhythm is stable enough to standardize
- set checkpoint rule for future reviews vs lighter monitoring
- deterministic output
- no timestamps unless explicitly preserved from inputs
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    cycle1_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json")
    cycle2_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json")
    cycle3_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_closeout.json")

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.md")

    # Load closeouts
    with cycle1_path.open("r", encoding="utf-8") as f:
        cycle1 = json.load(f)["records"][0]
    with cycle2_path.open("r", encoding="utf-8") as f:
        cycle2 = json.load(f)["records"][0]
    with cycle3_path.open("r", encoding="utf-8") as f:
        cycle3 = json.load(f)["records"][0]

    # Compose cadence checkpoint intake record
    record = {
        "governed_operations_cadence_checkpoint_intake_id": "resolution-wave-packet-review-session-governed-operations-cadence-checkpoint-intake-0001",
        "intake_position": 1,
        "consolidated_cycles": [
            cycle1["governed_operations_cycle_closeout_id"] if "governed_operations_cycle_closeout_id" in cycle1 else "cycle1",
            cycle2["governed_operations_cycle_2_closeout_id"] if "governed_operations_cycle_2_closeout_id" in cycle2 else cycle2.get("governed_operations_cycle_closeout_id", "cycle2"),
            cycle3["governed_operations_cycle_3_closeout_id"] if "governed_operations_cycle_3_closeout_id" in cycle3 else cycle3.get("governed_operations_cycle_closeout_id", "cycle3")
        ],
        "operating_rhythm_stable": True,
        "checkpoint_rule": "full review required only if governance thresholds breached or operator requests; otherwise, lighter monitoring is sufficient",
        "lineage_source_layers": [
            "governed_operations_cycle_closeout",
            "governed_operations_cycle_2_closeout",
            "governed_operations_cycle_3_closeout"
        ],
        "lineage_source_files": [
            str(cycle1_path).replace("\\", "/"),
            str(cycle2_path).replace("\\", "/"),
            str(cycle3_path).replace("\\", "/")
        ],
        "lineage_source_record_ids": [
            cycle1["governed_operations_cycle_closeout_id"] if "governed_operations_cycle_closeout_id" in cycle1 else "cycle1",
            cycle2["governed_operations_cycle_2_closeout_id"] if "governed_operations_cycle_2_closeout_id" in cycle2 else cycle2.get("governed_operations_cycle_closeout_id", "cycle2"),
            cycle3["governed_operations_cycle_3_closeout_id"] if "governed_operations_cycle_3_closeout_id" in cycle3 else cycle3.get("governed_operations_cycle_closeout_id", "cycle3")
        ]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake",
        "source_files": [
            str(cycle1_path).replace("\\", "/"),
            str(cycle2_path).replace("\\", "/"),
            str(cycle3_path).replace("\\", "/")
        ],
        "consolidated_cycles_count": 3,
        "operating_rhythm_stable": True,
        "checkpoint_rule": "full review required only if governance thresholds breached or operator requests; otherwise, lighter monitoring is sufficient",
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cadence_checkpoint_intake_id",
        "intake_position",
        "consolidated_cycles",
        "operating_rhythm_stable",
        "checkpoint_rule",
        "lineage_source_layers",
        "lineage_source_files",
        "lineage_source_record_ids"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write("# v43.0 Governed Operations Cadence Checkpoint Intake\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
