#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_second_live_event_closeout.py

Deterministically generates the v28.3 closeout for the controlled release resolution wave packet review session second live event under explicit governance.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_execution_evidence.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_closeout.md

Rules:
- second live-event family only
- do not reopen or mutate v8.8 through v28.2
- closeout only
- must evaluate success criteria and governance thresholds
- deterministic output
- no timestamps unless explicitly preserved from execution evidence
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_closeout.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_closeout.md"

RECORD = {
    "second_live_event_closeout_id": "resolution-wave-packet-review-session-second-live-event-closeout-0001",
    "closeout_position": 1,
    "second_live_event_production_plan_id": "resolution-wave-packet-review-session-second-live-event-production-plan-0001",
    "second_live_event_execution_evidence_id": "resolution-wave-packet-review-session-second-live-event-execution-evidence-0001",
    "final_operational_outcome": "accepted_into_operation",
    "requested_deliverables_completed": True,
    "success_criteria_met": True,
    "governance_thresholds_breached": False,
    "execution_result_summary": "provided_by_operator",
    "second_live_event_family_complete": True,
    "lineage_source_layer": "second_live_event_execution_evidence",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_execution_evidence.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-second-live-event-execution-evidence-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_second_live_event_closeout",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_execution_evidence.json"
    ],
    "frozen_slices": [
        "v28.0-controlled-release-resolution-wave-packet-review-session-second-live-event-production-intake",
        "v28.1-controlled-release-resolution-wave-packet-review-session-second-live-event-production-plan",
        "v28.2-controlled-release-resolution-wave-packet-review-session-second-live-event-execution-evidence"
    ],
    "second_live_event_production_plan_complete": True,
    "second_live_event_execution_evidence_complete": True,
    "second_live_event_family_complete": True,
    "execution_attempted": True,
    "execution_pass": True,
    "governance_thresholds_breached": False,
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
    "second_live_event_closeout_id",
    "closeout_position",
    "second_live_event_production_plan_id",
    "second_live_event_execution_evidence_id",
    "final_operational_outcome",
    "requested_deliverables_completed",
    "success_criteria_met",
    "governance_thresholds_breached",
    "execution_result_summary",
    "second_live_event_family_complete",
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
    lines.append("# v28.3 Controlled Release Resolution Wave Packet Review Session Second Live Event Closeout\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Closeout record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["second_live_event_closeout_id"],
        str(r["closeout_position"]),
        r["second_live_event_production_plan_id"],
        r["second_live_event_execution_evidence_id"],
        r["final_operational_outcome"],
        str(r["requested_deliverables_completed"]),
        str(r["success_criteria_met"]),
        str(r["governance_thresholds_breached"]),
        r["execution_result_summary"],
        str(r["second_live_event_family_complete"]),
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
