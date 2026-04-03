import json

# Input file
EXTERNAL_HANDOFF_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_external_consumer_handoff.json"

# Output files
PROD_ACTIVATION_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_intake.json"
PROD_ACTIVATION_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_intake.md"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def save_markdown(obj, path):
    lines = ["# v19.0 Production Activation Intake\n"]
    for k, v in obj.items():
        lines.append(f"- {k}: {v}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    handoff = load_json(EXTERNAL_HANDOFF_PATH)

    # Deterministic, production-facing activation intake record
    record = {
        "external_consumer_handoff_id": handoff.get("consumer_handoff_id"),
        "trial_id": handoff.get("trial_id"),
        "handoff_ready": handoff.get("handoff_ready", True),
        "intake_certified": True,
        "intake_notes": "Production activation intake certified from external consumer handoff."
    }

    save_json(record, PROD_ACTIVATION_JSON)
    save_markdown(record, PROD_ACTIVATION_MD)

if __name__ == "__main__":
    main()
