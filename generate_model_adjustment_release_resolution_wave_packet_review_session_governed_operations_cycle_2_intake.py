#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake.py

Purpose: Deterministically generate the v40.0 governed operations cycle 2 intake artifact from the review handoff, governance handoff, and operator-provided request.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json
- operator-provided governed operations cycle 2 request payload (operator_governed_operations_cycle_2_request.json)

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake.md

Rules:
- new operational family only
- do not reopen or mutate v8.8 through v39.2
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
    review_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_review_handoff.json")
    governance_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_handoff.json")
    request_path = Path("operator_governed_operations_cycle_2_request.json")

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake.md")

    # Load inputs
    with review_handoff_path.open("r", encoding="utf-8") as f:
        review_handoff = json.load(f)
    review_handoff_rec = review_handoff["records"][0]
    with governance_handoff_path.open("r", encoding="utf-8") as f:
        governance_handoff = json.load(f)
    governance_handoff_rec = governance_handoff["records"][0]
    with request_path.open("r", encoding="utf-8") as f:
        request = json.load(f)

    # Compose intake record
    record = {
        "governed_operations_cycle_2_intake_id": "resolution-wave-packet-review-session-governed-operations-cycle-2-intake-0001",
        "intake_position": 1,
        "prior_review_reference": review_handoff_rec["governed_operations_review_handoff_id"],
        "governance_handoff_id": governance_handoff_rec["operations_governance_handoff_id"],
        "recommended_disposition": review_handoff_rec["recommended_disposition"],
        "authorization_status": "authorized",
        "authorization_source": "operator",
        "operator": request["operator"],
        "target_operational_scope": request["target_operational_scope"],
        "requested_deliverables": request["requested_deliverables"],
        "governance_thresholds": governance_handoff_rec["governance_thresholds"],
        "alert_escalation_rules": governance_handoff_rec["alert_escalation_rules"],
        "review_cadence": governance_handoff_rec["review_cadence"],
        "approval_requirements": governance_handoff_rec["approval_requirements"],
        "operator_intervention_rules": governance_handoff_rec["operator_intervention_rules"],
        "rollback_trigger_rules": governance_handoff_rec["rollback_trigger_rules"],
        "evidence_artifact": request["evidence_artifact"],
        "stop_condition": request["stop_condition"],
        "lineage_source_layer": "governed_operations_review_handoff",
        "lineage_source_file": str(review_handoff_path).replace("\\", "/"),
        "lineage_source_record_id": review_handoff_rec["governed_operations_review_handoff_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_2_intake",
        "source_files": [
            str(review_handoff_path).replace("\\", "/"),
            str(governance_handoff_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_2_intake_id",
        "intake_position",
        "prior_review_reference",
        "governance_handoff_id",
        "recommended_disposition",
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
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write("# v40.0 Governed Operations Cycle 2 Intake\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
