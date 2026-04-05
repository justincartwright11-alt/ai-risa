#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.py

Deterministically generates the v26.1 performance monitoring baseline for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_execution_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_closeout.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v26.0
- baseline only
- deterministic output
- no timestamps unless explicitly preserved from evidence
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.md"

RECORD = {
    "performance_monitoring_baseline_id": "resolution-wave-packet-review-session-performance-monitoring-baseline-0001",
    "performance_monitoring_intake_id": "resolution-wave-packet-review-session-performance-monitoring-intake-0001",
    "baseline_position": 1,
    "monitored_family": "v25.0-v25.3 live-event production family",
    "baseline_run_reference": "resolution-wave-packet-review-session-live-event-closeout-0001",
    "monitoring_metrics": [
        "deliverable_completion_rate",
        "success_criteria_pass_rate",
        "incident_rate",
        "rollback_rate"
    ],
    "baseline_values": [
        "provided_by_operator"
    ],
    "acceptable_ranges": [
        "provided_by_operator"
    ],
    "alert_conditions": [
        "provided_by_operator"
    ],
    "review_interval": "provided_by_operator",
    "stop_condition": "baseline_frozen_and_ready_for_monitoring",
    "lineage_source_layer": "performance_monitoring_intake",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-performance-monitoring-intake-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_execution_evidence.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_closeout.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "performance_monitoring_baseline_id",
    "performance_monitoring_intake_id",
    "baseline_position",
    "monitored_family",
    "baseline_run_reference",
    "monitoring_metrics",
    "baseline_values",
    "acceptable_ranges",
    "alert_conditions",
    "review_interval",
    "stop_condition",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id"
]

def write_json():
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(JSON_CONTRACT, f, indent=2, ensure_ascii=False)

def write_md():
    lines = []
    lines.append("# v26.1 Controlled Release Resolution Wave Packet Review Session Performance Monitoring Baseline\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Baseline record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["performance_monitoring_baseline_id"],
        r["performance_monitoring_intake_id"],
        str(r["baseline_position"]),
        r["monitored_family"],
        r["baseline_run_reference"],
        ", ".join(r["monitoring_metrics"]),
        ", ".join(r["baseline_values"]),
        ", ".join(r["acceptable_ranges"]),
        ", ".join(r["alert_conditions"]),
        r["review_interval"],
        r["stop_condition"],
        r["lineage_source_layer"],
        r["lineage_source_file"],
        r["lineage_source_record_id"]
    ]
    lines.append(" | ".join(row))
    Path(OUTPUT_MD).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def main():
    write_json()
    write_md()

if __name__ == "__main__":
    main()
