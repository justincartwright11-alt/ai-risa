#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy.py

Purpose: Deterministically generate the v37.1 operations governance policy artifact from the frozen v37.0 intake, steady-state closeouts, and performance governance handoff.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy.md

Rules:
- governance family only
- do not reopen or mutate v8.8 through v37.0
- policy only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.json")
    ss_closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json")
    ss_window2_closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.json")
    perf_governance_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json")

    # Output paths
    policy_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy.json")
    policy_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    intake_rec = intake["records"][0]

    # Compose policy record (fields and values per v37.1 contract)
    record = {
        "operations_governance_policy_id": "resolution-wave-packet-review-session-operations-governance-policy-0001",
        "operations_governance_intake_id": "resolution-wave-packet-review-session-operations-governance-intake-0001",
        "policy_position": 1,
        "governance_objective": "govern ongoing scaled operations using validated steady-state evidence across multiple monitoring windows",
        "governance_metrics": [
            "deliverable_completion_rate",
            "approval_requirement_satisfaction_rate",
            "intervention_rate",
            "rollback_rate",
            "incident_rate"
        ],
        "governance_thresholds": ["provided_by_operator"],
        "alert_escalation_rules": ["provided_by_operator"],
        "review_cadence": "provided_by_operator",
        "steady_state_acceptance_rules": ["provided_by_operator"],
        "operator_intervention_rules": ["provided_by_operator"],
        "rollback_trigger_rules": ["provided_by_operator"],
        "approval_requirements": ["provided_by_operator"],
        "lineage_source_layer": "operations_governance_intake",
        "lineage_source_file": str(intake_path).replace("\\", "/"),
        "lineage_source_record_id": "resolution-wave-packet-review-session-operations-governance-intake-0001"
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy",
        "source_files": [
            str(intake_path).replace("\\", "/"),
            str(ss_closeout_path).replace("\\", "/"),
            str(ss_window2_closeout_path).replace("\\", "/"),
            str(perf_governance_handoff_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with policy_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "operations_governance_policy_id",
        "operations_governance_intake_id",
        "policy_position",
        "governance_objective",
        "governance_metrics",
        "governance_thresholds",
        "alert_escalation_rules",
        "review_cadence",
        "steady_state_acceptance_rules",
        "operator_intervention_rules",
        "rollback_trigger_rules",
        "approval_requirements",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    with policy_md_path.open("w", encoding="utf-8") as f:
        f.write("# v37.1 Operations Governance Policy\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
