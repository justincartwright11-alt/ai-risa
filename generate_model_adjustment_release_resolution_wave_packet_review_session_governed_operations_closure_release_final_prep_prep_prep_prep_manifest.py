"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_manifest.py

v64.144 closure-release-final-prep-prep-prep-prep-manifest generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_index.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_manifest.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_manifest.md
- Pure downstream projection: one manifest record per index record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-manifest-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_index.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_manifest.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_manifest.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

MANIFEST_FAMILY = "closure-release-final-prep-prep-prep-prep-manifest"
INDEX_FAMILY = "closure-release-final-prep-prep-prep-prep-index"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-manifest-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        index_records = json.load(f)

    manifest_records = []
    for idx, index in enumerate(sorted(index_records, key=lambda r: r["id"])):
        manifest_id = make_id(idx + 1)
        manifest_record = {
            "id": manifest_id,
            "family": MANIFEST_FAMILY,
            "parent_id": index["id"],
            "parent_family": INDEX_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": index.get("trace", []),
            "data": index.get("data", {}),
        }
        manifest_records.append(manifest_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {MANIFEST_FAMILY} (v64.144)\n\n")
        for rec in manifest_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
