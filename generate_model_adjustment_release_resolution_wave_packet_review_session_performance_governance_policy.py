#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.py

Deterministically generates the v27.1 performance governance policy for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.md

Rules:
- governance family only
- do not reopen or mutate v8.8 through v27.0
- policy only
- deterministic output
- no timestamps unless explicitly preserved from monitoring evidence
- no policy logic outside the declared governance artifact
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.md"

RECORD = {
    "performance_governance_policy_id": "resolution-wave-packet-review-session-performance-governance-policy-0001",
    "performance_governance_intake_id": "resolution-wave-packet-review-session-performance-governance-intake-0001",
    "policy_position": 1,
    "governance_objective": "govern future live-event production families using validated monitoring thresholds and escalation rules",
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
    "rollout_gate": "future live-event family may proceed only when governance policy is accepted",
    "operator_intervention_rules": [
        "provided_by_operator"
    ],
    "rollback_trigger_rules": [
        "provided_by_operator"
    ],
    "approval_requirements": [
        "provided_by_operator"
    ],
    "lineage_source_layer": "performance_governance_intake",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-performance-governance-intake-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_baseline.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_evidence.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_monitoring_closeout.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "performance_governance_policy_id",
    "performance_governance_intake_id",
    "policy_position",
    "governance_objective",
    "governance_metrics",
    "governance_thresholds",
    "alert_escalation_rules",
    "review_cadence",
    "rollout_gate",
    "operator_intervention_rules",
    "rollback_trigger_rules",
    "approval_requirements",
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
    lines.append("# v27.1 Controlled Release Resolution Wave Packet Review Session Performance Governance Policy\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Policy record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["performance_governance_policy_id"],
        r["performance_governance_intake_id"],
        str(r["policy_position"]),
        r["governance_objective"],
        ", ".join(r["governance_metrics"]),
        ", ".join(r["governance_thresholds"]),
        ", ".join(r["alert_escalation_rules"]),
        r["review_cadence"],
        r["rollout_gate"],
        ", ".join(r["operator_intervention_rules"]),
        ", ".join(r["rollback_trigger_rules"]),
        ", ".join(r["approval_requirements"]),
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
