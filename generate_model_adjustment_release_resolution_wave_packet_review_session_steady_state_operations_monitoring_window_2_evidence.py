#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence.py

Purpose: Deterministically generate the v36.2 steady-state operations monitoring window 2 evidence artifact from the frozen v36.1 baseline and operator-provided monitoring observations.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.json
- operator-provided steady-state monitoring observations for window 2

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v36.1
- evidence only
- deterministic output from supplied evidence
- no timestamps unless explicitly provided in monitoring evidence
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    baseline_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.json")
    operator_evidence_path = Path("operator_steady_state_monitoring_observations_window_2.json")  # Must be provided

    # Output paths
    evidence_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence.json")
    evidence_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence.md")

    # Load inputs
    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    with operator_evidence_path.open("r", encoding="utf-8") as f:
        operator_evidence = json.load(f)

    # Compose evidence record (fields and values per v36.2 contract)
    record = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence",
        "source_file": str(baseline_path).replace("\\", "/"),
        "record_count": 1,
        "records": [
            {
                "steady_state_operations_monitoring_window_2_evidence_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-evidence-0001",
                "steady_state_operations_monitoring_window_2_baseline_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-baseline-0001",
                "evidence_position": operator_evidence["evidence_position"],
                "monitoring_window_observed": operator_evidence["monitoring_window_observed"],
                "monitoring_metrics": [
                    "deliverable_completion_rate",
                    "approval_requirement_satisfaction_rate",
                    "intervention_rate",
                    "rollback_rate",
                    "incident_rate"
                ],
                "observed_values": operator_evidence["observed_values"],
                "acceptable_ranges": operator_evidence["acceptable_ranges"],
                "alert_conditions": operator_evidence["alert_conditions"],
                "alert_triggered": operator_evidence["alert_triggered"],
                "deviation_detected": operator_evidence["deviation_detected"],
                "comparison_to_window_1": operator_evidence["comparison_to_window_1"],
                "monitoring_result_summary": operator_evidence["monitoring_result_summary"],
                "lineage_source_layer": "steady_state_operations_monitoring_window_2_baseline",
                "lineage_source_file": str(baseline_path).replace("\\", "/"),
                "lineage_source_record_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-baseline-0001"
            }
        ]
    }

    # Deterministic JSON output
    with evidence_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "steady_state_operations_monitoring_window_2_evidence_id",
        "steady_state_operations_monitoring_window_2_baseline_id",
        "evidence_position",
        "monitoring_window_observed",
        "monitoring_metrics",
        "observed_values",
        "acceptable_ranges",
        "alert_conditions",
        "alert_triggered",
        "deviation_detected",
        "comparison_to_window_1",
        "monitoring_result_summary",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    rec = record["records"][0]
    with evidence_md_path.open("w", encoding="utf-8") as f:
        f.write("# v36.2 Steady-State Operations Monitoring Window 2 Evidence\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(rec[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
