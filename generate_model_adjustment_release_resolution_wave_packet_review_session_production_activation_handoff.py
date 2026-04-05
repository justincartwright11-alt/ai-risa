import json

# Input files
INTAKE_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_intake.json"
SMOKE_TEST_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_smoke_test.json"

# Output files
HANDOFF_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_handoff.json"
HANDOFF_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_handoff.md"

CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_production_activation_handoff",
    "source_files": [
        INTAKE_PATH,
        SMOKE_TEST_PATH
    ],
    "frozen_slices": [
        "v19.0-controlled-release-resolution-wave-packet-review-session-production-activation-intake",
        "v19.1-controlled-release-resolution-wave-packet-review-session-production-activation-smoke-test"
    ],
    "production_activation_intake_complete": True,
    "production_activation_smoke_test_complete": True,
    "production_activation_family_complete": True,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [
        {
            "production_activation_handoff_id": "resolution-wave-packet-review-session-production-activation-handoff-0001",
            "handoff_position": 1,
            "terminal_production_activation_intake_file": INTAKE_PATH,
            "terminal_production_activation_smoke_test_file": SMOKE_TEST_PATH,
            "production_activation_family_complete": True,
            "lineage_source_layer": "production_activation_smoke_test",
            "lineage_source_file": SMOKE_TEST_PATH,
            "lineage_source_record_id": "resolution-wave-packet-review-session-production-activation-smoke-test-0001"
        }
    ]
}

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v19.2 Production Activation Handoff\n"]
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
    save_json(CONTRACT, HANDOFF_JSON)
    save_markdown(CONTRACT, HANDOFF_MD)

if __name__ == "__main__":
    main()
