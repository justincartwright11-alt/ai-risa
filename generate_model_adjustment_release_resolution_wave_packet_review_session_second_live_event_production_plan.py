#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan.py

Deterministically generates the v28.1 second live event production plan for the controlled release resolution wave packet review session under explicit governance.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan.md

Rules:
- second live-event family only
- do not reopen or mutate v8.8 through v28.0
- planning only
- must preserve rollout_gate, approval_requirements, operator_intervention_rules, and rollback_trigger_rules from governance
- deterministic output
- no timestamps unless explicitly provided in intake
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan.md"

RECORD = {
    "second_live_event_production_plan_id": "resolution-wave-packet-review-session-second-live-event-production-plan-0001",
    "second_live_event_production_intake_id": "resolution-wave-packet-review-session-second-live-event-production-intake-0001",
    "plan_position": 1,
    "governance_handoff_id": "resolution-wave-packet-review-session-performance-governance-handoff-0001",
    "objective": "execute one governed second live AI-RISA event/report production path",
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
        "execution evidence captured",
        "governance thresholds not breached"
    ],
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
    "execution_steps": [
        "validate governed intake",
        "prepare second live-event inputs",
        "run governed live event/report generation path",
        "capture governed execution evidence",
        "evaluate outcome against success criteria and governance thresholds"
    ],
    "evidence_artifact": "second_live_event_execution_evidence",
    "stop_condition": "plan_frozen_and_ready_for_execution",
    "lineage_source_layer": "second_live_event_production_intake",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_intake.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-second-live-event-production-intake-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_plan",
    "source_files": [
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_second_live_event_production_intake.json",
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_performance_governance_policy.json"
    ],
    "record_count": 1,
    "records": [RECORD]
}

MD_COLS = [
    "second_live_event_production_plan_id",
    "second_live_event_production_intake_id",
    "plan_position",
    "governance_handoff_id",
    "objective",
    "operator",
    "target_event_or_workload",
    "requested_deliverables",
    "success_criteria",
    "rollout_gate",
    "approval_requirements",
    "operator_intervention_rules",
    "rollback_trigger_rules",
    "execution_steps",
    "evidence_artifact",
    "stop_condition",
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
    lines.append("# v28.1 Controlled Release Resolution Wave Packet Review Session Second Live Event Production Plan\n")
    lines.append("**Source files:**\n")
    for src in JSON_CONTRACT["source_files"]:
        lines.append(f"- {src}")
    lines.append("\n**Plan record:**\n")
    lines.append(" | ".join(MD_COLS))
    lines.append(" | ".join(["---"] * len(MD_COLS)))
    r = RECORD
    row = [
        r["second_live_event_production_plan_id"],
        r["second_live_event_production_intake_id"],
        str(r["plan_position"]),
        r["governance_handoff_id"],
        r["objective"],
        r["operator"],
        r["target_event_or_workload"],
        ", ".join(r["requested_deliverables"]),
        ", ".join(r["success_criteria"]),
        r["rollout_gate"],
        ", ".join(r["approval_requirements"]),
        ", ".join(r["operator_intervention_rules"]),
        ", ".join(r["rollback_trigger_rules"]),
        ", ".join(r["execution_steps"]),
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
