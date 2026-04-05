#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_decision.py

Deterministically generates the v29.1 multi-run operational decision artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_readiness.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_decision.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_decision.md

Rules:
- readiness family only
- do not reopen or mutate v8.8 through v29.0
- decision only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_decision.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_decision.md"

RECORD = {
    "multi_run_operational_decision_id": "resolution-wave-packet-review-session-multi-run-operational-decision-0001",
    "multi_run_operational_readiness_id": "resolution-wave-packet-review-session-multi-run-operational-readiness-0001",
    "decision_position": 1,
    "readiness_result": "provided_by_operator",
    "scale_recommendation": "provided_by_operator",
    "decision_outcome": "provided_by_operator",
    "operator_review_required": True,
    "rollout_authorized": "provided_by_operator",
    "rationale_summary": "provided_by_operator",
    "next_family_recommendation": "provided_by_operator",
    "lineage_source_layer": "multi_run_operational_readiness",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_readiness.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-multi-run-operational-readiness-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_decision",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_multi_run_operational_readiness.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "multi_run_operational_decision_id",
    "multi_run_operational_readiness_id",
    "decision_position",
    "readiness_result",
    "scale_recommendation",
    "decision_outcome",
    "operator_review_required",
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
    lines.append("# v29.1 Controlled Release Resolution Wave Packet Review Session Multi Run Operational Decision\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Decision record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["multi_run_operational_decision_id"],
        r["multi_run_operational_readiness_id"],
        str(r["decision_position"]),
        r["readiness_result"],
        r["scale_recommendation"],
        r["decision_outcome"],
        str(r["operator_review_required"]),
        r["rollout_authorized"],
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
