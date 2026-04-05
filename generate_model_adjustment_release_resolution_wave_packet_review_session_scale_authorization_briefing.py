#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing.py

Deterministically generates the v33.0 scale authorization briefing artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing.md

Rules:
- briefing family only
- do not reopen or mutate v8.8 through v32.3
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing.md"

RECORD = {
    "scale_authorization_briefing_id": "resolution-wave-packet-review-session-scale-authorization-briefing-0001",
    "prior_hold_review_handoff_id": "resolution-wave-packet-review-session-scale-hold-review-handoff-0001",
    "prior_reauthorization_handoff_id": "resolution-wave-packet-review-session-scale-reauthorization-handoff-0001",
    "performance_governance_handoff_id": "provided_by_operator",
    "rollout_authorized": False,
    "blocked_scale_reason": "rollout gate not explicitly approved by operator",
    "final_hold_review_summary": "provided_by_operator",
    "final_governance_summary": "provided_by_operator",
    "operator_decision_required": True,
    "authorization_request": "authorize / deny / defer",
    "lineage_source_layer": "scale_hold_review_handoff",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-hold-review-handoff-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_authorization_briefing",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_hold_review_handoff.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_reauthorization_handoff.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_authorization_briefing_id",
    "prior_hold_review_handoff_id",
    "prior_reauthorization_handoff_id",
    "performance_governance_handoff_id",
    "rollout_authorized",
    "blocked_scale_reason",
    "final_hold_review_summary",
    "final_governance_summary",
    "operator_decision_required",
    "authorization_request",
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
    lines.append("# v33.0 Controlled Release Resolution Wave Packet Review Session Scale Authorization Briefing\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Authorization briefing record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_authorization_briefing_id"],
        r["prior_hold_review_handoff_id"],
        r["prior_reauthorization_handoff_id"],
        r["performance_governance_handoff_id"],
        str(r["rollout_authorized"]),
        r["blocked_scale_reason"],
        r["final_hold_review_summary"],
        r["final_governance_summary"],
        str(r["operator_decision_required"]),
        r["authorization_request"],
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
