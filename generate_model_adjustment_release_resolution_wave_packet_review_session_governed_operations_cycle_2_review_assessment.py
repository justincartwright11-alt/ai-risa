#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_assessment.py

Purpose: Deterministically generate the v41.1 governed operations cycle 2 review assessment artifact from the frozen review intake, closeout, governance handoff, and operator-provided review findings.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json
- operator-provided cycle 2 review findings

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_assessment.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_assessment.md

Rules:
- review family only
- do not reopen or mutate v8.8 through v41.0
- assessment only
- deterministic output
- no timestamps unless explicitly provided in review findings
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_intake.json")
    closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json")
    governance_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")
    # Operator-provided review findings would be loaded here if available

    # Output paths
    assessment_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_assessment.json")
    assessment_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_assessment.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    intake_rec = intake["records"][0]
    with closeout_path.open("r", encoding="utf-8") as f:
        closeout = json.load(f)
    closeout_rec = closeout["records"][0]
    with governance_path.open("r", encoding="utf-8") as f:
        governance = json.load(f)
    governance_rec = governance["records"][0]

    # Compose assessment record (using provided contract and operator placeholders)
    record = {
        "governed_operations_cycle_2_review_assessment_id": "resolution-wave-packet-review-session-governed-operations-cycle-2-review-assessment-0001",
        "governed_operations_cycle_2_review_intake_id": intake_rec["governed_operations_cycle_2_review_intake_id"],
        "assessment_position": 1,
        "reviewed_cycle_reference": closeout_rec["governed_operations_cycle_2_closeout_id"],
        "governance_reference": governance_rec["operations_governance_handoff_id"] if "operations_governance_handoff_id" in governance_rec else "resolution-wave-packet-review-session-operations-governance-handoff-0001",
        "deliverable_completion_status": "provided_by_operator",
        "governance_threshold_compliance": "provided_by_operator",
        "approval_requirement_compliance": "provided_by_operator",
        "intervention_rule_compliance": "provided_by_operator",
        "rollback_rule_compliance": "provided_by_operator",
        "incident_status": "provided_by_operator",
        "review_findings": [
            "provided_by_operator"
        ],
        "recommended_disposition": "provided_by_operator",
        "lineage_source_layer": "governed_operations_cycle_2_review_intake",
        "lineage_source_file": str(intake_path).replace("\\", "/"),
        "lineage_source_record_id": intake_rec["governed_operations_cycle_2_review_intake_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_review_assessment",
        "source_files": [
            str(intake_path).replace("\\", "/"),
            str(closeout_path).replace("\\", "/"),
            str(governance_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with assessment_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_2_review_assessment_id",
        "governed_operations_cycle_2_review_intake_id",
        "assessment_position",
        "reviewed_cycle_reference",
        "governance_reference",
        "deliverable_completion_status",
        "governance_threshold_compliance",
        "approval_requirement_compliance",
        "intervention_rule_compliance",
        "rollback_rule_compliance",
        "incident_status",
        "review_findings",
        "recommended_disposition",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with assessment_md_path.open("w", encoding="utf-8") as f:
        f.write("# v41.1 Governed Operations Cycle 2 Review Assessment\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
