#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_plan.py

Purpose: Deterministically generate the v42.1 governed operations cycle 3 plan artifact from the frozen governed operations cycle 3 intake and governance handoff.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_plan.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_plan.md

Rules:
- governed-operations family only
- do not reopen or mutate v8.8 through v42.0
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
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_intake.json")
    handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")

    # Output paths
    plan_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_plan.json")
    plan_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_plan.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    intake_rec = intake["records"][0]
    with handoff_path.open("r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_rec = handoff["records"][0]

    # Compose plan record (using provided contract and operator placeholders)
    record = {
        "governed_operations_cycle_3_plan_id": "resolution-wave-packet-review-session-governed-operations-cycle-3-plan-0001",
        "governed_operations_cycle_3_intake_id": intake_rec["governed_operations_cycle_3_intake_id"],
        "plan_position": 1,
        "authorization_status": "authorized",
        "authorization_source": "operator",
        "operator": "provided_by_operator",
        "target_operational_scope": "provided_by_operator",
        "requested_deliverables": [
            "full report",
            "simulation brief",
            "operator summary"
        ],
        "governance_thresholds": [
            "provided_by_operator"
        ],
        "alert_escalation_rules": [
            "provided_by_operator"
        ],
        "review_cadence": "provided_by_operator",
        "approval_requirements": [
            "provided_by_operator"
        ],
        "operator_intervention_rules": [
            "provided_by_operator"
        ],
        "rollback_trigger_rules": [
            "provided_by_operator"
        ],
        "execution_steps": [
            "validate governed cycle 3 intake and inherited governance controls",
            "prepare governed operational inputs",
            "run governed operations cycle 3",
            "capture governed cycle 3 execution evidence",
            "evaluate outcome against governance thresholds and approval requirements"
        ],
        "evidence_artifact": "governed_operations_cycle_3_execution_evidence",
        "stop_condition": "plan_frozen_and_ready_for_governed_cycle_3_execution",
        "lineage_source_layer": "governed_operations_cycle_3_intake",
        "lineage_source_file": str(intake_path).replace("\\", "/"),
        "lineage_source_record_id": intake_rec["governed_operations_cycle_3_intake_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_plan",
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
        "governed_operations_cycle_3_plan_id",
        "governed_operations_cycle_3_intake_id",
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
        f.write("# v42.1 Governed Operations Cycle 3 Plan\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
