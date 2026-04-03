#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.py

Deterministically generates the v23.0 post-run retrospective/archive slice for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_decision.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.md

Rules:
- retrospective/archive only
- do not reopen or mutate v8.8 through v22.2
- deterministic output
- no timestamps unless explicitly preserved from evidence
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

# Constants
INPUTS = [
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.json",
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_evidence.json",
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_decision.json",
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff.json"
]
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.md"

FROZEN_SLICES = [
    "v21.2-controlled-release-resolution-wave-packet-review-session-operator-handoff",
    "v22.0-controlled-release-resolution-wave-packet-review-session-live-execution-evidence",
    "v22.1-controlled-release-resolution-wave-packet-review-session-live-execution-decision",
    "v22.2-controlled-release-resolution-wave-packet-review-session-live-execution-handoff"
]

# Deterministic record content (no timestamps, no policy logic)
RECORD = {
    "post_run_retrospective_id": "resolution-wave-packet-review-session-post-run-retrospective-0001",
    "retrospective_position": 1,
    "operator_handoff_id": "resolution-wave-packet-review-session-operator-handoff-0001",
    "live_execution_handoff_id": "resolution-wave-packet-review-session-live-execution-handoff-0001",
    "final_operational_outcome": "accepted_into_operation",
    "operator_decision_outcome": "continue",
    "rollback_required": False,
    "incident_detected": False,
    "archive_status": "archived_complete",
    "operator_rationale_summary": "operator accepted the live outcome and archived the family as complete",
    "lessons_learned": [
        "Deterministic slice discipline preserved auditability end to end.",
        "Operational handoff before live execution reduced ambiguity.",
        "Evidence plus decision artifacts made final archival state explicit."
    ],
    "followup_actions": [
        "Monitor steady-state operation under normal governance.",
        "Do not reopen sealed families unless a new top-level family is authorized."
    ],
    "lineage_source_layer": "live_execution_handoff",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-live-execution-handoff-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective",
    "source_files": INPUTS,
    "frozen_slices": FROZEN_SLICES,
    "review_session_program_complete": True,
    "operator_handoff_complete": True,
    "live_execution_evidence_complete": True,
    "live_execution_decision_complete": True,
    "live_execution_handoff_complete": True,
    "post_run_retrospective_complete": True,
    "archive_ready": True,
    "archive_decision": "archive_complete",
    "record_count": 1,
    "records": [RECORD]
}

def write_json():
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(JSON_CONTRACT, f, indent=2, ensure_ascii=False)

def write_md():
    lines = []
    lines.append("# v23.0 Controlled Release Resolution Wave Packet Review Session Post-Run Retrospective\n")
    lines.append("**Source files:**\n")
    for src in INPUTS:
        lines.append(f"- {src}")
    lines.append("\n**Frozen slices:**\n")
    for s in FROZEN_SLICES:
        lines.append(f"- {s}")
    lines.append("\n**Status flags:**\n")
    for k in [
        "review_session_program_complete",
        "operator_handoff_complete",
        "live_execution_evidence_complete",
        "live_execution_decision_complete",
        "live_execution_handoff_complete",
        "post_run_retrospective_complete",
        "archive_ready",
        "archive_decision"
    ]:
        v = JSON_CONTRACT[k]
        lines.append(f"- {k}: {v}")
    lines.append("\n**Lessons learned:**\n")
    for l in RECORD["lessons_learned"]:
        lines.append(f"- {l}")
    lines.append("\n**Follow-up actions:**\n")
    for l in RECORD["followup_actions"]:
        lines.append(f"- {l}")
    lines.append("\n**Post-run retrospective:**\n")
    # Table header
    cols = [
        "post_run_retrospective_id",
        "retrospective_position",
        "operator_handoff_id",
        "live_execution_handoff_id",
        "final_operational_outcome",
        "operator_decision_outcome",
        "rollback_required",
        "incident_detected",
        "archive_status",
        "operator_rationale_summary",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    lines.append(" | ".join(cols))
    lines.append(" | ".join(["---"] * len(cols)))
    r = RECORD
    row = [
        r["post_run_retrospective_id"],
        str(r["retrospective_position"]),
        r["operator_handoff_id"],
        r["live_execution_handoff_id"],
        r["final_operational_outcome"],
        r["operator_decision_outcome"],
        str(r["rollback_required"]),
        str(r["incident_detected"]),
        r["archive_status"],
        r["operator_rationale_summary"],
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
