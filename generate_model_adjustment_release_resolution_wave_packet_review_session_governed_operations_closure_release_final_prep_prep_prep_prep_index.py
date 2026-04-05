"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_index.py

v64.143 closure-release-final-prep-prep-prep-prep-index generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_catalog.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_index.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_index.md
- Pure downstream projection: one index record per catalog record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-index-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_catalog.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_index.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_index.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

INDEX_FAMILY = "closure-release-final-prep-prep-prep-prep-index"
CATALOG_FAMILY = "closure-release-final-prep-prep-prep-prep-catalog"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-index-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        catalog_records = json.load(f)

    index_records = []
    for idx, catalog in enumerate(sorted(catalog_records, key=lambda r: r["id"])):
        index_id = make_id(idx + 1)
        index_record = {
            "id": index_id,
            "family": INDEX_FAMILY,
            "parent_id": catalog["id"],
            "parent_family": CATALOG_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": catalog.get("trace", []),
            "data": catalog.get("data", {}),
        }
        index_records.append(index_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(index_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {INDEX_FAMILY} (v64.143)\n\n")
        for rec in index_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
