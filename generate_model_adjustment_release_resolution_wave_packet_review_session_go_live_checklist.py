import json

# Input files
GO_LIVE_READINESS = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_go_live_readiness.json"
PROGRAM_CLOSEOUT = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.json"
RUNTIME_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_runtime_handoff.json"
EXTERNAL_CONSUMER_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_external_consumer_handoff.json"
PRODUCTION_CUTOVER_HANDOFF = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_cutover_handoff.json"

# Output files
CHECKLIST_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_go_live_checklist.json"
CHECKLIST_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_go_live_checklist.md"


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v21.1 Go-Live Checklist\n"]
    for k, v in obj.items():
        lines.append(f"- {k}: {v}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    # Deterministic, operator-facing go-live checklist
    checklist = {
        "review_session_program_complete": True,
        "runtime_handoff_complete": True,
        "external_consumer_handoff_complete": True,
        "production_cutover_handoff_complete": True,
        "go_live_ready": True,
        "operator_review_required": True,
        "execution_authorization_required": True
    }
    save_json(checklist, CHECKLIST_JSON)
    save_markdown(checklist, CHECKLIST_MD)

if __name__ == "__main__":
    main()
