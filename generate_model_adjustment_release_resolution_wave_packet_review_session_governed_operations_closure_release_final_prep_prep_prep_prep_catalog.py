"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_catalog.py

v64.142 closure-release-final-prep-prep-prep-prep-catalog generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_resolution.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_catalog.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_catalog.md
- Pure downstream projection: one catalog record per resolution record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-catalog-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_resolution.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_catalog.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_catalog.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

CATALOG_FAMILY = "closure-release-final-prep-prep-prep-prep-catalog"
RESOLUTION_FAMILY = "closure-release-final-prep-prep-prep-prep-resolution"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-catalog-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        resolution_records = json.load(f)

    catalog_records = []
    for idx, resolution in enumerate(sorted(resolution_records, key=lambda r: r["id"])):
        catalog_id = make_id(idx + 1)
        catalog_record = {
            "id": catalog_id,
            "family": CATALOG_FAMILY,
            "parent_id": resolution["id"],
            "parent_family": RESOLUTION_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": resolution.get("trace", []),
            "data": resolution.get("data", {}),
        }
        catalog_records.append(catalog_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {CATALOG_FAMILY} (v64.142)\n\n")
        for rec in catalog_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
