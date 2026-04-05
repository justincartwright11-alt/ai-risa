#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan.py

Deterministically generates the v30.1 scale remediation plan artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan.md

Rules:
- remediation family only
- do not reopen or mutate v8.8 through v30.0
- planning only
- deterministic output
- no timestamps unless explicitly provided in intake
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan.md"

RECORD = {
    "scale_remediation_plan_id": "resolution-wave-packet-review-session-scale-remediation-plan-0001",
    "scale_remediation_intake_id": "resolution-wave-packet-review-session-scale-remediation-intake-0001",
    "plan_position": 1,
    "blocked_scale_reason": "rollout gate not explicitly approved by operator",
    "remediation_objective": "resolve blocked rollout authorization before scaled operations",
    "remediation_targets": [
        "approval gap",
        "operational readiness gap",
        "governance acceptance gap"
    ],
    "approval_requirements": [
        "provided_by_operator"
    ],
    "operator_intervention_rules": [
        "provided_by_operator"
    ],
    "rollback_trigger_rules": [
        "provided_by_operator"
    ],
    "remediation_steps": [
        "verify blocked rollout condition",
        "collect missing approval inputs",
        "resolve governance acceptance gaps",
        "resolve operational readiness gaps",
        "capture remediation evidence",
        "re-evaluate rollout authorization"
    ],
    "evidence_artifact": "scale_remediation_evidence",
    "stop_condition": "plan_frozen_and_ready_for_remediation",
    "lineage_source_layer": "scale_remediation_intake",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-remediation-intake-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_remediation_plan_id",
    "scale_remediation_intake_id",
    "plan_position",
    "blocked_scale_reason",
    "remediation_objective",
    "remediation_targets",
    "approval_requirements",
    "operator_intervention_rules",
    "rollback_trigger_rules",
    "remediation_steps",
    "evidence_artifact",
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
    lines.append("# v30.1 Controlled Release Resolution Wave Packet Review Session Scale Remediation Plan\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Remediation plan record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_remediation_plan_id"],
        r["scale_remediation_intake_id"],
        str(r["plan_position"]),
        r["blocked_scale_reason"],
        r["remediation_objective"],
        ", ".join(r["remediation_targets"]),
        ", ".join(r["approval_requirements"]),
        ", ".join(r["operator_intervention_rules"]),
        ", ".join(r["rollback_trigger_rules"]),
        ", ".join(r["remediation_steps"]),
        r["evidence_artifact"],
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
