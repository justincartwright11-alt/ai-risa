#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_intake.py

Purpose: Deterministically generate the v35.0 steady-state operations monitoring intake artifact from the closed scaled-operations baseline and operator-provided monitoring targets.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json
- operator-provided monitoring targets

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_intake.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v34.3
- deterministic output
- no timestamps unless explicitly provided
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_closeout.json")
    governance_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json")
    monitoring_targets_path = Path("operator_monitoring_targets.json")  # Must be provided

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_intake.md")

    # Load inputs
    with closeout_path.open("r", encoding="utf-8") as f:
        closeout = json.load(f)
    with governance_handoff_path.open("r", encoding="utf-8") as f:
        governance_handoff = json.load(f)
    with monitoring_targets_path.open("r", encoding="utf-8") as f:
        monitoring_targets = json.load(f)

    # Compose intake record
    record = {
        "steady_state_monitoring_intake_id": "resolution-wave-packet-review-session-steady-state-monitoring-intake-0001",
        "scaled_operations_closeout_id": closeout["scaled_operations_closeout_id"],
        "performance_governance_handoff_id": governance_handoff["records"][0]["performance_governance_handoff_id"],
        "monitoring_targets": monitoring_targets["monitoring_targets"],
        "monitoring_owner": monitoring_targets["monitoring_owner"],
        "monitoring_scope": monitoring_targets["monitoring_scope"],
        "incident_detection_rules": monitoring_targets["incident_detection_rules"],
        "intervention_rules": monitoring_targets["intervention_rules"],
        "rollback_signal_rules": monitoring_targets["rollback_signal_rules"],
        "deliverable_consistency_rules": monitoring_targets["deliverable_consistency_rules"],
        "lineage_source_layer": "scaled_operations_closeout",
        "lineage_source_file": str(closeout_path),
        "lineage_source_record_id": closeout["scaled_operations_closeout_id"]
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write(f"# v35.0 Steady-State Operations Monitoring Intake\n\n")
        for k, v in record.items():
            f.write(f"- **{k}**: {v}\n")

if __name__ == "__main__":
    main()
