#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_plan.py

Purpose: Deterministically generate the v40.1 governed operations cycle 2 plan artifact from the frozen governed operations cycle 2 intake and governance handoff.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_plan.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_plan.md

Rules:
- governed-operations family only
- do not reopen or mutate v8.8 through v40.0
- planning only
- must preserve governance thresholds, escalation rules, review cadence, intervention rules, rollback triggers, and approval requirements
- deterministic output
- no timestamps unless explicitly provided in intake
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake.json")
    handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")

    # Output paths
    plan_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_plan.json")
    plan_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_plan.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    intake_rec = intake["records"][0]
    with handoff_path.open("r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_rec = handoff["records"][0]

    # Compose plan record
    record = {
        "governed_operations_cycle_2_plan_id": "resolution-wave-packet-review-session-governed-operations-cycle-2-plan-0001",
        "governed_operations_cycle_2_intake_id": intake_rec["governed_operations_cycle_2_intake_id"],
        "plan_position": 1,
        "authorization_status": "authorized",
        "authorization_source": "operator",
        "operator": intake_rec["operator"],
        "target_operational_scope": intake_rec["target_operational_scope"],
        "requested_deliverables": intake_rec["requested_deliverables"],
        "governance_thresholds": handoff_rec["governance_thresholds"],
        "alert_escalation_rules": handoff_rec["alert_escalation_rules"],
        "review_cadence": handoff_rec["review_cadence"],
        "approval_requirements": handoff_rec["approval_requirements"],
        "operator_intervention_rules": handoff_rec["operator_intervention_rules"],
        "rollback_trigger_rules": handoff_rec["rollback_trigger_rules"],
        "execution_steps": [
            "validate governed cycle 2 intake and inherited governance controls",
            "prepare governed operational inputs",
            "run governed operations cycle 2",
            "capture governed cycle 2 execution evidence",
            "evaluate outcome against governance thresholds and approval requirements"
        ],
        "evidence_artifact": intake_rec["evidence_artifact"],
        "stop_condition": "plan_frozen_and_ready_for_governed_cycle_2_execution",
        "lineage_source_layer": "governed_operations_cycle_2_intake",
        "lineage_source_file": str(intake_path).replace("\\", "/"),
        "lineage_source_record_id": intake_rec["governed_operations_cycle_2_intake_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_plan",
        "source_files": [
            str(intake_path).replace("\\", "/"),
            str(handoff_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with plan_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_2_plan_id",
        "governed_operations_cycle_2_intake_id",
        "plan_position",
        "authorization_status",
        "authorization_source",
        "operator",
        "target_operational_scope",
        "requested_deliverables",
        "governance_thresholds",
        "alert_escalation_rules",
        "review_cadence",
        "approval_requirements",
        "operator_intervention_rules",
        "rollback_trigger_rules",
        "execution_steps",
        "evidence_artifact",
        "stop_condition",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with plan_md_path.open("w", encoding="utf-8") as f:
        f.write("# v40.1 Governed Operations Cycle 2 Plan\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
