import json

# Input files
TRIAL_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_cutover_trial.json"
HANDOFF_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_handoff.json"

# Output files
CUTOFF_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_cutover_handoff.json"
CUTOFF_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_cutover_handoff.md"

CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_production_cutover_handoff",
    "source_files": [
        TRIAL_PATH,
        HANDOFF_PATH
    ],
    "production_cutover_trial_complete": True,
    "production_activation_handoff_complete": True,
    "production_cutover_family_complete": True,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [
        {
            "production_cutover_handoff_id": "resolution-wave-packet-review-session-production-cutover-handoff-0001",
            "handoff_position": 1,
            "terminal_production_cutover_trial_file": TRIAL_PATH,
            "terminal_production_activation_handoff_file": HANDOFF_PATH,
            "production_cutover_family_complete": True,
            "lineage_source_layer": "production_cutover_trial",
            "lineage_source_file": TRIAL_PATH,
            "lineage_source_record_id": "resolution-wave-packet-review-session-production-cutover-trial-0001"
        }
    ]
}

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v20.1 Production Cutover Handoff\n"]
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
    save_json(CONTRACT, CUTOFF_JSON)
    save_markdown(CONTRACT, CUTOFF_MD)

if __name__ == "__main__":
    main()
