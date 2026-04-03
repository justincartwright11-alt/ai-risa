#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.py

Deterministically generates the v31.0 scale reauthorization intake artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_scale_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.json
- operator-provided reauthorization request payload

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.md

Rules:
- reauthorization family only
- do not reopen or mutate v8.8 through v30.3
- deterministic output
- no timestamps unless explicitly provided in the payload
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.md"

RECORD = {
    "scale_reauthorization_intake_id": "resolution-wave-packet-review-session-scale-reauthorization-intake-0001",
    "prior_scale_handoff_id": "resolution-wave-packet-review-session-multi-run-scale-handoff-0001",
    "remediation_closeout_id": "resolution-wave-packet-review-session-scale-remediation-closeout-0001",
    "previous_rollout_authorization": False,
    "remediation_outcome": "resolved_for_reauthorization",
    "reauthorization_objective": "determine if post-remediation conditions now permit scale rollout authorization",
    "reauthorization_targets": [
        "approval gap",
        "operational readiness gap",
        "governance acceptance gap"
    ],
    "approval_requirements": [
        "provided_by_operator"
    ],
    "operator_review_required": True,
    "evidence_artifact": "scale_reauthorization_evidence",
    "stop_condition": "intake_frozen_and_ready_for_review",
    "lineage_source_layer": "scale_remediation_closeout",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-remediation-closeout-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_scale_handoff.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_reauthorization_intake_id",
    "prior_scale_handoff_id",
    "remediation_closeout_id",
    "previous_rollout_authorization",
    "remediation_outcome",
    "reauthorization_objective",
    "reauthorization_targets",
    "approval_requirements",
    "operator_review_required",
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
    lines.append("# v31.0 Controlled Release Resolution Wave Packet Review Session Scale Reauthorization Intake\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Reauthorization intake record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_reauthorization_intake_id"],
        r["prior_scale_handoff_id"],
        r["remediation_closeout_id"],
        str(r["previous_rollout_authorization"]),
        r["remediation_outcome"],
        r["reauthorization_objective"],
        ", ".join(r["reauthorization_targets"]),
        ", ".join(r["approval_requirements"]),
        str(r["operator_review_required"]),
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
