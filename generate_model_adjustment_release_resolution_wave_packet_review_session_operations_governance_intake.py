#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.py

Purpose: Deterministically generate the v37.0 operations governance intake artifact from the closed steady-state monitoring families and performance governance handoff.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.md

Rules:
- governance family only
- do not reopen or mutate v8.8 through v36.3
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    ss_closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_closeout.json")
    ss_window2_closeout_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_steady_state_operations_monitoring_window_2_closeout.json")
    perf_governance_handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json")

    # Output paths
    intake_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.json")
    intake_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake.md")

    # Load inputs
    with ss_closeout_path.open("r", encoding="utf-8") as f:
        ss_closeout = json.load(f)
    with ss_window2_closeout_path.open("r", encoding="utf-8") as f:
        ss_window2_closeout = json.load(f)
    with perf_governance_handoff_path.open("r", encoding="utf-8") as f:
        perf_governance_handoff = json.load(f)
    perf_governance_rec = perf_governance_handoff["records"][0]

    # Compose intake record (fields and values for governance)
    record = {
        "operations_governance_intake_id": "resolution-wave-packet-review-session-operations-governance-intake-0001",
        "monitored_family_range": "v35.0-v36.3 steady-state monitoring families",
        "governance_objective": "convert stable steady-state results into durable operating rules for ongoing scaled operation",
        "steady_state_monitoring_closeout_reference": ss_closeout["steady_state_operations_monitoring_closeout_id"],
        "steady_state_monitoring_window_2_closeout_reference": ss_window2_closeout["records"][0]["steady_state_operations_monitoring_window_2_closeout_id"],
        "performance_governance_handoff_reference": perf_governance_rec["performance_governance_handoff_id"],
        "governance_metrics": [
            "deliverable_completion_rate",
            "approval_requirement_satisfaction_rate",
            "intervention_rate",
            "rollback_rate",
            "incident_rate"
        ],
        "governance_thresholds": ["provided_by_operator"],
        "escalation_paths": ["provided_by_operator"],
        "review_cadence": "provided_by_operator",
        "intervention_triggers": ["provided_by_operator"],
        "rollback_governance": ["provided_by_operator"],
        "lineage_source_layer": "steady_state_operations_monitoring_window_2_closeout",
        "lineage_source_file": str(ss_window2_closeout_path).replace("\\", "/"),
        "lineage_source_record_id": ss_window2_closeout["records"][0]["steady_state_operations_monitoring_window_2_closeout_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_operations_governance_intake",
        "source_files": [
            str(ss_closeout_path).replace("\\", "/"),
            str(ss_window2_closeout_path).replace("\\", "/"),
            str(perf_governance_handoff_path).replace("\\", "/")
        ],
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with intake_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "operations_governance_intake_id",
        "monitored_family_range",
        "governance_objective",
        "steady_state_monitoring_closeout_reference",
        "steady_state_monitoring_window_2_closeout_reference",
        "performance_governance_handoff_reference",
        "governance_metrics",
        "governance_thresholds",
        "escalation_paths",
        "review_cadence",
        "intervention_triggers",
        "rollback_governance",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    with intake_md_path.open("w", encoding="utf-8") as f:
        f.write("# v37.0 Operations Governance Intake\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(str(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
