import json

# Input files
GO_LIVE_READINESS = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_go_live_readiness.json"
GO_LIVE_CHECKLIST = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_go_live_checklist.json"

# Output files
OPERATOR_HANDOFF_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.json"
OPERATOR_HANDOFF_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.md"

CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_operator_handoff",
    "source_files": [
        GO_LIVE_READINESS,
        GO_LIVE_CHECKLIST
    ],
    "frozen_slices": [
        "v21.0-controlled-release-resolution-wave-packet-review-session-go-live-readiness",
        "v21.1-controlled-release-resolution-wave-packet-review-session-go-live-checklist"
    ],
    "review_session_program_complete": True,
    "runtime_handoff_complete": True,
    "external_consumer_handoff_complete": True,
    "production_cutover_handoff_complete": True,
    "go_live_ready": True,
    "operator_review_required": True,
    "execution_authorization_required": True,
    "operator_handoff_complete": True,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [
        {
            "operator_handoff_id": "resolution-wave-packet-review-session-operator-handoff-0001",
            "handoff_position": 1,
            "terminal_go_live_readiness_file": GO_LIVE_READINESS,
            "terminal_go_live_checklist_file": GO_LIVE_CHECKLIST,
            "operator_handoff_complete": True,
            "lineage_source_layer": "go_live_checklist",
            "lineage_source_file": GO_LIVE_CHECKLIST,
            "lineage_source_record_id": "resolution-wave-packet-review-session-go-live-checklist-0001"
        }
    ]
}

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v21.2 Operator Handoff\n"]
    lines.append("\n| operator_handoff_id | handoff_position | terminal_go_live_readiness_file | terminal_go_live_checklist_file | operator_handoff_complete | lineage_source_layer | lineage_source_file | lineage_source_record_id |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for rec in obj["records"]:
        lines.append(f"| {rec['operator_handoff_id']} | {rec['handoff_position']} | {rec['terminal_go_live_readiness_file']} | {rec['terminal_go_live_checklist_file']} | {rec['operator_handoff_complete']} | {rec['lineage_source_layer']} | {rec['lineage_source_file']} | {rec['lineage_source_record_id']} |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    save_json(CONTRACT, OPERATOR_HANDOFF_JSON)
    save_markdown(CONTRACT, OPERATOR_HANDOFF_MD)

if __name__ == "__main__":
    main()
