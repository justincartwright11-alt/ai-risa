#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_intake.py

Purpose: Deterministically generate the v34.0 scaled operations intake artifact under explicit operator authorization.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json
- operator authorization payload (external, must be provided)

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_intake.md

Rules:
- new scaled-operations family only
- do not reopen or mutate v8.8 through v33.0
- explicit operator authorization is now the rollout gate
- deterministic output
- no timestamps unless explicitly provided in the authorization payload
- no release logic
- no merge/tag/push

The intake must explicitly record:
- scaled_operations_intake_id
- authorization_status = authorized
- authorization_source = operator
- governance_handoff_id
- operator
- target_operational_scope
- requested_deliverables
- approval_requirements
- operator_intervention_rules
- rollback_trigger_rules
- evidence_artifact
- stop_condition
- lineage_source_layer
- lineage_source_file
- lineage_source_record_id
"""
import json
import sys
from pathlib import Path

def main():
    # Input paths
    auth_briefing_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing.json")
    governance_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json")
    operator_auth_payload_path = Path("operator_authorization_payload.json")  # External, must be provided

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_intake.md")

    # Load inputs
    with auth_briefing_path.open("r", encoding="utf-8") as f:
        auth_briefing = json.load(f)
    with governance_handoff_path.open("r", encoding="utf-8") as f:
        governance_handoff = json.load(f)
    with operator_auth_payload_path.open("r", encoding="utf-8") as f:
        operator_auth = json.load(f)

    # Deterministically generate scaled_operations_intake_id
    scale_auth_briefing_id = auth_briefing["records"][0]["scale_authorization_briefing_id"]
    scaled_operations_intake_id = f"v34.0-scaled-operations-intake-{scale_auth_briefing_id}"

    record = {
        "scaled_operations_intake_id": scaled_operations_intake_id,
        "authorization_status": operator_auth["authorization_status"],
        "authorization_source": operator_auth["authorization_source"],
        "governance_handoff_id": governance_handoff["records"][0]["performance_governance_handoff_id"],
        "operator": operator_auth["operator"],
        "target_operational_scope": operator_auth["target_operational_scope"],
        "requested_deliverables": operator_auth["requested_deliverables"],
        "approval_requirements": operator_auth["approval_requirements"],
        "operator_intervention_rules": operator_auth["operator_intervention_rules"],
        "rollback_trigger_rules": operator_auth["rollback_trigger_rules"],
        "evidence_artifact": operator_auth["evidence_artifact"],
        "stop_condition": operator_auth["stop_condition"],
        "lineage_source_layer": "v33.0-controlled-release-resolution-wave-packet-review-session-scale-authorization-briefing",
        "lineage_source_file": str(auth_briefing_path),
        "lineage_source_record_id": scale_auth_briefing_id
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write(f"# v34.0 Scaled Operations Intake\n\n")
        for k, v in record.items():
            f.write(f"- **{k}**: {v}\n")

if __name__ == "__main__":
    main()
