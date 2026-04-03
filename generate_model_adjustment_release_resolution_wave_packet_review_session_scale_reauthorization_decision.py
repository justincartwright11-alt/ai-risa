#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.py

Deterministically generates the v31.1 scale reauthorization decision artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.md

Rules:
- reauthorization family only
- do not reopen or mutate v8.8 through v31.0
- decision only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision.md"

RECORD = {
    "scale_reauthorization_decision_id": "resolution-wave-packet-review-session-scale-reauthorization-decision-0001",
    "scale_reauthorization_intake_id": "resolution-wave-packet-review-session-scale-reauthorization-intake-0001",
    "decision_position": 1,
    "previous_rollout_authorization": False,
    "remediation_outcome": "provided_by_operator",
    "decision_outcome": "provided_by_operator",
    "rollout_authorized": "provided_by_operator",
    "operator_review_required": True,
    "rationale_summary": "provided_by_operator",
    "next_family_recommendation": "provided_by_operator",
    "lineage_source_layer": "scale_reauthorization_intake",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-reauthorization-intake-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_decision",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_reauthorization_decision_id",
    "scale_reauthorization_intake_id",
    "decision_position",
    "previous_rollout_authorization",
    "remediation_outcome",
    "decision_outcome",
    "rollout_authorized",
    "operator_review_required",
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
    lines.append("# v31.1 Controlled Release Resolution Wave Packet Review Session Scale Reauthorization Decision\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Reauthorization decision record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_reauthorization_decision_id"],
        r["scale_reauthorization_intake_id"],
        str(r["decision_position"]),
        str(r["previous_rollout_authorization"]),
        r["remediation_outcome"],
        r["decision_outcome"],
        str(r["rollout_authorized"]),
        str(r["operator_review_required"]),
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
