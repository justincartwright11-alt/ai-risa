#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment.py

Purpose: Deterministically generate the v39.1 governed operations review assessment artifact from the frozen governed operations review intake, cycle closeout, governance handoff, and operator-provided review findings.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json
- operator-provided review findings (operator_governed_operations_review_findings.json)

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment.md

Rules:
- review family only
- do not reopen or mutate v8.8 through v39.0
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
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.json")
    closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json")
    handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")
    findings_path = Path("operator_governed_operations_review_findings.json")

    # Output paths
    assessment_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment.json")
    assessment_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    intake_rec = intake["records"][0]
    with closeout_path.open("r", encoding="utf-8") as f:
        closeout = json.load(f)
    closeout_rec = closeout["records"][0]
    with handoff_path.open("r", encoding="utf-8") as f:
        handoff = json.load(f)
    handoff_rec = handoff["records"][0]
    with findings_path.open("r", encoding="utf-8") as f:
        findings = json.load(f)

    # Compose assessment record
    record = {
        "governed_operations_review_assessment_id": "resolution-wave-packet-review-session-governed-operations-review-assessment-0001",
        "governed_operations_review_intake_id": intake_rec["governed_operations_review_intake_id"],
        "assessment_position": 1,
        "reviewed_cycle_reference": closeout_rec["governed_operations_cycle_closeout_id"],
        "governance_reference": handoff_rec["operations_governance_handoff_id"],
        "deliverable_completion_status": findings["deliverable_completion_status"],
        "governance_threshold_compliance": findings["governance_threshold_compliance"],
        "approval_requirement_compliance": findings["approval_requirement_compliance"],
        "intervention_rule_compliance": findings["intervention_rule_compliance"],
        "rollback_rule_compliance": findings["rollback_rule_compliance"],
        "incident_status": findings["incident_status"],
        "review_findings": findings["review_findings"],
        "recommended_disposition": findings["recommended_disposition"],
        "lineage_source_layer": "governed_operations_review_intake",
        "lineage_source_file": str(intake_path).replace("\\", "/"),
        "lineage_source_record_id": intake_rec["governed_operations_review_intake_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment",
        "source_files": [
            str(intake_path).replace("\\", "/"),
            str(closeout_path).replace("\\", "/"),
            str(handoff_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with assessment_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_review_assessment_id",
        "governed_operations_review_intake_id",
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
        f.write("# v39.1 Governed Operations Review Assessment\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
