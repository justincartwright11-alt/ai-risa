#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_live_event_production_intake.py

Deterministically generates the v25.0 live event/report production intake for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.json
- operator-provided live event request payload

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_production_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_production_intake.md

Rules:
- new family only
- do not reopen or mutate v8.8 through v24.2
- objective is a real business use case: one live event/report production run
- deterministic output
- no timestamps unless explicitly provided in the request payload
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

# Operator request payload (provided)
operator_payload = {
    "operator": "provided_by_operator",
    "target_event_or_workload": "provided_by_operator",
    "requested_deliverables": [
        "full report",
        "simulation brief",
        "operator summary"
    ],
    "success_criteria": [
        "all requested deliverables generated",
        "outputs internally consistent",
        "execution evidence captured"
    ],
    "evidence_artifact": "live_event_execution_evidence",
    "stop_condition": "intake_frozen_and_ready_for_execution"
}

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_production_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_production_intake.md"

RECORD = {
    "live_event_production_intake_id": "resolution-wave-packet-review-session-live-event-production-intake-0001",
    "intake_position": 1,
    "objective": "execute one live AI-RISA event/report production path",
    "operator": operator_payload["operator"],
    "target_event_or_workload": operator_payload["target_event_or_workload"],
    "requested_deliverables": operator_payload["requested_deliverables"],
    "success_criteria": operator_payload["success_criteria"],
    "evidence_artifact": operator_payload["evidence_artifact"],
    "stop_condition": operator_payload["stop_condition"],
    "lineage_source_layer": "archive_handoff",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-archive-handoff-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_live_event_production_intake",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

def write_json():
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(JSON_CONTRACT, f, indent=2, ensure_ascii=False)

def write_md():
    lines = []
    lines.append("# v25.0 Controlled Release Resolution Wave Packet Review Session Live Event Production Intake\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Intake record:**\n")
    cols = [
        "live_event_production_intake_id",
        "intake_position",
        "objective",
        "operator",
        "target_event_or_workload",
        "requested_deliverables",
        "success_criteria",
        "evidence_artifact",
        "stop_condition",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    lines.append(" | ".join(cols))
    lines.append(" | ".join(["---"] * len(cols)))
    r = RECORD
    row = [
        r["live_event_production_intake_id"],
        str(r["intake_position"]),
        r["objective"],
        r["operator"],
        r["target_event_or_workload"],
        ", ".join(r["requested_deliverables"]),
        ", ".join(r["success_criteria"]),
        r["evidence_artifact"],
        r["stop_condition"],
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
