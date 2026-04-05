#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.py

Purpose: Deterministically generate the v39.0 governed operations review intake artifact from the frozen governed operations cycle closeout, governance handoff, and operator-provided review targets.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json
- operator-provided review targets (operator_governed_operations_review_targets.json)

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.md

Rules:
- review family only
- do not reopen or mutate v8.8 through v38.3
- deterministic output
- no timestamps unless explicitly provided
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json")
    handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")
    review_targets_path = Path("operator_governed_operations_review_targets.json")

    # Output paths
    review_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.json")
    review_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.md")

    # Load inputs
    with closeout_path.open("r", encoding="utf-8") as f:
        closeout = json.load(f)
    closeout_rec = closeout["records"][0]
    with handoff_path.open("r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_rec = handoff["records"][0]
    with review_targets_path.open("r", encoding="utf-8") as f:
        review_targets = json.load(f)

    # Compose review intake record
    record = {
        "governed_operations_review_intake_id": "resolution-wave-packet-review-session-governed-operations-review-intake-0001",
        "governed_operations_cycle_closeout_id": closeout_rec["governed_operations_cycle_closeout_id"],
        "governance_handoff_reference": handoff_rec["operations_governance_handoff_id"],
        "review_position": 1,
        "review_targets": review_targets["review_targets"],
        "governance_thresholds": handoff_rec["governance_thresholds"],
        "alert_escalation_rules": handoff_rec["alert_escalation_rules"],
        "review_cadence": handoff_rec["review_cadence"],
        "operator_intervention_rules": handoff_rec["operator_intervention_rules"],
        "rollback_trigger_rules": handoff_rec["rollback_trigger_rules"],
        "approval_requirements": handoff_rec["approval_requirements"],
        "lineage_source_layer": "governed_operations_cycle_closeout",
        "lineage_source_file": str(closeout_path).replace("\\", "/"),
        "lineage_source_record_id": closeout_rec["governed_operations_cycle_closeout_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake",
        "source_files": [
            str(closeout_path).replace("\\", "/"),
            str(handoff_path).replace("\\", "/"),
            str(review_targets_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with review_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_review_intake_id",
        "governed_operations_cycle_closeout_id",
        "governance_handoff_reference",
        "review_position",
        "review_targets",
        "governance_thresholds",
        "alert_escalation_rules",
        "review_cadence",
        "operator_intervention_rules",
        "rollback_trigger_rules",
        "approval_requirements",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with review_md_path.open("w", encoding="utf-8") as f:
        f.write("# v39.0 Governed Operations Review Intake\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
