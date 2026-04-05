#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.py

Deterministically generates the v27.0 performance governance intake for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.md

Rules:
- governance family only
- do not reopen or mutate v8.8 through v26.3
- deterministic output
- no timestamps unless explicitly preserved from monitoring evidence
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.md"

RECORD = {
    "performance_governance_intake_id": "resolution-wave-packet-review-session-performance-governance-intake-0001",
    "monitored_family_range": "v26.0-v26.3 performance monitoring family",
    "governance_objective": "define reusable performance governance rules for all future live event families",
    "baseline_reference": "resolution-wave-packet-review-session-performance-monitoring-baseline-0001",
    "evidence_reference": "resolution-wave-packet-review-session-performance-monitoring-evidence-0001",
    "closeout_reference": "resolution-wave-packet-review-session-performance-monitoring-closeout-0001",
    "governance_metrics": [
        "deliverable_completion_rate",
        "success_criteria_pass_rate",
        "incident_rate",
        "rollback_rate"
    ],
    "governance_thresholds": [
        "provided_by_operator"
    ],
    "alert_escalation_rules": [
        "provided_by_operator"
    ],
    "review_cadence": "provided_by_operator",
    "rollout_gate": "provided_by_operator",
    "lineage_source_layer": "performance_monitoring_closeout",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-performance-monitoring-closeout-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "performance_governance_intake_id",
    "monitored_family_range",
    "governance_objective",
    "baseline_reference",
    "evidence_reference",
    "closeout_reference",
    "governance_metrics",
    "governance_thresholds",
    "alert_escalation_rules",
    "review_cadence",
    "rollout_gate",
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
    lines.append("# v27.0 Controlled Release Resolution Wave Packet Review Session Performance Governance Intake\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Intake record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["performance_governance_intake_id"],
        r["monitored_family_range"],
        r["governance_objective"],
        r["baseline_reference"],
        r["evidence_reference"],
        r["closeout_reference"],
        ", ".join(r["governance_metrics"]),
        ", ".join(r["governance_thresholds"]),
        ", ".join(r["alert_escalation_rules"]),
        r["review_cadence"],
        r["rollout_gate"],
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
