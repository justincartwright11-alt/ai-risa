#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.py

Deterministically generates the v27.2 performance governance handoff for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.md

Rules:
- governance family only
- do not reopen or mutate v8.8 through v27.1
- handoff only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff.md"

RECORD = {
    "performance_governance_handoff_id": "resolution-wave-packet-review-session-performance-governance-handoff-0001",
    "performance_governance_policy_id": "resolution-wave-packet-review-session-performance-governance-policy-0001",
    "handoff_position": 1,
    "governance_family_complete": True,
    "rollout_gate": "future live-event family may proceed only when governance policy is accepted",
    "approval_requirements": [
        "provided_by_operator"
    ],
    "operator_intervention_rules": [
        "provided_by_operator"
    ],
    "rollback_trigger_rules": [
        "provided_by_operator"
    ],
    "lineage_source_layer": "performance_governance_policy",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-performance-governance-policy-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_performance_governance_handoff",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json"
    ],
    "frozen_slices": [
        "v27.0-controlled-release-resolution-wave-packet-review-session-performance-governance-intake",
        "v27.1-controlled-release-resolution-wave-packet-review-session-performance-governance-policy"
    ],
    "performance_governance_intake_complete": True,
    "performance_governance_policy_complete": True,
    "performance_governance_family_complete": True,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "performance_governance_handoff_id",
    "performance_governance_policy_id",
    "handoff_position",
    "governance_family_complete",
    "rollout_gate",
    "approval_requirements",
    "operator_intervention_rules",
    "rollback_trigger_rules",
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
    lines.append("# v27.2 Controlled Release Resolution Wave Packet Review Session Performance Governance Handoff\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Frozen slices:**\n")
    for s in JSON_CONTRACT["frozen_slices"]:
        lines.append(f"- {s}")
    lines.append("\n**Handoff record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["performance_governance_handoff_id"],
        r["performance_governance_policy_id"],
        str(r["handoff_position"]),
        str(r["governance_family_complete"]),
        r["rollout_gate"],
        ", ".join(r["approval_requirements"]),
        ", ".join(r["operator_intervention_rules"]),
        ", ".join(r["rollback_trigger_rules"]),
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
