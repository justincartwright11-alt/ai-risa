#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.py

Deterministically generates the v31.2 scale reauthorization handoff artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.md

Rules:
- reauthorization family only
- do not reopen or mutate v8.8 through v31.1
- handoff only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.md"

RECORD = {
    "scale_reauthorization_handoff_id": "resolution-wave-packet-review-session-scale-reauthorization-handoff-0001",
    "scale_reauthorization_decision_id": "resolution-wave-packet-review-session-scale-reauthorization-decision-0001",
    "handoff_position": 1,
    "previous_rollout_authorization": False,
    "decision_outcome": "provided_by_operator",
    "rollout_authorized": "provided_by_operator",
    "operator_review_required": True,
    "next_family_recommendation": "provided_by_operator",
    "reauthorization_family_complete": True,
    "lineage_source_layer": "scale_reauthorization_decision",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-reauthorization-decision-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.json"
    ],
    "frozen_slices": [
        "v31.0-controlled-release-resolution-wave-packet-review-session-scale-reauthorization-intake",
        "v31.1-controlled-release-resolution-wave-packet-review-session-scale-reauthorization-decision"
    ],
    "scale_reauthorization_intake_complete": True,
    "scale_reauthorization_decision_complete": True,
    "scale_reauthorization_handoff_complete": True,
    "rollout_authorized": "provided_by_operator",
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_reauthorization_handoff_id",
    "scale_reauthorization_decision_id",
    "handoff_position",
    "previous_rollout_authorization",
    "decision_outcome",
    "rollout_authorized",
    "operator_review_required",
    "next_family_recommendation",
    "reauthorization_family_complete",
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
    lines.append("# v31.2 Controlled Release Resolution Wave Packet Review Session Scale Reauthorization Handoff\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Reauthorization handoff record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_reauthorization_handoff_id"],
        r["scale_reauthorization_decision_id"],
        str(r["handoff_position"]),
        str(r["previous_rollout_authorization"]),
        r["decision_outcome"],
        str(r["rollout_authorized"]),
        str(r["operator_review_required"]),
        r["next_family_recommendation"],
        str(r["reauthorization_family_complete"]),
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
