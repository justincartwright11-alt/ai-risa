#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_evidence.py

Purpose: Deterministically generate the v35.2 steady-state operations monitoring evidence artifact from the frozen v35.1 baseline and operator-provided monitoring observations.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_baseline.json
- operator-provided steady-state monitoring observations

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_evidence.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v35.1
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
    baseline_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_baseline.json")
    operator_evidence_path = Path("operator_steady_state_monitoring_observations.json")  # Must be provided

    # Output paths
    evidence_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_evidence.json")
    evidence_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_evidence.md")

    # Load inputs
    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    with operator_evidence_path.open("r", encoding="utf-8") as f:
        operator_evidence = json.load(f)

    # Compose evidence record
    record = {
        "steady_state_operations_monitoring_evidence_id": operator_evidence["steady_state_operations_monitoring_evidence_id"],
        "steady_state_operations_monitoring_baseline_id": baseline["steady_state_operations_monitoring_baseline_id"],
        "evidence_position": operator_evidence["evidence_position"],
        "monitoring_window_observed": operator_evidence["monitoring_window_observed"],
        "monitoring_metrics": baseline["monitoring_metrics"],
        "observed_values": operator_evidence["observed_values"],
        "acceptable_ranges": operator_evidence["acceptable_ranges"],
        "alert_conditions": operator_evidence["alert_conditions"],
        "alert_triggered": operator_evidence["alert_triggered"],
        "deviation_detected": operator_evidence["deviation_detected"],
        "monitoring_result_summary": operator_evidence["monitoring_result_summary"],
        "lineage_source_layer": "steady_state_operations_monitoring_baseline",
        "lineage_source_file": str(baseline_path),
        "lineage_source_record_id": baseline["steady_state_operations_monitoring_baseline_id"]
    }

    # Deterministic JSON output
    with evidence_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output
    with evidence_md_path.open("w", encoding="utf-8") as f:
        f.write(f"# v35.2 Steady-State Operations Monitoring Evidence\n\n")
        for k, v in record.items():
            f.write(f"- **{k}**: {v}\n")

if __name__ == "__main__":
    main()
