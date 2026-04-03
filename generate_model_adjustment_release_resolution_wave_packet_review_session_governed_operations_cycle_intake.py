#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_intake.py

Purpose: Deterministically generate the v38.0 governed operations cycle intake artifact from the sealed governance handoff, scaled operations closeout, and operator-provided request.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_closeout.json
- operator-provided governed operations request payload

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_intake.md

Rules:
- new operational family only
- do not reopen or mutate v8.8 through v37.2
- must inherit governance thresholds, escalation rules, review cadence, intervention rules, rollback triggers, and approval requirements
- deterministic output
- no timestamps unless explicitly provided in the request payload
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")
    scaled_closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_closeout.json")
    request_path = Path("operator_governed_operations_request.json")  # Must be provided

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_intake.md")

    # Load inputs
    with handoff_path.open("r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_rec = handoff["records"][0]
    with scaled_closeout_path.open("r", encoding="utf-8") as f:
        scaled_closeout = json.load(f)
    with request_path.open("r", encoding="utf-8") as f:
        request = json.load(f)

    # Compose intake record (fields and values for governed operations cycle)
    record = {
        "governed_operations_cycle_intake_id": "resolution-wave-packet-review-session-governed-operations-cycle-intake-0001",
        "governance_handoff_reference": handoff_rec["operations_governance_handoff_id"],
        "scaled_operations_closeout_reference": scaled_closeout["scaled_operations_closeout_id"],
        "intake_position": 1,
        "governed_operations_request": request["governed_operations_request"],
        "governance_thresholds": handoff_rec["governance_thresholds"],
        "alert_escalation_rules": handoff_rec["alert_escalation_rules"],
        "review_cadence": handoff_rec["review_cadence"],
        "operator_intervention_rules": handoff_rec["operator_intervention_rules"],
        "rollback_trigger_rules": handoff_rec["rollback_trigger_rules"],
        "approval_requirements": handoff_rec["approval_requirements"],
        "lineage_source_layer": "operations_governance_handoff",
        "lineage_source_file": str(handoff_path).replace("\\", "/"),
        "lineage_source_record_id": handoff_rec["operations_governance_handoff_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_intake",
        "source_files": [
            str(handoff_path).replace("\\", "/"),
            str(scaled_closeout_path).replace("\\", "/"),
            str(request_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_intake_id",
        "governance_handoff_reference",
        "scaled_operations_closeout_reference",
        "intake_position",
        "governed_operations_request",
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
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write("# v38.0 Governed Operations Cycle Intake\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
