#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.py

Purpose: Deterministically generate the v35.3 steady-state operations monitoring closeout artifact from the frozen v35.2 evidence baseline.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_baseline.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_evidence.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v35.2
- closeout only
- deterministic output
- no timestamps unless explicitly preserved from monitoring evidence
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    baseline_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_baseline.json")
    evidence_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_evidence.json")

    # Output paths
    closeout_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json")
    closeout_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.md")

    # Load inputs
    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    with evidence_path.open("r", encoding="utf-8") as f:
        evidence = json.load(f)

    # Compose closeout record
    record = {
        "steady_state_operations_monitoring_closeout_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-closeout-0001",
        "closeout_position": 1,
        "steady_state_operations_monitoring_baseline_id": baseline["steady_state_operations_monitoring_baseline_id"],
        "steady_state_operations_monitoring_evidence_id": evidence["steady_state_operations_monitoring_evidence_id"],
        "final_monitoring_outcome": "within_expected_range",
        "alert_triggered": evidence["alert_triggered"],
        "deviation_detected": evidence["deviation_detected"],
        "monitoring_result_summary": evidence["monitoring_result_summary"],
        "steady_state_operations_monitoring_family_complete": True,
        "lineage_source_layer": "steady_state_operations_monitoring_evidence",
        "lineage_source_file": str(evidence_path),
        "lineage_source_record_id": evidence["steady_state_operations_monitoring_evidence_id"]
    }

    # Deterministic JSON output
    with closeout_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "steady_state_operations_monitoring_closeout_id",
        "closeout_position",
        "steady_state_operations_monitoring_baseline_id",
        "steady_state_operations_monitoring_evidence_id",
        "final_monitoring_outcome",
        "alert_triggered",
        "deviation_detected",
        "monitoring_result_summary",
        "steady_state_operations_monitoring_family_complete",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    with closeout_md_path.open("w", encoding="utf-8") as f:
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
