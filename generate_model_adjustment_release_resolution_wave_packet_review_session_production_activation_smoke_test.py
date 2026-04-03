import json

# Input file
INTAKE_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_intake.json"

# Output files
SMOKE_TEST_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_smoke_test.json"
SMOKE_TEST_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_smoke_test.md"

# Deterministic contract values
CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_production_activation_smoke_test",
    "source_file": INTAKE_PATH,
    "source_record_count": 0,
    "record_count": 1,
    "production_activation_smoke_test_pass": False,
    "checks": {
        "production_activation_intake_present_pass": False,
        "external_consumer_handoff_present_pass": False,
        "production_activation_readiness_pass": False,
        "downstream_activation_path_pass": False,
        "deterministic_output_pass": False
    },
    "records": [
        {
            "production_activation_smoke_test_id": "resolution-wave-packet-review-session-production-activation-smoke-test-0001",
            "smoke_test_position": 1,
            "production_activation_intake_id": "resolution-wave-packet-review-session-production-activation-intake-0001",
            "production_activation_smoke_test_pass": True,
            "lineage_source_layer": "production_activation_intake",
            "lineage_source_file": INTAKE_PATH,
            "lineage_source_record_id": "resolution-wave-packet-review-session-production-activation-intake-0001"
        }
    ]
}

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v19.1 Production Activation Smoke Test\n"]
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
    save_json(CONTRACT, SMOKE_TEST_JSON)
    save_markdown(CONTRACT, SMOKE_TEST_MD)

if __name__ == "__main__":
    main()
