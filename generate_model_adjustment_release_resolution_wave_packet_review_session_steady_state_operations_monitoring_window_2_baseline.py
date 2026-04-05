#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.py

Purpose: Deterministically generate the v36.1 steady-state operations monitoring window 2 baseline artifact from the frozen v36.0 intake, scaled-operations execution evidence, scaled-operations closeout, and prior steady-state closeout.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_execution_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v36.0
- baseline only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_intake.json")
    execution_evidence_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_execution_evidence.json")
    scaled_closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scaled_operations_closeout.json")
    prior_monitoring_closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json")

    # Output paths
    baseline_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.json")
    baseline_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.md")

    # Load inputs
    with intake_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)
    with execution_evidence_path.open("r", encoding="utf-8") as f:
        execution_evidence = json.load(f)
    with scaled_closeout_path.open("r", encoding="utf-8") as f:
        scaled_closeout = json.load(f)
    with prior_monitoring_closeout_path.open("r", encoding="utf-8") as f:
        prior_monitoring_closeout = json.load(f)

    intake_rec = intake["records"][0]

    # Compose baseline record (fields and values per v36.1 contract)
    record = {
        "steady_state_operations_monitoring_window_2_baseline_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-baseline-0001",
        "steady_state_operations_monitoring_window_2_intake_id": intake_rec["steady_state_operations_monitoring_window_2_intake_id"],
        "baseline_position": 1,
        "monitored_family": intake_rec["monitored_family"],
        "baseline_run_reference": scaled_closeout["scaled_operations_closeout_id"],
        "prior_monitoring_reference": intake_rec["prior_monitoring_reference"],
        "monitoring_metrics": intake_rec["monitoring_metrics"],
        "baseline_values": ["provided_by_operator"],
        "acceptable_ranges": intake_rec["acceptable_ranges"],
        "alert_conditions": intake_rec["alert_conditions"],
        "review_interval": intake_rec["review_interval"],
        "comparison_reference": intake_rec["comparison_reference"],
        "stop_condition": "baseline_frozen_and_ready_for_monitoring_window_2",
        "lineage_source_layer": "steady_state_operations_monitoring_window_2_intake",
        "lineage_source_file": str(intake_path).replace("\\", "/"),
        "lineage_source_record_id": intake_rec["steady_state_operations_monitoring_window_2_intake_id"]
    }

    # Deterministic JSON output
    with baseline_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "steady_state_operations_monitoring_window_2_baseline_id",
        "steady_state_operations_monitoring_window_2_intake_id",
        "baseline_position",
        "monitored_family",
        "baseline_run_reference",
        "prior_monitoring_reference",
        "monitoring_metrics",
        "baseline_values",
        "acceptable_ranges",
        "alert_conditions",
        "review_interval",
        "comparison_reference",
        "stop_condition",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    with baseline_md_path.open("w", encoding="utf-8") as f:
        f.write("# v36.1 Steady-State Operations Monitoring Window 2 Baseline\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
