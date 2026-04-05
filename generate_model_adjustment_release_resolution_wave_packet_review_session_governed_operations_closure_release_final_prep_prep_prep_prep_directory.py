"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_directory.py

v64.145 closure-release-final-prep-prep-prep-prep-directory generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_manifest.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_directory.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_directory.md
- Pure downstream projection: one directory record per manifest record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-directory-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_manifest.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_directory.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_directory.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

DIRECTORY_FAMILY = "closure-release-final-prep-prep-prep-prep-directory"
MANIFEST_FAMILY = "closure-release-final-prep-prep-prep-prep-manifest"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-directory-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        manifest_records = json.load(f)

    directory_records = []
    for idx, manifest in enumerate(sorted(manifest_records, key=lambda r: r["id"])):
        directory_id = make_id(idx + 1)
        directory_record = {
            "id": directory_id,
            "family": DIRECTORY_FAMILY,
            "parent_id": manifest["id"],
            "parent_family": MANIFEST_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": manifest.get("trace", []),
            "data": manifest.get("data", {}),
        }
        directory_records.append(directory_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(directory_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {DIRECTORY_FAMILY} (v64.145)\n\n")
        for rec in directory_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
