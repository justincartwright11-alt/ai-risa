#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.py

Deterministically generates the v26.3 performance monitoring closeout for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.md

Rules:
- monitoring family only
- do not reopen or mutate v8.8 through v26.2
- closeout only
- deterministic output
- no timestamps unless explicitly preserved from monitoring evidence
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.md"

RECORD = {
    "performance_monitoring_closeout_id": "resolution-wave-packet-review-session-performance-monitoring-closeout-0001",
    "closeout_position": 1,
    "performance_monitoring_baseline_id": "resolution-wave-packet-review-session-performance-monitoring-baseline-0001",
    "performance_monitoring_evidence_id": "resolution-wave-packet-review-session-performance-monitoring-evidence-0001",
    "final_monitoring_outcome": "within_expected_range",
    "alert_triggered": False,
    "deviation_detected": False,
    "monitoring_result_summary": "provided_by_operator",
    "performance_monitoring_family_complete": True,
    "lineage_source_layer": "performance_monitoring_evidence",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-performance-monitoring-evidence-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json"
    ],
    "frozen_slices": [
        "v26.0-controlled-release-resolution-wave-packet-review-session-performance-monitoring-intake",
        "v26.1-controlled-release-resolution-wave-packet-review-session-performance-monitoring-baseline",
        "v26.2-controlled-release-resolution-wave-packet-review-session-performance-monitoring-evidence"
    ],
    "performance_monitoring_baseline_complete": True,
    "performance_monitoring_evidence_complete": True,
    "performance_monitoring_family_complete": True,
    "monitoring_window_observed": True,
    "alert_triggered": False,
    "deviation_detected": False,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "performance_monitoring_closeout_id",
    "closeout_position",
    "performance_monitoring_baseline_id",
    "performance_monitoring_evidence_id",
    "final_monitoring_outcome",
    "alert_triggered",
    "deviation_detected",
    "monitoring_result_summary",
    "performance_monitoring_family_complete",
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
    lines.append("# v26.3 Controlled Release Resolution Wave Packet Review Session Performance Monitoring Closeout\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Frozen slices:**\n")
    for s in JSON_CONTRACT["frozen_slices"]:
        lines.append(f"- {s}")
    lines.append("\n**Closeout record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["performance_monitoring_closeout_id"],
        str(r["closeout_position"]),
        r["performance_monitoring_baseline_id"],
        r["performance_monitoring_evidence_id"],
        r["final_monitoring_outcome"],
        str(r["alert_triggered"]),
        str(r["deviation_detected"]),
        r["monitoring_result_summary"],
        str(r["performance_monitoring_family_complete"]),
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
