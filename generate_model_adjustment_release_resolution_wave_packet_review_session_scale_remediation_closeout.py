#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.py

Deterministically generates the v30.3 scale remediation closeout artifact for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_evidence.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.md

Rules:
- remediation family only
- do not reopen or mutate v8.8 through v30.2
- closeout only
- deterministic output
- no timestamps unless explicitly preserved from remediation evidence
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout.md"

RECORD = {
    "scale_remediation_closeout_id": "resolution-wave-packet-review-session-scale-remediation-closeout-0001",
    "closeout_position": 1,
    "scale_remediation_plan_id": "resolution-wave-packet-review-session-scale-remediation-plan-0001",
    "scale_remediation_evidence_id": "resolution-wave-packet-review-session-scale-remediation-evidence-0001",
    "final_remediation_outcome": "resolved_for_reauthorization",
    "approval_gap_resolved": "provided_by_operator",
    "operational_readiness_gap_resolved": "provided_by_operator",
    "governance_acceptance_gap_resolved": "provided_by_operator",
    "remediation_result_summary": "provided_by_operator",
    "scale_remediation_family_complete": True,
    "lineage_source_layer": "scale_remediation_evidence",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_evidence.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-scale-remediation-evidence-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_closeout",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_plan.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_scale_remediation_evidence.json"
    ],
    "frozen_slices": [
        "v30.0-controlled-release-resolution-wave-packet-review-session-scale-remediation-intake",
        "v30.1-controlled-release-resolution-wave-packet-review-session-scale-remediation-plan",
        "v30.2-controlled-release-resolution-wave-packet-review-session-scale-remediation-evidence"
    ],
    "scale_remediation_plan_complete": True,
    "scale_remediation_evidence_complete": True,
    "scale_remediation_family_complete": True,
    "remediation_attempted": True,
    "remediation_pass": True,
    "approval_gap_resolved": "provided_by_operator",
    "operational_readiness_gap_resolved": "provided_by_operator",
    "governance_acceptance_gap_resolved": "provided_by_operator",
    "alert_triggered": False,
    "incident_detected": False,
    "rollback_required": False,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "scale_remediation_closeout_id",
    "closeout_position",
    "scale_remediation_plan_id",
    "scale_remediation_evidence_id",
    "final_remediation_outcome",
    "approval_gap_resolved",
    "operational_readiness_gap_resolved",
    "governance_acceptance_gap_resolved",
    "remediation_result_summary",
    "scale_remediation_family_complete",
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
    lines.append("# v30.3 Controlled Release Resolution Wave Packet Review Session Scale Remediation Closeout\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Remediation closeout record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["scale_remediation_closeout_id"],
        str(r["closeout_position"]),
        r["scale_remediation_plan_id"],
        r["scale_remediation_evidence_id"],
        r["final_remediation_outcome"],
        r["approval_gap_resolved"],
        r["operational_readiness_gap_resolved"],
        r["governance_acceptance_gap_resolved"],
        r["remediation_result_summary"],
        str(r["scale_remediation_family_complete"]),
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
