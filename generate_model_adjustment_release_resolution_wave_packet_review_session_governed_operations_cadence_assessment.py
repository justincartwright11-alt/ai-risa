#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.py

Purpose: Deterministically generate the v43.1 governed operations cadence assessment artifact, referencing the v43.0 intake and all three governed operations cycle closeouts, plus governance handoff and operator-provided findings.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json
- operator-provided cadence review findings (manual input)

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.md

Rules:
- cadence family only
- do not reopen or mutate v8.8 through v43.0
- assessment only
- deterministic output
- no timestamps unless explicitly provided in cadence review findings
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.json")
    cycle1_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_closeout.json")
    cycle2_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_closeout.json")
    cycle3_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_3_closeout.json")
    governance_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")

    # Output paths
    assessment_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.json")
    assessment_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.md")

    # Load required records
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)["records"][0]
    with cycle1_path.open("r", encoding="utf-8") as f:
        cycle1_rec = json.load(f)["records"][0]
        cycle1 = cycle1_rec["governed_operations_cycle_closeout_id"] if "governed_operations_cycle_closeout_id" in cycle1_rec else "cycle1"
    with cycle2_path.open("r", encoding="utf-8") as f:
        cycle2_rec = json.load(f)["records"][0]
        cycle2 = cycle2_rec["governed_operations_cycle_2_closeout_id"] if "governed_operations_cycle_2_closeout_id" in cycle2_rec else cycle2_rec.get("governed_operations_cycle_closeout_id", "cycle2")
    with cycle3_path.open("r", encoding="utf-8") as f:
        cycle3_rec = json.load(f)["records"][0]
        cycle3 = cycle3_rec["governed_operations_cycle_3_closeout_id"] if "governed_operations_cycle_3_closeout_id" in cycle3_rec else cycle3_rec.get("governed_operations_cycle_closeout_id", "cycle3")
    with governance_handoff_path.open("r", encoding="utf-8") as f:
        governance_handoff = json.load(f)["records"][0]

    # Operator-provided findings (manual input)
    provided = "provided_by_operator"

    # Compose assessment record
    record = {
        "governed_operations_cadence_assessment_id": "resolution-wave-packet-review-session-governed-operations-cadence-assessment-0001",
        "governed_operations_cadence_checkpoint_intake_id": intake["governed_operations_cadence_checkpoint_intake_id"],
        "assessment_position": 1,
        "reviewed_cycle_references": [
            "resolution-wave-packet-review-session-governed-operations-cycle-closeout-0001",
            "resolution-wave-packet-review-session-governed-operations-cycle-2-closeout-0001",
            "resolution-wave-packet-review-session-governed-operations-cycle-3-closeout-0001"
        ],
        "governance_reference": "resolution-wave-packet-review-session-operations-governance-handoff-0001",
        "multi_cycle_stability_status": provided,
        "deliverable_completion_trend": provided,
        "governance_threshold_trend": provided,
        "approval_requirement_trend": provided,
        "intervention_trend": provided,
        "rollback_trend": provided,
        "incident_trend": provided,
        "cadence_findings": [provided],
        "recommended_disposition": provided,
        "lineage_source_layer": "governed_operations_cadence_checkpoint_intake",
        "lineage_source_file": str(intake_path).replace("\\", "/"),
        "lineage_source_record_id": intake["governed_operations_cadence_checkpoint_intake_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment",
        "source_files": [
            str(intake_path).replace("\\", "/"),
            str(cycle1_path).replace("\\", "/"),
            str(cycle2_path).replace("\\", "/"),
            str(cycle3_path).replace("\\", "/"),
            str(governance_handoff_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with assessment_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cadence_assessment_id",
        "governed_operations_cadence_checkpoint_intake_id",
        "assessment_position",
        "reviewed_cycle_references",
        "governance_reference",
        "multi_cycle_stability_status",
        "deliverable_completion_trend",
        "governance_threshold_trend",
        "approval_requirement_trend",
        "intervention_trend",
        "rollback_trend",
        "incident_trend",
        "cadence_findings",
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
        f.write("# v43.1 Governed Operations Cadence Assessment\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
