#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.py

Deterministically generates the v26.0 performance monitoring intake for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_execution_evidence.json
- operator-provided monitoring targets

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.md

Rules:
- new monitoring family only
- do not reopen or mutate v8.8 through v25.3
- deterministic output
- no timestamps unless explicitly provided in evidence
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake.md"

# Example operator-provided monitoring targets (placeholder)
operator_monitoring_targets = {
    "monitoring_metrics": [
        "event_completion_time",
        "incident_rate",
        "deliverable_accuracy"
    ],
    "acceptable_ranges": {
        "event_completion_time": "< 2 hours",
        "incident_rate": "0%",
        "deliverable_accuracy": ">= 99%"
    },
    "alert_conditions": [
        "incident_rate > 0%",
        "deliverable_accuracy < 99%"
    ],
    "review_interval": "per event",
    "stop_condition": "3 consecutive failures"
}

RECORD = {
    "performance_monitoring_intake_id": "resolution-wave-packet-review-session-performance-monitoring-intake-0001",
    "monitored_family": "v25.0-v25.3-controlled-release-resolution-wave-packet-review-session-live-event-family",
    "baseline_run_reference": "resolution-wave-packet-review-session-live-event-closeout-0001",
    "monitoring_metrics": operator_monitoring_targets["monitoring_metrics"],
    "acceptable_ranges": operator_monitoring_targets["acceptable_ranges"],
    "alert_conditions": operator_monitoring_targets["alert_conditions"],
    "evidence_artifact": "resolution-wave-packet-review-session-live-event-execution-evidence-0001",
    "review_interval": operator_monitoring_targets["review_interval"],
    "stop_condition": operator_monitoring_targets["stop_condition"],
    "lineage_source_layer": "live_event_closeout",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_closeout.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-live-event-closeout-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_intake",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_closeout.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_execution_evidence.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "performance_monitoring_intake_id",
    "monitored_family",
    "baseline_run_reference",
    "monitoring_metrics",
    "acceptable_ranges",
    "alert_conditions",
    "evidence_artifact",
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
    lines.append("# v26.0 Controlled Release Resolution Wave Packet Review Session Performance Monitoring Intake\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Intake record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["performance_monitoring_intake_id"],
        r["monitored_family"],
        r["baseline_run_reference"],
        ", ".join(r["monitoring_metrics"]),
        json.dumps(r["acceptable_ranges"]),
        ", ".join(r["alert_conditions"]),
        r["evidence_artifact"],
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
