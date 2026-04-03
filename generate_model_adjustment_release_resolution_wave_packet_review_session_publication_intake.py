"""
generate_model_adjustment_release_resolution_wave_packet_review_session_publication_intake.py

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.md
- Contract: New downstream workstream, do not mutate v8.8–v12.5, deterministic ordering, one publication intake record per delivery handoff record, stable lineage, no timestamps/policy/release logic/merge/tag/push.
"""
import json
import os

HANDOFF_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_delivery_handoff.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_publication_intake.md"

INTAKE_ID_PREFIX = "resolution-wave-packet-review-session-publication-intake-"

MD_COLUMNS = [
    "publication_intake_id",
    "intake_position",
    "delivery_handoff_id",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]


def main():
    with open(HANDOFF_FILE, "r", encoding="utf-8") as f:
        handoff_data = json.load(f)
    handoff_records = handoff_data["records"]

    intake_records = []
    for i, handoff_record in enumerate(handoff_records, 1):
        intake_record = {
            "publication_intake_id": f"{INTAKE_ID_PREFIX}{i:04d}",
            "intake_position": i,
            "delivery_handoff_id": handoff_record["delivery_handoff_id"],
            "lineage_source_layer": "delivery_handoff",
            "lineage_source_file": HANDOFF_FILE,
            "lineage_source_record_id": handoff_record["delivery_handoff_id"],
        }
        intake_records.append(intake_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_publication_intake",
        "source_file": HANDOFF_FILE,
        "record_count": len(intake_records),
        "records": intake_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        for record in intake_records:
            row = [str(record[col]) for col in MD_COLUMNS]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
