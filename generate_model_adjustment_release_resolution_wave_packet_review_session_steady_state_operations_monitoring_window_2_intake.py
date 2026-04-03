#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake.py

Purpose: Deterministically generate the v36.0 steady-state operations monitoring window 2 intake artifact from the closed v35.3 monitoring family, performance governance handoff, and operator-provided monitoring targets.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json
- operator-provided monitoring targets for window 2

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v35.3
- deterministic output
- no timestamps unless explicitly provided
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json")
    governance_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json")
    monitoring_targets_path = Path("operator_monitoring_targets_window_2.json")  # Must be provided

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake.md")

    # Load inputs
    with closeout_path.open("r", encoding="utf-8") as f:
        closeout = json.load(f)
    with governance_handoff_path.open("r", encoding="utf-8") as f:
        governance_handoff = json.load(f)
    with monitoring_targets_path.open("r", encoding="utf-8") as f:
        monitoring_targets = json.load(f)

    # Compose intake record (fields and values per v36.0 contract)
    record = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake",
        "source_files": [
            str(closeout_path).replace("\\", "/"),
            str(governance_handoff_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [
            {
                "steady_state_operations_monitoring_window_2_intake_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-intake-0001",
                "intake_position": 1,
                "prior_monitoring_reference": closeout["steady_state_operations_monitoring_closeout_id"],
                "monitored_family": "v34.0-v34.3 scaled-operations family",
                "monitoring_window_label": "window_2",
                "monitoring_objective": "confirm steady-state operational stability across a second monitoring window",
                "monitoring_metrics": [
                    "deliverable_completion_rate",
                    "approval_requirement_satisfaction_rate",
                    "intervention_rate",
                    "rollback_rate",
                    "incident_rate"
                ],
                "acceptable_ranges": monitoring_targets["acceptable_ranges"],
                "alert_conditions": monitoring_targets["alert_conditions"],
                "review_interval": monitoring_targets["review_interval"],
                "comparison_reference": "v35 steady-state monitoring family",
                "evidence_artifact": "steady_state_operations_monitoring_window_2_evidence",
                "stop_condition": "intake_frozen_and_ready_for_window_2_monitoring",
                "lineage_source_layer": "steady_state_operations_monitoring_closeout",
                "lineage_source_file": str(closeout_path).replace("\\", "/"),
                "lineage_source_record_id": closeout["steady_state_operations_monitoring_closeout_id"]
            }
        ]
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "steady_state_operations_monitoring_window_2_intake_id",
        "intake_position",
        "prior_monitoring_reference",
        "monitored_family",
        "monitoring_window_label",
        "monitoring_objective",
        "monitoring_metrics",
        "acceptable_ranges",
        "alert_conditions",
        "review_interval",
        "comparison_reference",
        "evidence_artifact",
        "stop_condition",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    rec = record["records"][0]
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write("# v36.0 Steady-State Operations Monitoring Window 2 Intake\n\n")
        f.write(f"**Source files:** {record['source_files']}\n\n")
        f.write(f"**Monitoring objective:** {rec['monitoring_objective']}\n\n")
        f.write(f"**Monitored family:** {rec['monitored_family']}\n\n")
        f.write(f"**Prior monitoring reference:** {rec['prior_monitoring_reference']}\n\n")
        f.write(f"**Metrics:** {rec['monitoring_metrics']}\n\n")
        f.write(f"**Acceptable ranges:** {rec['acceptable_ranges']}\n\n")
        f.write(f"**Alert conditions:** {rec['alert_conditions']}\n\n")
        f.write(f"**Review interval:** {rec['review_interval']}\n\n")
        f.write(f"**Stop condition:** {rec['stop_condition']}\n\n")
        f.write("\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(rec[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
