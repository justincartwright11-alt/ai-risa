import json

# Input file
EVIDENCE_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_evidence.json"

# Output files
DECISION_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_decision.json"
DECISION_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_decision.md"

# Example operator decision (replace with real values as needed)
decision_outcome = "continue"
decision_rationale = "First live run completed successfully with no incidents."
followup_required = False

# Load evidence for pass-through fields
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v22.1 Live Execution Decision\n"]
    for k, v in obj.items():
        if k != "records":
            lines.append(f"- {k}: {v}")
    lines.append("\n## Records\n")
    for rec in obj["records"]:
        for rk, rv in rec.items():
            lines.append(f"- {rk}: {rv}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    evidence = load_json(EVIDENCE_PATH)
    # Pass-through fields from evidence
    operator_handoff_present = evidence.get("operator_handoff_present", True)
    live_execution_attempted = evidence.get("live_execution_attempted", True)
    live_execution_pass = evidence.get("live_execution_pass", True)
    rollback_required = evidence.get("rollback_required", False)
    incident_detected = evidence.get("incident_detected", False)

    record = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_live_execution_decision",
        "source_file": EVIDENCE_PATH,
        "operator_handoff_present": operator_handoff_present,
        "live_execution_attempted": live_execution_attempted,
        "live_execution_pass": live_execution_pass,
        "rollback_required": rollback_required,
        "incident_detected": incident_detected,
        "decision_outcome": decision_outcome,
        "decision_rationale": decision_rationale,
        "followup_required": followup_required,
        "record_count": 1,
        "records": [
            {
                "live_execution_decision_id": "resolution-wave-packet-review-session-live-execution-decision-0001",
                "decision_position": 1,
                "live_execution_evidence_id": "resolution-wave-packet-review-session-live-execution-evidence-0001",
                "decision_outcome": decision_outcome,
                "decision_rationale": decision_rationale,
                "followup_required": followup_required,
                "lineage_source_layer": "live_execution_evidence",
                "lineage_source_file": EVIDENCE_PATH,
                "lineage_source_record_id": "resolution-wave-packet-review-session-live-execution-evidence-0001"
            }
        ]
    }
    save_json(record, DECISION_JSON)
    save_markdown(record, DECISION_MD)

if __name__ == "__main__":
    main()
