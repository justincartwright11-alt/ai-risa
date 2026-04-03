#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.py

Deterministically generates the v30.0 scale remediation intake artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_scale_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json
- operator-provided remediation request payload

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.md

Rules:
- remediation family only
- do not reopen or mutate v8.8 through v29.2
- objective is to resolve the blocked rollout gate
- deterministic output
- no timestamps unless explicitly provided in the remediation payload
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake.md"

RECORD = {
    "scale_remediation_intake_id": "resolution-wave-packet-review-session-scale-remediation-intake-0001",
    "multi_run_scale_handoff_id": "resolution-wave-packet-review-session-multi-run-scale-handoff-0001",
    "remediation_position": 1,
    "rollout_authorized": False,
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
    "evidence_artifact": "scale_remediation_evidence",
    "stop_condition": "intake_frozen_and_ready_for_remediation",
    "lineage_source_layer": "multi_run_scale_handoff",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_scale_handoff.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-multi-run-scale-handoff-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_intake",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_scale_handoff.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_remediation_intake_id",
    "multi_run_scale_handoff_id",
    "remediation_position",
    "rollout_authorized",
    "blocked_scale_reason",
    "remediation_objective",
    "remediation_targets",
    "approval_requirements",
    "operator_intervention_rules",
    "rollback_trigger_rules",
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
    lines.append("# v30.0 Controlled Release Resolution Wave Packet Review Session Scale Remediation Intake\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Remediation intake record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_remediation_intake_id"],
        r["multi_run_scale_handoff_id"],
        str(r["remediation_position"]),
        str(r["rollout_authorized"]),
        r["blocked_scale_reason"],
        r["remediation_objective"],
        ", ".join(r["remediation_targets"]),
        ", ".join(r["approval_requirements"]),
        ", ".join(r["operator_intervention_rules"]),
        ", ".join(r["rollback_trigger_rules"]),
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
