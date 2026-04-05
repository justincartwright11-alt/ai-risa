#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.py

Purpose: Deterministically generate the v37.2 operations governance handoff artifact from the frozen v37.0 intake and v37.1 policy.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.md

Rules:
- governance family only
- do not reopen or mutate v8.8 through v37.1
- handoff only
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
    policy_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_policy.json")

    # Output paths
    handoff_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")
    handoff_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    with policy_path.open("r", encoding="utf-8") as f:
        policy = json.load(f)
    policy_rec = policy["records"][0]

    # Compose handoff record (fields and values per v37.2 contract)
    record = {
        "operations_governance_handoff_id": "resolution-wave-packet-review-session-operations-governance-handoff-0001",
        "operations_governance_policy_id": "resolution-wave-packet-review-session-operations-governance-policy-0001",
        "handoff_position": 1,
        "governance_family_complete": True,
        "governance_objective": policy_rec["governance_objective"],
        "governance_metrics": policy_rec["governance_metrics"],
        "governance_thresholds": policy_rec["governance_thresholds"],
        "alert_escalation_rules": policy_rec["alert_escalation_rules"],
        "review_cadence": policy_rec["review_cadence"],
        "steady_state_acceptance_rules": policy_rec["steady_state_acceptance_rules"],
        "operator_intervention_rules": policy_rec["operator_intervention_rules"],
        "rollback_trigger_rules": policy_rec["rollback_trigger_rules"],
        "approval_requirements": policy_rec["approval_requirements"],
        "lineage_source_layer": "operations_governance_policy",
        "lineage_source_file": str(policy_path).replace("\\", "/"),
        "lineage_source_record_id": "resolution-wave-packet-review-session-operations-governance-policy-0001"
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff",
        "source_files": [
            str(intake_path).replace("\\", "/"),
            str(policy_path).replace("\\", "/")
        ],
        "frozen_slices": [
            "v37.0-controlled-release-resolution-wave-packet-review-session-operations-governance-intake",
            "v37.1-controlled-release-resolution-wave-packet-review-session-operations-governance-policy"
        ],
        "operations_governance_intake_complete": True,
        "operations_governance_policy_complete": True,
        "operations_governance_handoff_complete": True,
        "merge_performed": False,
        "tag_performed": False,
        "push_performed": False,
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with handoff_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "operations_governance_handoff_id",
        "operations_governance_policy_id",
        "handoff_position",
        "governance_family_complete",
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
    with handoff_md_path.open("w", encoding="utf-8") as f:
        f.write("# v37.2 Operations Governance Handoff\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
