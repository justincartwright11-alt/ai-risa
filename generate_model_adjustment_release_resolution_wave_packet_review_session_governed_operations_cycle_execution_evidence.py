#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence.py

Purpose: Deterministically generate the v38.2 governed operations cycle execution evidence artifact from the frozen governed operations cycle plan and operator-provided execution outcome inputs.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_plan.json
- operator-provided governed operations execution outcome inputs (operator_governed_operations_execution_outcome.json)

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence.md

Rules:
- governed-operations family only
- do not reopen or mutate v8.8 through v38.1
- evidence only
- must evaluate requested deliverables, governance thresholds, approval requirements, intervention rules, and rollback triggers
- deterministic output from supplied evidence
- no timestamps unless explicitly provided in execution evidence
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

def main():
    # Input paths
    plan_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_plan.json")
    outcome_path = Path("operator_governed_operations_execution_outcome.json")

    # Output paths
    evidence_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence.json")
    evidence_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence.md")

    # Load inputs
    with plan_path.open("r", encoding="utf-8") as f:
        plan = json.load(f)
    plan_rec = plan["records"][0]
    with outcome_path.open("r", encoding="utf-8") as f:
        outcome = json.load(f)

    # Compose evidence record
    record = {
        "governed_operations_cycle_execution_evidence_id": "resolution-wave-packet-review-session-governed-operations-cycle-execution-evidence-0001",
        "governed_operations_cycle_plan_id": plan_rec["governed_operations_cycle_plan_id"],
        "evidence_position": 1,
        "execution_attempted": outcome["execution_attempted"],
        "execution_pass": outcome["execution_pass"],
        "requested_deliverables": plan_rec["requested_deliverables"],
        "delivered_artifacts": outcome["delivered_artifacts"],
        "governance_thresholds_breached": outcome["governance_thresholds_breached"],
        "approval_requirements_satisfied": outcome["approval_requirements_satisfied"],
        "operator_intervention_invoked": outcome["operator_intervention_invoked"],
        "rollback_triggered": outcome["rollback_triggered"],
        "incident_detected": outcome["incident_detected"],
        "execution_result_summary": outcome["execution_result_summary"],
        "lineage_source_layer": "governed_operations_cycle_plan",
        "lineage_source_file": str(plan_path).replace("\\", "/"),
        "lineage_source_record_id": plan_rec["governed_operations_cycle_plan_id"]
    }

    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cycle_execution_evidence",
        "source_file": str(plan_path).replace("\\", "/"),
        "record_count": 1,
        "records": [record]
    }

    # Deterministic JSON output
    with evidence_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output (columns in exact order)
    columns = [
        "governed_operations_cycle_execution_evidence_id",
        "governed_operations_cycle_plan_id",
        "evidence_position",
        "execution_attempted",
        "execution_pass",
        "requested_deliverables",
        "delivered_artifacts",
        "governance_thresholds_breached",
        "approval_requirements_satisfied",
        "operator_intervention_invoked",
        "rollback_triggered",
        "incident_detected",
        "execution_result_summary",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    def fmt(val):
        if isinstance(val, list):
            return "<br>".join(str(x) for x in val)
        return str(val)
    with evidence_md_path.open("w", encoding="utf-8") as f:
        f.write("# v38.2 Governed Operations Cycle Execution Evidence\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "---|" * len(columns) + "\n")
        f.write("| " + " | ".join(fmt(record[col]) for col in columns) + " |\n")

if __name__ == "__main__":
    main()
