#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.py

Deterministically generates the v32.3 scale hold-review handoff artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.md

Rules:
- hold/review family only
- do not reopen or mutate v8.8 through v32.2
- handoff only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.md"

RECORD = {
    "scale_hold_review_handoff_id": "resolution-wave-packet-review-session-scale-hold-review-handoff-0001",
    "scale_hold_review_decision_id": "resolution-wave-packet-review-session-scale-hold-review-decision-0001",
    "handoff_position": 1,
    "blocked_scale_reason": "rollout gate not explicitly approved by operator",
    "decision_outcome": "provided_by_operator",
    "rollout_authorized": False,
    "next_family_recommendation": "provided_by_operator",
    "hold_review_family_complete": True,
    "lineage_source_layer": "scale_hold_review_decision",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-hold-review-decision-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_assessment.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_decision.json"
    ],
    "frozen_slices": [
        "v32.0-controlled-release-resolution-wave-packet-review-session-scale-hold-review-intake",
        "v32.1-controlled-release-resolution-wave-packet-review-session-scale-hold-review-assessment",
        "v32.2-controlled-release-resolution-wave-packet-review-session-scale-hold-review-decision"
    ],
    "scale_hold_review_assessment_complete": True,
    "scale_hold_review_decision_complete": True,
    "scale_hold_review_handoff_complete": True,
    "rollout_authorized": False,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_hold_review_handoff_id",
    "scale_hold_review_decision_id",
    "handoff_position",
    "blocked_scale_reason",
    "decision_outcome",
    "rollout_authorized",
    "next_family_recommendation",
    "hold_review_family_complete",
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
    lines.append("# v32.3 Controlled Release Resolution Wave Packet Review Session Scale Hold Review Handoff\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Hold review handoff record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_hold_review_handoff_id"],
        r["scale_hold_review_decision_id"],
        str(r["handoff_position"]),
        r["blocked_scale_reason"],
        r["decision_outcome"],
        str(r["rollout_authorized"]),
        r["next_family_recommendation"],
        str(r["hold_review_family_complete"]),
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
