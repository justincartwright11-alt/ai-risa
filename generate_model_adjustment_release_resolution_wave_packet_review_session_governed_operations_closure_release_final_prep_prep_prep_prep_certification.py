import json
import hashlib
from pathlib import Path

PARENT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_verification.json"
JSON_OUTPUT = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_certification.json"
MD_OUTPUT = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_certification.md"

REQUIRED_FIELDS = [
    "certification_id",
    "certification_position",
    "source_verification_id",
    "source_verification_position",
    "source_verification_artifact",
    "certification_locator_key"
]

PASS_THROUGH_FIELDS = [
    "verification_id",
    "source_attestation_id",
    "attestation_id",
    "receipt_id",
    "source_handoff_id",
    "handoff_id",
    "source_register_id",
    "register_id",
    "map_id",
    "record_type",
    "status",
    "name",
    "title",
    "slug"
]

def load_parent_records():
    with open(PARENT_PATH, "r", encoding="utf-8") as f:
        parent = json.load(f)
    records = parent.get("records", [])
    if not all("verification_id" in r for r in records):
        raise ValueError("No usable verification_id exists in parent.")
    return parent, records

def make_certification_records(parent_records):
    certification_records = []
    for idx, record in enumerate(parent_records):
        cert_record = {
            "certification_id": f"cert_{record['verification_id']}",
            "certification_position": idx + 1,
            "source_verification_id": record["verification_id"],
            "source_verification_position": record.get("verification_position", idx + 1),
            "source_verification_artifact": PARENT_PATH,
            "certification_locator_key": f"cert_{record['verification_id']}"
        }
        for field in PASS_THROUGH_FIELDS:
            if field in record:
                cert_record[field] = record[field]
        certification_records.append(cert_record)
    return certification_records

def write_json(parent, records):
    out = {
        "parent_artifact": PARENT_PATH,
        "record_count": len(records),
        "records": records
    }
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return out

def write_markdown(parent, records):
    lines = [
        "# closure-release-final-prep-prep-prep-prep-certification\n",
        f"* parent_artifact: {PARENT_PATH}",
        f"* record_count: {len(records)}\n",
        "| certification_id | certification_position | source_verification_id | certification_locator_key |",
        "| ---------------- | ---------------------: | ---------------------- | ------------------------- |"
    ]
    for rec in records:
        lines.append(f"| {rec['certification_id']} | {rec['certification_position']} | {rec['source_verification_id']} | {rec['certification_locator_key']} |")
    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def main():
    parent, parent_records = load_parent_records()
    certification_records = make_certification_records(parent_records)
    write_json(parent, certification_records)
    write_markdown(parent, certification_records)

if __name__ == "__main__":
    main()
