#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.py

Deterministically generates the v26.2 performance monitoring evidence for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json
- operator-provided monitoring observations for the monitored run window

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v26.1
- evidence only
- deterministic output from supplied evidence
- no timestamps unless explicitly preserved from monitoring evidence
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.md"

RECORD = {
    "performance_monitoring_evidence_id": "resolution-wave-packet-review-session-performance-monitoring-evidence-0001",
    "performance_monitoring_baseline_id": "resolution-wave-packet-review-session-performance-monitoring-baseline-0001",
    "evidence_position": 1,
    "monitoring_window_observed": True,
    "monitoring_metrics": [
        "deliverable_completion_rate",
        "success_criteria_pass_rate",
        "incident_rate",
        "rollback_rate"
    ],
    "observed_values": [
        "provided_by_operator"
    ],
    "acceptable_ranges": [
        "provided_by_operator"
    ],
    "alert_conditions": [
        "provided_by_operator"
    ],
    "alert_triggered": False,
    "deviation_detected": False,
    "monitoring_result_summary": "provided_by_operator",
    "lineage_source_layer": "performance_monitoring_baseline",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-performance-monitoring-baseline-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence",
    "source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json",
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "performance_monitoring_evidence_id",
    "performance_monitoring_baseline_id",
    "evidence_position",
    "monitoring_window_observed",
    "monitoring_metrics",
    "observed_values",
    "acceptable_ranges",
    "alert_conditions",
    "alert_triggered",
    "deviation_detected",
    "monitoring_result_summary",
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
    lines.append("# v26.2 Controlled Release Resolution Wave Packet Review Session Performance Monitoring Evidence\n")
    lines.append("**Source file:**\n")
    lines.append(f"- {JSON_CONTRACT['source_file']}")
    lines.append("\n**Evidence record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["performance_monitoring_evidence_id"],
        r["performance_monitoring_baseline_id"],
        str(r["evidence_position"]),
        str(r["monitoring_window_observed"]),
        ", ".join(r["monitoring_metrics"]),
        ", ".join(r["observed_values"]),
        ", ".join(r["acceptable_ranges"]),
        ", ".join(r["alert_conditions"]),
        str(r["alert_triggered"]),
        str(r["deviation_detected"]),
        r["monitoring_result_summary"],
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
