import json

# Input files
EVIDENCE_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_evidence.json"
DECISION_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_decision.json"

# Output files
HANDOFF_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff.json"
HANDOFF_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff.md"

CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff",
    "source_files": [
        EVIDENCE_PATH,
        DECISION_PATH
    ],
    "frozen_slices": [
        "v22.0-controlled-release-resolution-wave-packet-review-session-live-execution-evidence",
        "v22.1-controlled-release-resolution-wave-packet-review-session-live-execution-decision"
    ],
    "live_execution_evidence_complete": True,
    "live_execution_decision_complete": True,
    "live_execution_family_complete": True,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [
        {
            "live_execution_handoff_id": "resolution-wave-packet-review-session-live-execution-handoff-0001",
            "handoff_position": 1,
            "terminal_live_execution_evidence_file": EVIDENCE_PATH,
            "terminal_live_execution_decision_file": DECISION_PATH,
            "live_execution_family_complete": True,
            "lineage_source_layer": "live_execution_decision",
            "lineage_source_file": DECISION_PATH,
            "lineage_source_record_id": "resolution-wave-packet-review-session-live-execution-decision-0001"
        }
    ]
}

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v22.2 Live Execution Handoff\n"]
    lines.append("\n| live_execution_handoff_id | handoff_position | terminal_live_execution_evidence_file | terminal_live_execution_decision_file | live_execution_family_complete | lineage_source_layer | lineage_source_file | lineage_source_record_id |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for rec in obj["records"]:
        lines.append(f"| {rec['live_execution_handoff_id']} | {rec['handoff_position']} | {rec['terminal_live_execution_evidence_file']} | {rec['terminal_live_execution_decision_file']} | {rec['live_execution_family_complete']} | {rec['lineage_source_layer']} | {rec['lineage_source_file']} | {rec['lineage_source_record_id']} |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    save_json(CONTRACT, HANDOFF_JSON)
    save_markdown(CONTRACT, HANDOFF_MD)

if __name__ == "__main__":
    main()
