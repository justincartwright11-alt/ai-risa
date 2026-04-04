"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_locator.py

v64.146 closure-release-final-prep-prep-prep-prep-locator generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_directory.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_locator.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_locator.md
- Pure downstream projection: one locator record per directory record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-locator-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_directory.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_locator.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_locator.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

LOCATOR_FAMILY = "closure-release-final-prep-prep-prep-prep-locator"
DIRECTORY_FAMILY = "closure-release-final-prep-prep-prep-prep-directory"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-locator-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        directory_records = json.load(f)

    locator_records = []
    for idx, directory in enumerate(sorted(directory_records, key=lambda r: r["id"])):
        locator_id = make_id(idx + 1)
        locator_record = {
            "id": locator_id,
            "family": LOCATOR_FAMILY,
            "parent_id": directory["id"],
            "parent_family": DIRECTORY_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": directory.get("trace", []),
            "data": directory.get("data", {}),
        }
        locator_records.append(locator_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(locator_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {LOCATOR_FAMILY} (v64.146)\n\n")
        for rec in locator_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
