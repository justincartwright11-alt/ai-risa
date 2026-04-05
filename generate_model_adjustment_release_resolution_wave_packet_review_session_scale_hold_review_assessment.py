#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.py

Deterministically generates the v32.1 scale hold-review assessment artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json
- operator-provided review findings

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.md

Rules:
- hold/review family only
- do not reopen or mutate v8.8 through v32.0
- assessment only
- deterministic output
- no timestamps unless explicitly provided in review findings
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.md"

RECORD = {
    "scale_hold_review_assessment_id": "resolution-wave-packet-review-session-scale-hold-review-assessment-0001",
    "scale_hold_review_intake_id": "resolution-wave-packet-review-session-scale-hold-review-intake-0001",
    "assessment_position": 1,
    "blocked_scale_reason": "rollout_authorized remains false after remediation and reauthorization; operator review required",
    "unresolved_items": [
        "operator review not complete",
        "governance acceptance not confirmed",
        "operational readiness not confirmed"
    ],
    "operator_review_findings": "provided_by_operator",
    "authorization_gap_status": "provided_by_operator",
    "operational_readiness_status": "provided_by_operator",
    "governance_acceptance_status": "provided_by_operator",
    "recommended_disposition": "provided_by_operator",
    "lineage_source_layer": "scale_hold_review_intake",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-hold-review-intake-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_hold_review_assessment_id",
    "scale_hold_review_intake_id",
    "assessment_position",
    "blocked_scale_reason",
    "unresolved_items",
    "operator_review_findings",
    "authorization_gap_status",
    "operational_readiness_status",
    "governance_acceptance_status",
    "recommended_disposition",
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
    lines.append("# v32.1 Controlled Release Resolution Wave Packet Review Session Scale Hold Review Assessment\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Hold review assessment record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_hold_review_assessment_id"],
        r["scale_hold_review_intake_id"],
        str(r["assessment_position"]),
        r["blocked_scale_reason"],
        ", ".join(r["unresolved_items"]),
        r["operator_review_findings"],
        r["authorization_gap_status"],
        r["operational_readiness_status"],
        r["governance_acceptance_status"],
        r["recommended_disposition"],
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
