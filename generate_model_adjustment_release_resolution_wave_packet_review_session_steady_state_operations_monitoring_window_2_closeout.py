#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.py

Purpose: Deterministically generate the v36.3 steady-state operations monitoring window 2 closeout artifact from the frozen v36.1 baseline and v36.2 evidence.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v36.2
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
    baseline_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_baseline.json")
    evidence_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_evidence.json")

    # Output paths
    closeout_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.json")
    closeout_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.md")

    # Load inputs
    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    with evidence_path.open("r", encoding="utf-8") as f:
        evidence = json.load(f)
    evidence_rec = evidence["records"][0]

    # Compose closeout record (fields and values per v36.3 contract)
    record = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout",
        "source_files": [
            str(baseline_path).replace("\\", "/"),
            str(evidence_path).replace("\\", "/")
        ],
        "frozen_slices": [
            "v36.0-controlled-release-resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-intake",
            "v36.1-controlled-release-resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-baseline",
            "v36.2-controlled-release-resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-evidence"
        ],
        "steady_state_operations_monitoring_window_2_baseline_complete": True,
        "steady_state_operations_monitoring_window_2_evidence_complete": True,
        "steady_state_operations_monitoring_window_2_family_complete": True,
        "monitoring_window_observed": True,
        "alert_triggered": evidence_rec["alert_triggered"],
        "deviation_detected": evidence_rec["deviation_detected"],
        "merge_performed": False,
        "tag_performed": False,
        "push_performed": False,
        "record_count": 1,
        "records": [
            {
                "steady_state_operations_monitoring_window_2_closeout_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-closeout-0001",
                "closeout_position": 1,
                "steady_state_operations_monitoring_window_2_baseline_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-baseline-0001",
                "steady_state_operations_monitoring_window_2_evidence_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-evidence-0001",
                "final_monitoring_outcome": "within_expected_range",
                "alert_triggered": evidence_rec["alert_triggered"],
                "deviation_detected": evidence_rec["deviation_detected"],
                "comparison_to_window_1": evidence_rec["comparison_to_window_1"],
                "monitoring_result_summary": evidence_rec["monitoring_result_summary"],
                "steady_state_operations_monitoring_window_2_family_complete": True,
                "lineage_source_layer": "steady_state_operations_monitoring_window_2_evidence",
                "lineage_source_file": str(evidence_path).replace("\\", "/"),
                "lineage_source_record_id": "resolution-wave-packet-review-session-steady-state-operations-monitoring-window-2-evidence-0001"
            }
        ]
    }

    # Deterministic JSON output
    with closeout_json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "steady_state_operations_monitoring_window_2_closeout_id",
        "closeout_position",
        "steady_state_operations_monitoring_window_2_baseline_id",
        "steady_state_operations_monitoring_window_2_evidence_id",
        "final_monitoring_outcome",
        "alert_triggered",
        "deviation_detected",
        "comparison_to_window_1",
        "monitoring_result_summary",
        "steady_state_operations_monitoring_window_2_family_complete",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    rec = record["records"][0]
    with closeout_md_path.open("w", encoding="utf-8") as f:
        f.write("# v36.3 Steady-State Operations Monitoring Window 2 Closeout\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(rec[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
