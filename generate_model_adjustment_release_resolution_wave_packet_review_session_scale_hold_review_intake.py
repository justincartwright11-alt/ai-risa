#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.py

Deterministically generates the v32.0 scale hold-review intake artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json
- operator-provided hold/review request payload

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.md

Rules:
- hold/review family only
- do not reopen or mutate v8.8 through v31.2
- objective is to capture unresolved authorization state and final review requirements
- deterministic output
- no timestamps unless explicitly provided in the payload
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.md"

RECORD = {
    "scale_hold_review_intake_id": "resolution-wave-packet-review-session-scale-hold-review-intake-0001",
    "prior_scale_reauthorization_handoff_id": "resolution-wave-packet-review-session-scale-reauthorization-handoff-0001",
    "rollout_authorized": False,
    "hold_review_objective": "capture unresolved authorization state and final review requirements before any further scale operations",
    "hold_review_targets": [
        "operator review",
        "governance review",
        "remediation review"
    ],
    "operator_review_required": True,
    "governance_review_required": True,
    "remediation_review_required": True,
    "final_review_requirements": [
        "provided_by_operator"
    ],
    "evidence_artifact": "scale_hold_review_evidence",
    "stop_condition": "hold_review_frozen_and_ready_for_final_review",
    "lineage_source_layer": "scale_reauthorization_handoff",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-reauthorization-handoff-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_hold_review_intake_id",
    "prior_scale_reauthorization_handoff_id",
    "rollout_authorized",
    "hold_review_objective",
    "hold_review_targets",
    "operator_review_required",
    "governance_review_required",
    "remediation_review_required",
    "final_review_requirements",
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
    lines.append("# v32.0 Controlled Release Resolution Wave Packet Review Session Scale Hold Review Intake\n")
    lines.append("**Source file:** ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json\n")
    lines.append("\n**Hold review intake record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_hold_review_intake_id"],
        r["prior_scale_reauthorization_handoff_id"],
        str(r["rollout_authorized"]),
        r["hold_review_objective"],
        ", ".join(r["hold_review_targets"]),
        str(r["operator_review_required"]),
        str(r["governance_review_required"]),
        str(r["remediation_review_required"]),
        ", ".join(r["final_review_requirements"]),
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
