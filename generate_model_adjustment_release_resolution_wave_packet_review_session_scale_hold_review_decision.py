#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.py

Deterministically generates the v32.2 scale hold-review decision artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.md

Rules:
- hold/review family only
- do not reopen or mutate v8.8 through v32.1
- decision only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.md"

RECORD = {
    "scale_hold_review_decision_id": "resolution-wave-packet-review-session-scale-hold-review-decision-0001",
    "scale_hold_review_assessment_id": "resolution-wave-packet-review-session-scale-hold-review-assessment-0001",
    "decision_position": 1,
    "blocked_scale_reason": "rollout gate not explicitly approved by operator",
    "authorization_gap_status": "provided_by_operator",
    "operational_readiness_status": "provided_by_operator",
    "governance_acceptance_status": "provided_by_operator",
    "decision_outcome": "provided_by_operator",
    "rollout_authorized": False,
    "rationale_summary": "provided_by_operator",
    "next_family_recommendation": "provided_by_operator",
    "lineage_source_layer": "scale_hold_review_assessment",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-hold-review-assessment-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_hold_review_decision_id",
    "scale_hold_review_assessment_id",
    "decision_position",
    "blocked_scale_reason",
    "authorization_gap_status",
    "operational_readiness_status",
    "governance_acceptance_status",
    "decision_outcome",
    "rollout_authorized",
    "rationale_summary",
    "next_family_recommendation",
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
    lines.append("# v32.2 Controlled Release Resolution Wave Packet Review Session Scale Hold Review Decision\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Hold review decision record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_hold_review_decision_id"],
        r["scale_hold_review_assessment_id"],
        str(r["decision_position"]),
        r["blocked_scale_reason"],
        r["authorization_gap_status"],
        r["operational_readiness_status"],
        r["governance_acceptance_status"],
        r["decision_outcome"],
        str(r["rollout_authorized"]),
        r["rationale_summary"],
        r["next_family_recommendation"],
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
