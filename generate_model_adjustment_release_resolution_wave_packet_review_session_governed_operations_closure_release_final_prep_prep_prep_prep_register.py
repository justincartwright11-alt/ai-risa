"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_register.py

v64.149 closure-release-final-prep-prep-prep-prep-register generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_map.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_register.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_register.md
- Pure downstream projection: one register record per map record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-register-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_map.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_register.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_register.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

REGISTER_FAMILY = "closure-release-final-prep-prep-prep-prep-register"
MAP_FAMILY = "closure-release-final-prep-prep-prep-prep-map"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-register-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        map_records = json.load(f)

    register_records = []
    for idx, map_rec in enumerate(sorted(map_records, key=lambda r: r["id"])):
        register_id = make_id(idx + 1)
        register_record = {
            "id": register_id,
            "family": REGISTER_FAMILY,
            "parent_id": map_rec["id"],
            "parent_family": MAP_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": map_rec.get("trace", []),
            "data": map_rec.get("data", {}),
        }
        register_records.append(register_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(register_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {REGISTER_FAMILY} (v64.150)\n\n")
        for rec in register_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
