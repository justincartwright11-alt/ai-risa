"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_map.py

v64.148 closure-release-final-prep-prep-prep-prep-map generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_routing.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_map.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_map.md
- Pure downstream projection: one map record per routing record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-map-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_routing.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_map.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_map.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

MAP_FAMILY = "closure-release-final-prep-prep-prep-prep-map"
ROUTING_FAMILY = "closure-release-final-prep-prep-prep-prep-routing"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-map-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        routing_records = json.load(f)

    map_records = []
    for idx, routing in enumerate(sorted(routing_records, key=lambda r: r["id"])):
        map_id = make_id(idx + 1)
        map_record = {
            "id": map_id,
            "family": MAP_FAMILY,
            "parent_id": routing["id"],
            "parent_family": ROUTING_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": routing.get("trace", []),
            "data": routing.get("data", {}),
        }
        map_records.append(map_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(map_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {MAP_FAMILY} (v64.148)\n\n")
        for rec in map_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
