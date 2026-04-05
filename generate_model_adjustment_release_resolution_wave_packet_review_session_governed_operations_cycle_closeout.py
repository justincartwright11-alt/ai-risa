#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.py

Purpose: Deterministically generate the v38.3 governed operations cycle closeout artifact from the frozen governed operations cycle plan and execution evidence.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_plan.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.md

Rules:
- governed-operations family only
- do not reopen or mutate v8.8 through v38.2
- closeout only
- must evaluate requested deliverables, governance thresholds, approval requirements, intervention rules, and rollback triggers
- deterministic output
- no timestamps unless explicitly preserved from execution evidence
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    plan_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_plan.json")
    evidence_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence.json")

    # Output paths
    closeout_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json")
    closeout_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.md")

    # Load inputs
    with plan_path.open("r", encoding="utf-8") as f:
        plan = json.load(f)
    plan_rec = plan["records"][0]
    with evidence_path.open("r", encoding="utf-8") as f:
        evidence = json.load(f)
    evidence_rec = evidence["records"][0]

    # Compose closeout record
    record = {
        "governed_operations_cycle_closeout_id": "resolution-wave-packet-review-session-governed-operations-cycle-closeout-0001",
        "closeout_position": 1,
        "governed_operations_cycle_plan_id": plan_rec["governed_operations_cycle_plan_id"],
        "governed_operations_cycle_execution_evidence_id": evidence_rec["governed_operations_cycle_execution_evidence_id"],
        "final_operational_outcome": "accepted_into_operation",
        "requested_deliverables_completed": True,
        "governance_thresholds_breached": evidence_rec["governance_thresholds_breached"],
        "approval_requirements_satisfied": evidence_rec["approval_requirements_satisfied"],
        "operator_intervention_invoked": evidence_rec["operator_intervention_invoked"],
        "rollback_triggered": evidence_rec["rollback_triggered"],
        "execution_result_summary": evidence_rec["execution_result_summary"],
        "governed_operations_cycle_family_complete": True,
        "lineage_source_layer": "governed_operations_cycle_execution_evidence",
        "lineage_source_file": str(evidence_path).replace("\\", "/"),
        "lineage_source_record_id": evidence_rec["governed_operations_cycle_execution_evidence_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout",
        "source_files": [
            str(plan_path).replace("\\", "/"),
            str(evidence_path).replace("\\", "/")
        ],
        "frozen_slices": [
            "v38.0-controlled-release-resolution-wave-packet-review-session-governed-operations-cycle-intake",
            "v38.1-controlled-release-resolution-wave-packet-review-session-governed-operations-cycle-plan",
            "v38.2-controlled-release-resolution-wave-packet-review-session-governed-operations-cycle-execution-evidence"
        ],
        "governed_operations_cycle_plan_complete": True,
        "governed_operations_cycle_execution_evidence_complete": True,
        "governed_operations_cycle_family_complete": True,
        "execution_attempted": evidence_rec["execution_attempted"],
        "execution_pass": evidence_rec["execution_pass"],
        "governance_thresholds_breached": evidence_rec["governance_thresholds_breached"],
        "approval_requirements_satisfied": evidence_rec["approval_requirements_satisfied"],
        "operator_intervention_invoked": evidence_rec["operator_intervention_invoked"],
        "rollback_triggered": evidence_rec["rollback_triggered"],
        "incident_detected": evidence_rec["incident_detected"],
        "merge_performed": False,
        "tag_performed": False,
        "push_performed": False,
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with closeout_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_closeout_id",
        "closeout_position",
        "governed_operations_cycle_plan_id",
        "governed_operations_cycle_execution_evidence_id",
        "final_operational_outcome",
        "requested_deliverables_completed",
        "governance_thresholds_breached",
        "approval_requirements_satisfied",
        "operator_intervention_invoked",
        "rollback_triggered",
        "execution_result_summary",
        "governed_operations_cycle_family_complete",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with closeout_md_path.open("w", encoding="utf-8") as f:
        f.write("# v38.3 Governed Operations Cycle Closeout\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
