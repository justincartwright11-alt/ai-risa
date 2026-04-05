#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff.py

Purpose: Deterministically generate the v39.2 governed operations review handoff artifact from the frozen governed operations review intake and assessment.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff.md

Rules:
- review family only
- do not reopen or mutate v8.8 through v39.1
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
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_intake.json")
    assessment_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_assessment.json")

    # Output paths
    handoff_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff.json")
    handoff_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    intake_rec = intake["records"][0]
    with assessment_path.open("r", encoding="utf-8") as f:
        assessment = json.load(f)
    assessment_rec = assessment["records"][0]

    # Compose handoff record
    record = {
        "governed_operations_review_handoff_id": "resolution-wave-packet-review-session-governed-operations-review-handoff-0001",
        "governed_operations_review_assessment_id": assessment_rec["governed_operations_review_assessment_id"],
        "handoff_position": 1,
        "reviewed_cycle_reference": assessment_rec["reviewed_cycle_reference"],
        "governance_reference": assessment_rec["governance_reference"],
        "deliverable_completion_status": assessment_rec["deliverable_completion_status"],
        "governance_threshold_compliance": assessment_rec["governance_threshold_compliance"],
        "approval_requirement_compliance": assessment_rec["approval_requirement_compliance"],
        "intervention_rule_compliance": assessment_rec["intervention_rule_compliance"],
        "rollback_rule_compliance": assessment_rec["rollback_rule_compliance"],
        "incident_status": assessment_rec["incident_status"],
        "recommended_disposition": assessment_rec["recommended_disposition"],
        "review_family_complete": True,
        "lineage_source_layer": "governed_operations_review_assessment",
        "lineage_source_file": str(assessment_path).replace("\\", "/"),
        "lineage_source_record_id": assessment_rec["governed_operations_review_assessment_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff",
        "source_files": [
            str(intake_path).replace("\\", "/"),
            str(assessment_path).replace("\\", "/")
        ],
        "frozen_slices": [
            "v39.0-controlled-release-resolution-wave-packet-review-session-governed-operations-review-intake",
            "v39.1-controlled-release-resolution-wave-packet-review-session-governed-operations-review-assessment"
        ],
        "governed_operations_review_intake_complete": True,
        "governed_operations_review_assessment_complete": True,
        "governed_operations_review_handoff_complete": True,
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
        "governed_operations_review_handoff_id",
        "governed_operations_review_assessment_id",
        "handoff_position",
        "reviewed_cycle_reference",
        "governance_reference",
        "deliverable_completion_status",
        "governance_threshold_compliance",
        "approval_requirement_compliance",
        "intervention_rule_compliance",
        "rollback_rule_compliance",
        "incident_status",
        "recommended_disposition",
        "review_family_complete",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with handoff_md_path.open("w", encoding="utf-8") as f:
        f.write("# v39.2 Governed Operations Review Handoff\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
